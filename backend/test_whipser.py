import whisper
import torch

print('Device:', 'cuda' if torch.cuda.is_available() else 'cpu')
model = whisper.load_model('small', device='cuda')
result = model.transcribe('uploads/Motivational_Minute_1_-_Believe_in_Yourself_720p', fp16=True)
print(result['text'][:200])