import time

start = time.perf_counter()

import torch
from qwen_asr import Qwen3ASRModel

from qp_voice.asr_model import resolve_asr_model

model = Qwen3ASRModel.from_pretrained(
    resolve_asr_model()[0],
    dtype=torch.float32,  # ✅ CPU-safe
    device_map="cpu",  # ✅ correct
    max_inference_batch_size=1,  # ✅ realistic for CPU
    max_new_tokens=256,
)

results = model.transcribe(
    audio="/home/copper/Downloads/Father.wav",
    language="English",  # ✅ explicitly force English (better accuracy)
)
end = time.perf_counter()

print(f"Elapsed time: {end - start:.3f} seconds")
print(results[0].language)
print(results[0].text)
