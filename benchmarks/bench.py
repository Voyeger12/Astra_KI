import time
import json
import os
import sys
# ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules.database import Database
from modules.ollama_client import OllamaClient
from config import DEFAULT_MODEL

results = {}

# DB benchmark
db = Database()
chat_name = "Benchmark Chat"
# ensure chat exists
db.create_chat(chat_name)

save_times = []
for i in range(10):
    t0 = time.perf_counter()
    ok = db.save_message(chat_name, "user", f"Test message {i}")
    t1 = time.perf_counter()
    save_times.append((t1-t0)*1000)

results['db'] = {
    'samples_ms': save_times,
    'avg_ms': sum(save_times)/len(save_times),
    'min_ms': min(save_times),
    'max_ms': max(save_times)
}

# Ollama benchmark (small chat)
ollama = OllamaClient()
model = DEFAULT_MODEL
chat_prompt = [{"role": "system", "content": "You are a helpful assistant."},
               {"role": "user", "content": "Say hello in one sentence."}]

ollama_times = []
for i in range(2):
    t0 = time.perf_counter()
    try:
        resp = ollama.chat(model, chat_prompt)
        ok = True
    except Exception as e:
        resp = str(e)
        ok = False
    t1 = time.perf_counter()
    ollama_times.append({'ms': (t1-t0)*1000, 'ok': ok, 'resp_preview': resp[:120] if isinstance(resp, str) else str(resp)})

results['ollama'] = {
    'model': model,
    'samples': ollama_times,
    'avg_ms': sum(s['ms'] for s in ollama_times)/len(ollama_times)
}

print(json.dumps(results, indent=2))
