"""Agentverse-hosted version of uagent.py. build_hosted.py copies this to hosted/agent.py next to the flattened backend.
Agentverse fixes name/seed/address for hosted agents, and resets globals each call: kb is fetched, history lives in ctx.storage."""
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import requests
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (ChatAcknowledgement, ChatMessage, EndSessionContent,
                                                 TextContent, chat_protocol_spec)

from agents_conversation import ask, format_text

KB_URL = os.getenv("KB_URL", "https://raw.githubusercontent.com/vanisha2277/la-hacks/main/app/out/kb.json")

agent = Agent()
chat = Protocol(spec=chat_protocol_spec)


@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    question = msg.text().strip()
    if not question:
        return
    h = ctx.storage.get(sender) or []
    try:
        kb = requests.get(KB_URL, timeout=30).json()  # ponytail: 300 KB fetch per message, globals don't survive calls
        r = await asyncio.to_thread(ask, question, h[-6:], "junior", kb)
        reply = format_text(r)
        ctx.storage.set(sender, (h + [{"role": "user", "content": question},
                                      {"role": "assistant", "content": r["answer"]}])[-12:])
    except Exception as e:
        ctx.logger.exception("ask failed")
        reply = f"Sorry, I hit an error answering that: {e}"
    await ctx.send(sender, ChatMessage(content=[TextContent(type="text", text=reply),
                                                EndSessionContent(type="end-session")], msg_id=uuid4()))


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(chat, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
