"""Smoke test: ASI:One key, tool calling, and Agentverse seed. Run: python scripts/test_keys.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from openai import OpenAI

assert config.ASI1_API_KEY, "ASI1_API_KEY missing in .env"
assert config.AGENT_SEED_PHRASE, "AGENT_SEED_PHRASE missing in .env"

client = OpenAI(api_key=config.ASI1_API_KEY, base_url=config.ASI1_BASE_URL)
print(f"model: {config.MODEL} (heavy: {config.MODEL_HEAVY})")

# 1. plain chat
r = client.chat.completions.create(
    model=config.MODEL, messages=[{"role": "user", "content": "Reply with exactly: pong"}]
)
print("1. chat:", r.choices[0].message.content.strip())

# 2. tool calling (the whole agent depends on this)
tools = [{"type": "function", "function": {
    "name": "get_component",
    "description": "Look up a P&ID component by tag.",
    "parameters": {"type": "object", "properties": {"tag": {"type": "string"}}, "required": ["tag"]},
}}]
r = client.chat.completions.create(
    model=config.MODEL, tools=tools,
    messages=[{"role": "user", "content": "What is V-200? Use the tool."}],
)
calls = r.choices[0].message.tool_calls or []
assert calls, f"no tool call returned: {r.choices[0].message.content!r}"
args = json.loads(calls[0].function.arguments)
print("2. tool call:", calls[0].function.name, args)
assert args.get("tag") == "V-200", "tool called with wrong args"

# 3. Agentverse identity from seed
try:
    from uagents import Agent
    print("3. agent address:", Agent(name="pid-agent", seed=config.AGENT_SEED_PHRASE).address)
except ImportError:
    print("3. skipped (uagents not installed)")

print("OK")
