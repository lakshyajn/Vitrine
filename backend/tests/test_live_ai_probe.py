import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env")
key = os.environ.get("NEBIUS_API_KEY")
fast_key = os.environ.get("NEMOTRON_FAST_API_KEY")
model_ultra = os.environ.get("NEBIUS_MODEL_ID", "nvidia/nemotron-3-ultra-550b-a55b")
model_fast = os.environ.get("NEMOTRON_FAST_MODEL_ID", "nvidia/nemotron-3.5-super-vl-120b-a12b")

print(f"Testing Ultra model '{model_ultra}' on NVIDIA NIM...")
try:
    r = httpx.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model_ultra,
            "messages": [{"role": "user", "content": "Respond strictly in JSON: {\"status\": \"ok\"}"}],
            "response_format": {"type": "json_object"}
        },
        timeout=30.0
    )
    print(f"Ultra status: {r.status_code}")
    if r.status_code == 200:
        print("Ultra response:", r.json()["choices"][0]["message"]["content"][:100])
    else:
        print("Ultra error:", r.text[:200])
except Exception as e:
    print("Ultra exception:", e)

print(f"\nTesting Fast model '{model_fast}' on NVIDIA NIM...")
try:
    r2 = httpx.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {fast_key}"},
        json={
            "model": model_fast,
            "messages": [{"role": "user", "content": "Respond strictly in JSON: {\"status\": \"ok\"}"}],
            "response_format": {"type": "json_object"}
        },
        timeout=30.0
    )
    print(f"Fast status: {r2.status_code}")
    if r2.status_code == 200:
        print("Fast response:", r2.json()["choices"][0]["message"]["content"][:100])
    else:
        print("Fast error:", r2.text[:200])
except Exception as e:
    print("Fast exception:", e)

