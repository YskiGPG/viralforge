"""ViralForge — Streamlit chat frontend (Phase 6).

A chat interface over the orchestrator that:
  - streams the agent's output token by token (6.1),
  - shows which Skills and Tools are running in real time via the progress hook (6.1),
  - offers a "try a different angle" regenerate control (6.2),
  - provides quick-start demo examples (6.3),
  - and a Claude-style left sidebar with "New chat" + clickable session history (Change 3).

Run:  streamlit run app.py     (needs a filled-in .env, same as the CLI)

Conversations are session-scoped (st.session_state) — they reset on browser refresh / app
restart, which is acceptable for this project. STRETCH (optional persistence): dump each
conversation's `messages` to a local JSON file (e.g. .chat_history.json) on every turn and reload
it on startup; rebuild a fresh orchestrator.Session per conversation (the Session's in-memory
last_plan won't survive, but the visible transcript will). Left out by default to keep it simple.
"""

import sys
from pathlib import Path

# Make src/ importable (orchestrator and friends import each other as top-level modules).
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st

import orchestrator

st.set_page_config(page_title="ViralForge", page_icon="🎬", layout="centered")

# Demo examples (6.3): the primary climbing case plus two rotating ideas.
EXAMPLES = [
    "I want to film myself singing while rock climbing",
    "A 60-second tutorial on making cold brew coffee at home",
    "POV: my cat reacts to different sounds",
]


# ── Conversation state ───────────────────────────────────────────────────────
def _new_conversation() -> dict:
    """Create a fresh conversation (its own orchestrator.Session) and make it current."""
    st.session_state.counter += 1
    conv = {
        "id": st.session_state.counter,
        "title": "New chat",
        "messages": [],                     # [{"role", "content"}]
        "session": orchestrator.Session(),  # holds this chat's plan memory
        "last_concept": None,               # last full-plan concept, for regenerate
    }
    st.session_state.conversations.append(conv)
    st.session_state.current_id = conv["id"]
    return conv


if "conversations" not in st.session_state:
    st.session_state.conversations = []
    st.session_state.current_id = None
    st.session_state.counter = 0
    st.session_state.pending = None  # a prompt queued by a button click
    _new_conversation()


def _current() -> dict:
    return next(c for c in st.session_state.conversations if c["id"] == st.session_state.current_id)


def queue(prompt: str) -> None:
    """Queue a prompt (from a button) and rerun so the main flow processes it."""
    st.session_state.pending = prompt
    st.rerun()


# ── Sidebar: New chat + clickable history ────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 ViralForge")
    if st.button("➕  New chat", use_container_width=True):
        _new_conversation()
        st.rerun()

    st.markdown("##### Chats")
    # Most-recent first.
    for conv in reversed(st.session_state.conversations):
        is_active = conv["id"] == st.session_state.current_id
        if st.button(
            conv["title"],
            key=f"conv_{conv['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_id = conv["id"]
            st.rerun()

cur = _current()

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🎬 ViralForge")
st.caption("Conversational planning for YouTube Shorts — grounded in real YouTube + Reddit data.")

with st.expander("Try an example", expanded=not cur["messages"]):
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, use_container_width=True, key=f"ex_{ex[:20]}"):
            queue(ex)

# ── Replay current conversation ──────────────────────────────────────────────
for msg in cur["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Regenerate control (6.2) — only meaningful once a plan exists in this chat.
if cur["last_concept"]:
    if st.button("🔄 Try a different angle", help="Re-plan the same idea with a fresh creative angle"):
        queue(
            f"{cur['last_concept']}\n\n"
            "Give a completely different creative angle than your previous plan for this idea."
        )


def generate(prompt: str, conv: dict) -> str:
    """Run the orchestrator with a live progress panel and token streaming, return the answer."""
    status = st.status("🧠 ViralForge is planning…", expanded=True)
    live = status.empty()
    buf = {"text": ""}

    def on_event(kind: str, data: dict) -> None:
        if kind == "step":
            status.update(label=data["label"])
            status.write(f"➡️ {data['label']}")
            buf["text"] = ""  # start a fresh live view for the new step
        elif kind == "tool":
            status.write(f"🔧 tool · `{data['name']}` {data.get('input', '')}")
        elif kind == "skill":
            status.write(f"📄 progressive disclosure · loaded skill `{data['name']}`")
        elif kind == "route":
            tail = f" → `{data['skill']}`" if data.get("skill") else ""
            status.write(f"🧭 route · **{data['intent']}**{tail}")
        elif kind == "token":
            label = data.get("label")
            if label and str(label).startswith("_"):
                return  # internal call (e.g. the router's JSON) — don't show
            buf["text"] += data["text"]
            live.markdown(buf["text"] + "▌")

    orchestrator.set_progress(on_event)
    orchestrator.reset_usage()
    try:
        answer = conv["session"].handle(prompt)
    finally:
        orchestrator.set_progress(None)
    usage = orchestrator.reset_usage()

    live.empty()
    tokens = sum(u["in"] + u["out"] for u in usage)
    status.update(
        label=f"✅ Done · {len(usage)} model calls · {tokens:,} tokens",
        state="complete",
        expanded=False,
    )
    st.markdown(answer)

    if answer.startswith("# ViralForge plan"):
        conv["last_concept"] = prompt.split("\n\n")[0]
    return answer


# ── Handle input (chat box or a queued button prompt) ────────────────────────
prompt = st.chat_input("Describe a Short idea, or refine the current plan…")
if st.session_state.pending:
    prompt, st.session_state.pending = st.session_state.pending, None

if prompt:
    # Auto-title the conversation from its first user message.
    if not cur["messages"]:
        cur["title"] = (prompt[:38] + "…") if len(prompt) > 39 else prompt

    cur["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        answer = generate(prompt, cur)
    cur["messages"].append({"role": "assistant", "content": answer})
