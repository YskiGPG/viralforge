"""Minimal check that the Anthropic API key works.

Run:  python tests/check_anthropic.py
Expected: prints "ViralForge is alive" plus a token count.
"""

import sys
from pathlib import Path

# Make src/ importable when running this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import anthropic

import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

resp = client.messages.create(
    model=config.MODEL_FAST,  # use the cheap model to verify, saves credit
    max_tokens=50,
    messages=[{"role": "user", "content": "Say 'ViralForge is alive' and nothing else."}],
)

print(resp.content[0].text)
print(f"tokens used → in:{resp.usage.input_tokens} out:{resp.usage.output_tokens}")
print("✅ Anthropic OK")
