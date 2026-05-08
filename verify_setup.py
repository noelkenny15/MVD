
import os
import subprocess
import sys

print("=" * 60)
print("DUBSYNC SETUP VERIFICATION")
print("=" * 60)

# 1. Check Python environment
print("\n1. Python Environment")
print(f"   Python: {sys.version.split()[0]}")
print(f"   Location: {sys.executable}")

# 2. Check PyTorch/CUDA
print("\n2. PyTorch & CUDA")
try:
    import torch
    print(f"   ✓ PyTorch: {torch.__version__}")
    print(f"   ✓ CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   ✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   ✓ Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 3. Check required packages
print("\n3. Required Python Packages")
packages = ['fastapi', 'uvicorn', 'moviepy', 'pydub', 'scipy', 'soundfile']
for pkg in packages:
    try:
        __import__(pkg)
        print(f"   ✓ {pkg}")
    except ImportError:
        print(f"   ✗ {pkg} - NOT INSTALLED")

# 4. Check AI models
print("\n4. AI Models")
try:
    import whisper
    print(f"   ✓ Whisper available")
except:
    print(f"   ✗ Whisper not installed")

try:
    import edge_tts
    print(f"   ✓ edge-tts available")
except:
    print(f"   ✗ edge-tts not installed")

try:
    from deep_translator import GoogleTranslator
    print(f"   ✓ deep-translator available")
except:
    print(f"   ✗ deep-translator not installed")

# 5. Check files/directories
print("\n5. Project Files")
files_to_check = [
    ('backend/main.py', 'FastAPI server'),
    ('backend/pipeline.py', 'Dubbing pipeline'),
    ('backend/lipsync.py', 'Lip sync wrapper'),
    ('frontend/package.json', 'React config'),
    ('Wav2Lip/inference.py', 'Wav2Lip inference'),
    ('Wav2Lip/checkpoints/wav2lip_gan.pth', 'Wav2Lip model'),
]

for filepath, description in files_to_check:
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"   {status} {description}: {filepath}")

# 6. Check ffmpeg
print("\n6. System Tools")
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    version = result.stdout.split('\n')[0]
    print(f"   ✓ ffmpeg: {version}")
except:
    print(f"   ✗ ffmpeg not found")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
