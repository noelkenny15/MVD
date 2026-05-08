# pipeline.py — Core dubbing pipeline

import os
import asyncio
import numpy as np
from scipy.io import wavfile
import moviepy.editor as mp
import whisper
import edge_tts
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import subprocess
import sys

async def list_available_languages():
    voices = await edge_tts.list_voices()
    languages = {}
    for v in voices:
        lang = v["Locale"][:2]
        if lang not in languages:
            languages[lang] = []
        languages[lang].append(v["ShortName"])
    
    for lang, voice_list in sorted(languages.items()):
        print(f"{lang}: {voice_list}")


# ================= LOAD WHISPER MODEL (GPU) =================
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Using device: {DEVICE}")

model = whisper.load_model("small", device=DEVICE)

# ================= EXTRACT AUDIO =================
def extract_audio(video_path: str, audio_path: str):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()

# ================= TRANSCRIBE =================
def transcribe_audio(audio_path: str):
    result = model.transcribe(audio_path, word_timestamps=True)
    return result

# ================= GENDER DETECTION =================
def detect_gender(audio_path, segments):
    try:
        sr, y = wavfile.read(audio_path)
        if y.ndim > 1:
            y = y[:, 0]
        y = y[:sr * 20].astype(np.float32)  # first 20 seconds

        # Use autocorrelation for better pitch detection
        chunk_size = sr // 4  # 250ms chunks
        pitches = []

        for i in range(0, len(y) - chunk_size, chunk_size):
            chunk = y[i:i + chunk_size]
            corr = np.correlate(chunk, chunk, mode='full')
            corr = corr[len(corr)//2:]
            min_lag = int(sr / 255)
            max_lag = int(sr / 85)
            if max_lag >= len(corr):
                continue
            peak_lag = np.argmax(corr[min_lag:max_lag]) + min_lag
            if corr[peak_lag] > 0.3 * corr[0]:
                pitch = sr / peak_lag
                pitches.append(pitch)

        if not pitches:
            print("[INFO] No pitch detected, defaulting to male.")
            return "male"

        median_pitch = np.median(pitches)
        print(f"[INFO] Median pitch: {median_pitch:.2f} Hz")
        return "female" if median_pitch > 180 else "male"

    except Exception as e:
        print(f"[WARN] Gender detection failed: {e}")
        return "male"

# ================= VOICE SELECTION =================
async def get_voice_for_language(target_language: str, gender: str) -> str:
    voices = await edge_tts.list_voices()
    matching = [v for v in voices if v["Locale"].lower().startswith(target_language.lower())]
    
    # DEBUG
    print(f"[DEBUG] Looking for: lang={target_language}, gender={gender}")
    print(f"[DEBUG] Matching voices: {[v['ShortName'] for v in matching]}")
    
    if not matching:
        print("[WARN] No voice found for language. Falling back to English.")
        matching = [v for v in voices if v["Locale"].lower().startswith("en")]

    gender_filtered = [v for v in matching if v["Gender"].lower() == gender.lower()]
    
    # DEBUG
    print(f"[DEBUG] Gender filtered: {[v['ShortName'] for v in gender_filtered]}")
    
    selected = gender_filtered[0]["ShortName"] if gender_filtered else matching[0]["ShortName"]
    print(f"[INFO] Selected voice: {selected} (gender={gender})")
    return selected

# ================= TTS =================
async def generate_tts(text: str, voice: str, output_file: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# ================= BUILD AUDIO WITH TIMING =================
def generate_translated_audio(segments, voice, output_path):
    final_audio = AudioSegment.silent(duration=0)

    for i, segment in enumerate(segments):
        start_ms = float(segment["start"]) * 1000
        text = segment["text"].strip()

        if not text:
            continue

        temp_file = f"temp_seg_{i}.mp3"
        asyncio.run(generate_tts(text, voice, temp_file))
        segment_audio = AudioSegment.from_file(temp_file, format="mp3")
        segment_audio= segment_audio.set_frame_rate(16000)

        silence_needed = start_ms - len(final_audio)
        if silence_needed > 0:
            final_audio += AudioSegment.silent(duration=silence_needed)

        final_audio += segment_audio
        os.remove(temp_file)

    final_audio.export(output_path, format="mp3")

# ================= MERGE AUDIO + VIDEO =================
def merge_audio_with_video(video_path: str, audio_path: str, output_path: str):
    video = mp.VideoFileClip(video_path)
    audio = mp.AudioFileClip(audio_path)
    final = video.set_audio(audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    video.close()
    audio.close()

# ================= MAIN PIPELINE =================
def run_pipeline(video_path: str, target_language: str, output_path: str):
    from lipsync import run_lipsync

    audio_path = "temp_audio.wav"
    translated_audio_path = "translated_audio.mp3"
    dubbed_no_lipsync = "dubbed_no_lipsync.mp4"

    try:
        print("[1/6] Extracting audio...")
        extract_audio(video_path, audio_path)

        print("[2/6] Transcribing...")
        result = transcribe_audio(audio_path)
        segments = result["segments"]

        print("[3/6] Detecting gender...")
        gender = detect_gender(audio_path, segments)
        print(f"[INFO] Gender: {gender}")

        print("[4/6] Selecting voice...")
        selected_voice = asyncio.run(get_voice_for_language(target_language, gender))

        print("[5/6] Translating and generating TTS...")
        for segment in segments:
            try:
                translated = GoogleTranslator(source='auto', target=target_language).translate(segment["text"])
                segment["text"] = translated
            except Exception as e:
                print(f"[WARN] Translation failed for segment: {e}")

        generate_translated_audio(segments, selected_voice, translated_audio_path)

        # Trim audio to match video length
        video_clip = mp.VideoFileClip(video_path)
        video_duration_ms = int(video_clip.duration * 1000)
        video_clip.close()
        audio_clip = AudioSegment.from_file(translated_audio_path)
        if len(audio_clip) > video_duration_ms:
            audio_clip = audio_clip[:video_duration_ms]
            audio_clip.export(translated_audio_path, format="mp3")
            print(f"[INFO] Trimmed audio to {video_duration_ms}ms")

        print("[6/6] Running Wav2Lip lip sync...")
        success = run_lipsync(video_path, translated_audio_path, output_path)

        if not success:
            print("[WARN] Lip sync failed, falling back to basic merge...")
            merge_audio_with_video(video_path, translated_audio_path, output_path)

        print(f"[✅] Done! Output: {output_path}")

    finally:
        for f in [audio_path, translated_audio_path, dubbed_no_lipsync]:
            if os.path.exists(f):
                os.remove(f)