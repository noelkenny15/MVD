# lipsync.py - Fixed Version
# Wav2Lip integration for DubSync

import os
import sys
import subprocess

# CORRECT PATHS - WITH QUOTES!
WAV2LIP_PATH = os.path.join(os.path.dirname(__file__), '..', 'Wav2Lip')
WAV2LIP_MODEL = os.path.join(WAV2LIP_PATH, 'checkpoints', 'wav2lip_gan.pth')
INFERENCE_SCRIPT = os.path.join(WAV2LIP_PATH, 'inference.py')

def run_lipsync(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    Run Wav2Lip inference to generate lip-synced video
    
    Args:
        video_path: Path to original video
        audio_path: Path to dubbed audio (WAV)
        output_path: Path to output video
        
    Returns:
        True if successful, False otherwise
    """
    
    # Verify checkpoint exists
    if not os.path.exists(WAV2LIP_MODEL):
        print(f"[ERROR] Wav2Lip model not found at: {WAV2LIP_MODEL}")
        return False
    
    # Verify inference script exists
    if not os.path.exists(INFERENCE_SCRIPT):
        print(f"[ERROR] Wav2Lip inference.py not found at: {INFERENCE_SCRIPT}")
        return False
    
    print("[LipSync] Starting Wav2Lip inference...")
    
    # Build command
    cmd = [
        sys.executable,
        INFERENCE_SCRIPT,
        "--checkpoint_path", os.path.abspath(WAV2LIP_MODEL),
        "--face", os.path.abspath(video_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path),
        "--resize_factor", "1",
        "--nosmooth",
        "--pads", "0", "10", "0", "0",
        "--face_det_batch_size", "2",      # For RTX 3050 (4GB)
        "--wav2lip_batch_size", "64",      # For RTX 3050 (4GB)
    ]
    
    try:
        # Run Wav2Lip inference
        result = subprocess.run(
            cmd,
            cwd=os.path.abspath(WAV2LIP_PATH),
            timeout=600,  # 10 minute timeout
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Check return code
        if result.returncode != 0:
            print(f"[ERROR] Wav2Lip failed with return code {result.returncode}")
            # Print last 2000 chars of output for debugging
            output_tail = result.stdout[-2000:] if result.stdout else "No output"
            print(f"[OUTPUT] {output_tail}")
            return False
        
        print("[LipSync] Lip-sync completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Wav2Lip timed out after 600 seconds")
        return False
        
    except Exception as e:
        print(f"[ERROR] Wav2Lip execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wav2lip_setup() -> bool:
    """Test if Wav2Lip is properly configured"""
    print("\n" + "="*60)
    print("WAV2LIP SETUP TEST")
    print("="*60)
    
    # Test 1: Check paths
    print(f"\n1. Path Configuration")
    print(f"   Wav2Lip Path: {WAV2LIP_PATH}")
    print(f"   Checkpoint: {WAV2LIP_MODEL}")
    print(f"   Inference: {INFERENCE_SCRIPT}")
    
    # Test 2: Check checkpoint exists
    print(f"\n2. Checkpoint File")
    if os.path.exists(WAV2LIP_MODEL):
        size = os.path.getsize(WAV2LIP_MODEL) / 1e9
        print(f"   ✓ EXISTS: {size:.1f} GB")
    else:
        print(f"   ✗ MISSING")
        return False
    
    # Test 3: Check inference script exists
    print(f"\n3. Inference Script")
    if os.path.exists(INFERENCE_SCRIPT):
        print(f"   ✓ EXISTS")
    else:
        print(f"   ✗ MISSING")
        return False
    
    # Test 4: Check parent directory structure
    print(f"\n4. Directory Structure")
    print(f"   Wav2Lip dir: {os.path.isdir(WAV2LIP_PATH)}")
    print(f"   Checkpoints dir: {os.path.isdir(os.path.dirname(WAV2LIP_MODEL))}")
    
    print("\n" + "="*60)
    print("✓ ALL CHECKS PASSED")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    # Test setup when running directly
    test_wav2lip_setup()