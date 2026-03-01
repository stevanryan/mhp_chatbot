import uuid
import streamlit as st


def init_game_state():
    defaults = {
        "session_id": str(uuid.uuid4()),
        "points": 0,
        "answered_faq_ids": set(),
        "messages": [],
        "quiz_index": 0,
        "quiz_answered_ids": set(),
        "quiz_score": 0,
        "quiz_finished": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat_and_game():
    keep_session_id = st.session_state.get("session_id", str(uuid.uuid4()))
    st.session_state.clear()
    st.session_state.session_id = keep_session_id
    init_game_state()


def add_points(value: int):
    st.session_state.points += int(value)


def get_badge(points: int) -> str:
    if points >= 100:
        return "Mini Hydropower Ambassador"
    if points >= 60:
        return "Energy Explorer"
    if points >= 30:
        return "Explorer Beginner"
    return "New Visitor"
