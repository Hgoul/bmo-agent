import sounddevice as sd
import numpy as np
from openwakeword.model import Model
import time
import sys

WAKE_WORD_MODEL = "./wakeword.onnx"
WAKE_WORD_THRESHOLD = 0.5
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms at 16kHz

try:
    oww_model = Model(wakeword_model_paths=[WAKE_WORD_MODEL])
except TypeError:
    oww_model = Model(wakeword_models=[WAKE_WORD_MODEL])

duration = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
detected_events = []
start = time.time()

def callback(indata, frames, time_info, status):
    audio_data = indata[:, 0] if indata.ndim > 1 else indata
    prediction = oww_model.predict(audio_data)
    for mdl in oww_model.prediction_buffer.keys():
        score = list(oww_model.prediction_buffer[mdl])[-1]
        if score > 0.15:
            print(f"[{time.time()-start:5.1f}s] {mdl}: {score:.3f}", flush=True)
        if score > WAKE_WORD_THRESHOLD:
            detected_events.append((time.time()-start, mdl, score))

print(f"Listening for {duration:.0f}s on the default input device (16kHz)...", flush=True)
with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE, callback=callback):
    sd.sleep(int(duration * 1000))

print("---", flush=True)
if detected_events:
    print(f"DETECTED {len(detected_events)} time(s):", flush=True)
    for t, mdl, score in detected_events:
        print(f"  at {t:.1f}s -> {mdl} (score {score:.2f})", flush=True)
else:
    print("NOT DETECTED - no score crossed the 0.5 threshold.", flush=True)
