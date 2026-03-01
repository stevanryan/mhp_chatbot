import streamlit as st
import pandas as pd

from utils.loader import load_faq_json, load_quiz_json
from utils.matcher import FAQMatcher
from utils.gamification import init_game_state, add_points, get_badge, reset_chat_and_game
from utils.logger import log_interaction

FAQ_PATH = "data/faq_data.json"
QUIZ_PATH = "data/quiz_data.json"
LOG_PATH = "data/interaction_logs.csv"

st.set_page_config(
    page_title="MHP Edu-Tourism Chatbot",
    page_icon="💧",
    layout="wide",
)

st.title("💧 Educational Tourism Chatbot for Mini Hydropower")
st.caption("FAQ retrieval + TF-IDF similarity + gamification")

faq_items = load_faq_json(FAQ_PATH)
quiz_items = load_quiz_json(QUIZ_PATH)
matcher = FAQMatcher(faq_items=faq_items, threshold=0.30)

init_game_state()

if not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! Ask me about the tourism site, mini hydropower, safety, or the quiz. "
                "Example questions: 'What is mini hydropower?' or 'What safety rules should visitors follow?'"
            ),
        }
    ]

# ---------- Top status row ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Points", st.session_state.points)
with col2:
    st.metric("Badge", get_badge(st.session_state.points))
with col3:
    st.metric("Quiz Progress", f"{min(st.session_state.quiz_index, len(quiz_items))}/{len(quiz_items)}")
with col4:
    if st.button("Reset Session"):
        reset_chat_and_game()
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Session reset. Ask me something about the site or mini hydropower.",
            }
        ]
        st.rerun()

# ---------- Main content ----------
left, right = st.columns([2.2, 1.2])

with left:
    st.subheader("Chat")
    chat_container = st.container(border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

with right:
    st.subheader("Learn & Quiz")

    with st.expander("📘 Mini Hydropower Summary", expanded=True):
        st.write(
            "Mini hydropower is a small-scale electricity system that uses flowing water. "
            "Water moves a turbine, the turbine drives a generator, and the generator produces electricity."
        )
        st.write(
            "This tourism site is educational because visitors can enjoy nature while learning how renewable energy works in practice."
        )

    with st.expander("🧠 Quiz", expanded=True):
        if not st.session_state.quiz_finished:
            current_idx = st.session_state.quiz_index
            if current_idx < len(quiz_items):
                q = quiz_items[current_idx]
                st.write(f"**Question {current_idx + 1}**")
                st.write(q["question"])

                choice = st.radio(
                    "Choose one answer:",
                    q["options"],
                    key=f"quiz_choice_{current_idx}",
                    index=None,
                )

                if st.button("Submit Quiz Answer", type="primary"):
                    if choice is None:
                        st.warning("Please choose an answer before submitting.")
                    else:
                        correct_option = q["options"][q["correct_index"]]
                        is_correct = choice == correct_option

                        if q["id"] not in st.session_state.quiz_answered_ids:
                            if is_correct:
                                add_points(20)
                                st.session_state.quiz_score += 1
                            st.session_state.quiz_answered_ids.add(q["id"])

                        log_interaction(
                            filepath=LOG_PATH,
                            session_id=st.session_state.session_id,
                            event_type="quiz",
                            user_query=q["question"],
                            matched_id=q["id"],
                            similarity_score=1.0 if is_correct else 0.0,
                            bot_reply=f"Selected: {choice} | Correct: {correct_option}",
                            total_points=st.session_state.points,
                            badge=get_badge(st.session_state.points),
                            extra=q["explanation"],
                        )

                        if is_correct:
                            st.success("Correct! +20 points")
                        else:
                            st.error(f"Incorrect. Correct answer: {correct_option}")
                        st.info(q["explanation"])

                        st.session_state.quiz_index += 1
                        if st.session_state.quiz_index >= len(quiz_items):
                            st.session_state.quiz_finished = True
                        st.rerun()
            else:
                st.session_state.quiz_finished = True

        if st.session_state.quiz_finished:
            st.success("Quiz completed!")
            st.write(f"Your quiz score: **{st.session_state.quiz_score}/{len(quiz_items)}**")
            st.write(f"Your current badge: **{get_badge(st.session_state.points)}**")
            if st.button("Restart Quiz"):
                st.session_state.quiz_index = 0
                st.session_state.quiz_answered_ids = set()
                st.session_state.quiz_score = 0
                st.session_state.quiz_finished = False
                st.rerun()

    with st.expander("ℹ️ Suggested Questions"):
        st.markdown(
            "- What is mini hydropower?\n"
            "- How does mini hydropower work?\n"
            "- What are the benefits of mini hydropower?\n"
            "- What facilities are available?\n"
            "- What safety rules should visitors follow?"
        )

# chat_input should stay in the main area (not sidebar/forms/tabs for best compatibility)
user_query = st.chat_input("Ask your question here...")
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    result = matcher.search(user_query)
    bot_reply = result["answer"]
    matched_id = result.get("id") or ""
    score = result.get("score", 0.0)

    # Award points once per matched FAQ ID
    if matched_id and matched_id not in st.session_state.answered_faq_ids:
        add_points(result.get("points", 5))
        st.session_state.answered_faq_ids.add(matched_id)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    log_interaction(
        filepath=LOG_PATH,
        session_id=st.session_state.session_id,
        event_type="chat",
        user_query=user_query,
        matched_id=matched_id,
        similarity_score=score,
        bot_reply=bot_reply,
        total_points=st.session_state.points,
        badge=get_badge(st.session_state.points),
        extra=result.get("match_type", ""),
    )

    st.rerun()

# Optional log preview
with st.expander("📄 Preview Interaction Logs (optional)"):
    try:
        logs = pd.read_csv(LOG_PATH)
        st.dataframe(logs.tail(20), use_container_width=True)
    except FileNotFoundError:
        st.info("No logs yet. Start chatting or answer the quiz to generate logs.")
