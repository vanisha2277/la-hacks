"""Agentverse / ASI:One front door. Same ask() as the UI, rendered as plain text.
Run: python agentverse/uagent.py  (then open the inspector link it prints and connect the mailbox)"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (ChatAcknowledgement, ChatMessage, EndSessionContent,
                                                 TextContent, chat_protocol_spec)

import config
from agents.conversation import ask, format_text

agent = Agent(name="pid-senior-engineer", seed=config.AGENT_SEED_PHRASE, port=8001, mailbox=True,
              publish_agent_details=True, readme_path=str(Path(__file__).with_name("AGENT_README.md")))
chat = Protocol(spec=chat_protocol_spec)
history = {}  # ponytail: in-memory per-sender history, lost on restart


@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    question = msg.text().strip()
    if not question:
        return
    h = history.setdefault(sender, [])
    try:
        r = await asyncio.to_thread(ask, question, h[-6:], "junior")  # ASI:One users are always junior (read-only)
        reply = format_text(r)
        h += [{"role": "user", "content": question}, {"role": "assistant", "content": r["answer"]}]
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
    print("agent address:", agent.address)
    agent.run()
