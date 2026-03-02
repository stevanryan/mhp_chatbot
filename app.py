import streamlit as st
import pandas as pd
import base64

from utils.loader import load_faq_json, load_quiz_json
from utils.matcher import FAQMatcher
from utils.gamification import init_game_state, add_points, get_badge, reset_chat_and_game
from utils.logger import log_interaction

FAQ_PATH = "data/faq_data.json"
QUIZ_PATH = "data/quiz_data.json"
LOG_PATH = "data/interaction_logs.csv"

st.set_page_config(
    page_title="Chatbot Edu-Wisata PLTMH",
    page_icon="💧", 
    layout="wide",
)


# Fungsi untuk membaca file lokal dan mengubahnya ke format base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path gambar lokal Anda
img_path = "img/tukbulus.jpg"

try:
    # Ubah gambar ke base64
    img_base64 = get_base64_of_bin_file(img_path)
    # Gunakan format data URI untuk background-image
    bg_img_url = f"data:image/jpeg;base64,{img_base64}"
except FileNotFoundError:
    st.error(f"File gambar tidak ditemukan di path: {img_path}")
    bg_img_url = "" # Fallback jika gambar tidak ada

custom_css = f"""
<style>
.title-banner {{
    background-image: linear-gradient(rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.55)), url('{bg_img_url}');
    background-size: cover;
    background-position: center;
    padding: 50px 20px;
    border-radius: 15px;
    margin-bottom: 25px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.title-banner h1 {{
    color: white !important;
    margin: 0;
    font-size: 2.6rem;
    font-weight: bold;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}}
.title-banner p {{
    color: #e0e0e0 !important;
    font-size: 1.1rem;
    margin-top: 10px;
    font-style: italic;
}}
</style>

<div class="title-banner">
    <h1>Chatbot Edu-Wisata Desa Tuk Bulus Pembangkit Listrik Tenaga Mikro Hidro (PLTMH)</h1>
    <p>Pencarian FAQ • Kemiripan TF-IDF • Gamifikasi</p>
</div>
"""

st.markdown(custom_css, unsafe_allow_html=True)


faq_items = load_faq_json(FAQ_PATH)
quiz_items = load_quiz_json(QUIZ_PATH)
matcher = FAQMatcher(faq_items=faq_items, threshold=0.30)

init_game_state()

if not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Halo! Tanyakan kepada saya tentang lokasi wisata, pembangkit listrik mikro hidro (PLTMH), keselamatan, atau kuis. "
                "Contoh pertanyaan: 'Apa itu PLTMH?' atau 'Apa aturan keselamatan yang harus diikuti pengunjung?'"
            ),
        }
    ]


st.write("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Poin", st.session_state.points)
with col2:
    st.metric("Lencana", get_badge(st.session_state.points))
with col3:
    st.metric("Progres Kuis", f"{min(st.session_state.quiz_index, len(quiz_items))}/{len(quiz_items)}")
with col4:

    st.write("")
    st.write("")
    if st.button("Mulai Ulang Sesi", use_container_width=True):
        reset_chat_and_game()
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Sesi telah dimulai ulang. Tanyakan sesuatu tentang lokasi wisata atau PLTMH kepada saya.",
            }
        ]
        st.rerun()

st.divider()

# ---------- Konten utama ----------
left, right = st.columns([2.2, 1.2])

with left:
    st.subheader("Obrolan")
    chat_container = st.container(height=500, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

with right:
    st.subheader("Belajar & Kuis")

    with st.expander("📘 Ringkasan PLTMH", expanded=True):
        st.write(
            "PLTMH (Pembangkit Listrik Tenaga Mikro Hidro) adalah sistem kelistrikan skala kecil yang memanfaatkan aliran air. "
            "Air menggerakkan turbin, turbin memutar generator, dan generator tersebut menghasilkan listrik."
        )
        st.write(
            "Lokasi wisata ini bersifat edukatif karena pengunjung dapat menikmati alam sambil belajar secara langsung bagaimana energi terbarukan bekerja."
        )

    with st.expander("🧠 Kuis", expanded=True):
        if not st.session_state.quiz_finished:
            current_idx = st.session_state.quiz_index
            if current_idx < len(quiz_items):
                q = quiz_items[current_idx]
                st.write(f"**Pertanyaan {current_idx + 1}**")
                st.write(q["question"])

                choice = st.radio(
                    "Pilih salah satu jawaban:",
                    q["options"],
                    key=f"quiz_choice_{current_idx}",
                    index=None,
                )

                if st.button("Kirim Jawaban Kuis", type="primary"):
                    if choice is None:
                        st.warning("Harap pilih jawaban sebelum mengirim.")
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
                            bot_reply=f"Dipilih: {choice} | Benar: {correct_option}",
                            total_points=st.session_state.points,
                            badge=get_badge(st.session_state.points),
                            extra=q["explanation"],
                        )

                        if is_correct:
                            st.success("Benar! +20 poin")
                        else:
                            st.error(f"Salah. Jawaban yang benar adalah: {correct_option}")
                        st.info(q["explanation"])

                        st.session_state.quiz_index += 1
                        if st.session_state.quiz_index >= len(quiz_items):
                            st.session_state.quiz_finished = True
                        st.rerun()
            else:
                st.session_state.quiz_finished = True

        if st.session_state.quiz_finished:
            st.success("Kuis selesai!")
            st.write(f"Skor kuis Anda: **{st.session_state.quiz_score}/{len(quiz_items)}**")
            st.write(f"Lencana Anda saat ini: **{get_badge(st.session_state.points)}**")
            if st.button("Mulai Ulang Kuis"):
                st.session_state.quiz_index = 0
                st.session_state.quiz_answered_ids = set()
                st.session_state.quiz_score = 0
                st.session_state.quiz_finished = False
                st.rerun()

    with st.expander("ℹ️ Saran Pertanyaan"):
        st.markdown(
            "- Apa itu PLTMH?\n"
            "- Bagaimana cara kerja PLTMH?\n"
            "- Apa saja manfaat PLTMH?\n"
            "- Fasilitas apa saja yang tersedia di sini?\n"
            "- Aturan keselamatan apa yang harus diikuti pengunjung?"
        )

user_query = st.chat_input("Ketik pertanyaan Anda di sini...")
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    result = matcher.search(user_query)
    bot_reply = result["answer"]
    matched_id = result.get("id") or ""
    score = result.get("score", 0.0)

    
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

with st.expander("📄 Pratinjau Log Interaksi (Opsional)"):
    try:
        logs = pd.read_csv(LOG_PATH)
        st.dataframe(logs.tail(20), use_container_width=True)
    except FileNotFoundError:
        st.info("Belum ada log. Mulai mengobrol atau jawab kuis untuk membuat log interaksi.")