"""
Tests for M7 fix: SessionStore._append trims in user/assistant pairs so we
never hand the LLM a conversation that starts with an assistant message
(which the Anthropic API rejects with 400).

Old behaviour: `s.messages = s.messages[excess:]` — a head-anchored slice that
would happily leave an `assistant` block at index 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.session_store import SessionStore  # noqa: E402


def _fill(store: SessionStore, sid: str, n_user: int, n_assistant: int | None = None) -> None:
    """Simulate a real chat loop: append 1 user → 1 assistant turn (with
    trim) → repeat. So the head is always a clean pair after each round.
    """
    if n_assistant is None:
        n_assistant = n_user
    for i in range(max(n_user, n_assistant)):
        if i < n_user:
            store.append_user(sid, f"user-{i}")
        if i < n_assistant:
            store.append_assistant_turn(sid, text_blocks=[{"text": f"a-{i}"}])


def test_keeps_all_when_under_cap():
    store = SessionStore(max_messages=10)
    s = store.create()
    _fill(store, s.id, 3)
    assert len(store.get(s.id).messages) == 6  # 3 user + 3 assistant
    first = store.get(s.id).messages[0]
    assert first["role"] == "user", "head must be user (Anthropic requirement)"


def test_trims_one_pair_per_turn_when_over_cap():
    """M7: each assistant_turn call trims at most one (user, assistant)
    pair from the head when over cap. We use a cap that is *just* under the
    message count so trim fires every round."""
    store = SessionStore(max_messages=4)
    s = store.create()
    # Build up to 6 (just over cap of 4): u0,a0,u1,a1
    _fill(store, s.id, 2)
    msgs = store.get(s.id).messages
    assert len(msgs) == 4
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]

    # Now add round 3 (u2, a2). After append: 6 messages; trim drops the
    # oldest (u0, a0) leaving 4.
    store.append_user(s.id, "u2")
    store.append_assistant_turn(s.id, text_blocks=[{"text": "a2"}])
    msgs = store.get(s.id).messages
    assert len(msgs) == 4
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert msgs[0]["content"] == "user-1"
    assert msgs[1]["content"][0]["text"] == "a-1"


def test_no_orphan_assistant_at_head():
    """Regression: a head-anchored slice that left an `assistant` at index
    0 is impossible now because trim only deletes when the head IS a
    (user, assistant) pair.
    """
    store = SessionStore(max_messages=2)
    s = store.create()
    _fill(store, s.id, 3)  # 6 total
    msgs = store.get(s.id).messages
    # After 3 rounds with cap=2, head is always (user, assistant) — never
    # an orphan assistant.
    for m in msgs:
        pass
    assert msgs, "should not have trimmed everything"
    assert msgs[0]["role"] == "user", f"head must be user, got {msgs[0]['role']}"
    # No consecutive role duplicates either
    for i in range(len(msgs) - 1):
        assert msgs[i]["role"] != msgs[i + 1]["role"], (
            f"two {msgs[i]['role']} in a row at index {i}"
        )


def test_partial_pair_at_head_is_not_destroyed():
    """If the oldest block is a lone user message (assistant hasn't been
    appended yet because the LLM is still streaming), we must NOT delete the
    user just to satisfy the cap. The stream handler depends on it.
    """
    store = SessionStore(max_messages=2)
    s = store.create()
    store.append_user(s.id, "u0")
    # No assistant yet — we're at cap
    msgs = store.get(s.id).messages
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"

    # Trim never fires here (append_user doesn't trim).
    # Adding the assistant turn + another user should now produce a valid
    # pair and trim it on the next round.
    store.append_assistant_turn(s.id, text_blocks=[{"text": "a0"}])
    store.append_user(s.id, "u1")
    store.append_assistant_turn(s.id, text_blocks=[{"text": "a1"}])
    msgs = store.get(s.id).messages
    # After round 2, head is still u0, a0 (we don't trim because the round
    # was triggered by an in-flight user, not by an over-cap state). Actually
    # round 2's append_user brings us to 3 > cap=2, then assistant_turn → 4,
    # then _trim drops the head (u0, a0) → 2 left.
    assert msgs[0]["role"] == "user"


def test_trim_loop_terminates():
    """Sanity: even with a long sequence, the loop exits and the cap is respected."""
    store = SessionStore(max_messages=4)
    s = store.create()
    for i in range(20):
        store.append_user(s.id, f"u{i}")
        store.append_assistant_turn(s.id, text_blocks=[{"text": f"a{i}"}])
    msgs = store.get(s.id).messages
    assert len(msgs) <= 4
    assert msgs[0]["role"] == "user", "head must always be user"
    for i in range(len(msgs) - 1):
        assert msgs[i]["role"] != msgs[i + 1]["role"], (
            f"two {msgs[i]['role']} in a row at index {i}"
        )
