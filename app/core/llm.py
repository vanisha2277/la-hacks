"""ASI:One client, JSON helper, and the traced tool-calling loop."""
import json
import re

from openai import OpenAI

import config

client = OpenAI(api_key=config.ASI1_API_KEY, base_url=config.ASI1_BASE_URL)


def parse_json(text):
    """Parse JSON from a model reply that may wrap it in fences or prose."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
        if not starts:
            raise
        start = min(starts)
        end = text.rfind("}" if text[start] == "{" else "]")
        return json.loads(text[start:end + 1])


def chat(messages, model=None, **kw):
    r = client.chat.completions.create(model=model or config.MODEL, messages=messages, **kw)
    return r.choices[0].message


def chat_json(messages, model=None):
    return parse_json(chat(messages, model).content or "")


def run_tools(messages, tools, dispatch, model=None, max_steps=12, on_step=None):
    """Chat loop that executes tool calls via dispatch(name, args) -> envelope.
    Returns (final_text, trace, messages). The trace is the real record of every call.
    on_step(entry) is called after each tool call (for streaming progress)."""
    messages = list(messages)
    trace = []
    for _ in range(max_steps):
        msg = chat(messages, model, tools=tools)
        if not msg.tool_calls:
            return msg.content or "", trace, messages
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
            except Exception as e:  # bad args / unknown tool: tell the model, keep going
                args, result = call.function.arguments, {"error": str(e), "data": None, "citations": [], "empty": True}
            trace.append({"step": len(trace) + 1, "tool": call.function.name, "args": args, "result": result})
            if on_step:
                on_step(trace[-1])
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    messages.append({"role": "user", "content": "Tool budget used up. Give your final JSON answer now with what you have."})
    return chat(messages, model).content or "", trace, messages
