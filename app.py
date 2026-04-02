import streamlit as st
import pandas as pd
import base64

from utils.loader import load_faq_json, load_quiz_json
from utils.matcher import FAQMatcher
from utils.gamification import init_game_state, add_points, get_badge, reset_chat_and_game
from utils.logger import log_interaction

FAQ_PATH = "data/faq_data2.json"
QUIZ_PATH = "data/quiz_data2.json"
LOG_PATH = "data/interaction_logs.csv"

st.set_page_config(
    page_title="Chatbot Edu-Wisata PLTMH",
    page_icon="💧", 
    layout="wide",
)


# Function to read local file and convert it to base64 format
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "img/tukbulus.jpg"
try:
    img_base64 = get_base64_of_bin_file(img_path)
    bg_img_url = f"data:image/jpeg;base64,{img_base64}"
except FileNotFoundError:
    bg_img_url = "" 

custom_css = f"""
<style>
/* Style untuk Banner Judul */
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

[data-testid="stChatInput"] {{
    border: 2px solid #1E88E5 !important; /* Border luar biru tebal */
    border-radius: 15px !important;
    background-color: white !important; /* Paksa container jadi putih bersih */
    padding: 4px !important;
    box-shadow: 0 4px 10px rgba(30, 136, 229, 0.2) !important;
    transition: .3s;
}}

[data-testid="stChatInput"]:focus-within {{
    box-shadow: 0 4px 15px rgba(30, 136, 229, 0.5) !important;
}}

[data-testid="stChatInput"] div {{
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}

[data-testid="stChatInput"] textarea {{
    font-size: 1.1rem !important;
    color: #333 !important;
    background-color: transparent !important;
    outline: none !important;
    border: none !important;
    box-shadow: none !important;
}}

[data-testid="stChatInput"] textarea:focus {{
    outline: none !important;
    border: none !important;
    box-shadow: none !important;
}}

[data-testid="stChatInput"] textarea::placeholder {{
    color: #888 !important; 
    opacity: 0.8;
}}

[data-testid="stChatInput"] button {{
    background-color: #1E88E5 !important;
    color: white !important;
    border-radius: 50% !important;
    padding: 10px !important;
}}
</style>
"""

faq_items = load_faq_json(FAQ_PATH)
quiz_items = load_quiz_json(QUIZ_PATH)
matcher = FAQMatcher(faq_items=faq_items, threshold=0.30)

init_game_state()

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

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

with st.sidebar:
    st.title("🧭 Navigasi Menu")
    
    if st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.error("🔒 Ujian Berlangsung: Navigasi Terkunci")
        nav_options = ["🧠 Kuis Interaktif"]
        default_index = 0
    else:
        nav_options = ["💬 Chatbot Utama", "📖 Ruang Belajar", "🧠 Kuis Interaktif"]
        
        if st.session_state.quiz_finished:
            default_index = 2
        else:
            default_index = 0

    page_selection = st.radio(
        "Pergi ke halaman:",
        nav_options,
        index=default_index
    )
    
    st.divider()
    
    st.subheader("Status Anda")
    st.metric("Lencana", get_badge(st.session_state.points))
    
    colA, colB = st.columns(2)
    with colA:
        st.metric("Poin", st.session_state.points)
    with colB:
        st.metric("Progres Kuis", f"{min(st.session_state.quiz_index, len(quiz_items))}/{len(quiz_items)}")
    
    st.divider()
    
    # Reset session button
    if st.button("Mulai Ulang Sesi", use_container_width=True):
        reset_chat_and_game()
        st.session_state.quiz_started = False # Make sure quiz lock is reset when starting a new session
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Sesi telah dimulai ulang. Tanyakan sesuatu tentang lokasi wisata atau PLTMH kepada saya.",
            }
        ]
        st.rerun()

    # with st.expander("📄 Log Interaksi (Admin)"):
    #     try:
    #         logs = pd.read_csv(LOG_PATH)
    #         st.dataframe(logs.tail(5), use_container_width=True)
    #     except FileNotFoundError:
    #         st.info("Belum ada log.")


# --- PAGE ROUTING ---
# Page 1: Main Chatbot Interface
if page_selection == "💬 Chatbot Utama":
    st.markdown(custom_css, unsafe_allow_html=True)
    st.markdown("""
        <div class="title-banner">
            <h1>Chatbot Edu-Wisata Desa Tuk Bulus PLTMH</h1>
            <p>Pencarian FAQ • Kemiripan TF-IDF • Gamifikasi</p>
        </div>
    """, unsafe_allow_html=True)

    chat_container = st.container(height=320, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
    with st.expander("ℹ️ Saran Pertanyaan"):
        st.markdown(
            "- Apa itu PLTMH?\n"
            "- Bagaimana cara kerja PLTMH?\n"
            "- Apa saja manfaat PLTMH?\n"
            "- Fasilitas apa saja yang tersedia di sini?\n"
            "- Aturan keselamatan apa yang harus diikuti pengunjung?"
        )
                
    # Chat input
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


# Page 2: Learning section
elif page_selection == "📖 Ruang Belajar":
    st.title("📖 Ruang Belajar PLTMH")
    st.write("Selamat datang di pusat materi Edu-Wisata. Silakan pelajari informasi di bawah ini sebelum menguji pengetahuan Anda di halaman Kuis!")
    st.divider()
    
    st.header("Ringkasan PLTMH")
    st.write(
        "PLTMH (Pembangkit Listrik Tenaga Mikro Hidro) adalah sistem kelistrikan skala kecil yang memanfaatkan aliran air. "
        "Air menggerakkan turbin, turbin memutar generator, dan generator tersebut menghasilkan listrik."
    )
    st.info(
        "Lokasi wisata ini bersifat edukatif karena pengunjung dapat menikmati alam sambil belajar secara langsung bagaimana energi terbarukan bekerja."
    )
    

# Page 3 & 4: Quiz In Progress & Quiz Finished
elif page_selection == "🧠 Kuis Interaktif":
    
    # HALAMAN PERSIAPAN: Sebelum kuis dimulai
    if not st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.title("🧠 Siap Menguji Pengetahuan Anda?")
        st.write("Anda akan mengerjakan kuis untuk mendapatkan poin dan lencana.")
        
        st.warning("🚨 **Perhatian:** Begitu kuis dimulai, menu navigasi akan dikunci. Anda tidak dapat kembali ke halaman Chatbot atau Materi hingga kuis selesai (Pencegahan Mencontek).")
        
        if st.button("🚀 Mulai Kuis Sekarang!", type="primary"):
            st.session_state.quiz_started = True
            st.rerun()

    # Page 3: Quiz In Progress
    elif st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.title("🧠 Mengerjakan Kuis...")
        st.divider()
        
        current_idx = st.session_state.quiz_index
        if current_idx < len(quiz_items):
            q = quiz_items[current_idx]
            st.subheader(f"Pertanyaan {current_idx + 1} dari {len(quiz_items)}")
            st.write(f"**{q['question']}**")

            choice = st.radio(
                "Pilih jawaban yang menurut Anda paling tepat:",
                q["options"],
                key=f"quiz_choice_{current_idx}",
                index=None,
            )

            if st.button("Simpan Jawaban", type="primary"):
                if choice is None:
                    st.warning("Harap pilih jawaban sebelum menyimpan.")
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
                        st.success("Tepat Sekali! +20 poin 🎯")
                    else:
                        st.error(f"Sayang sekali, jawaban yang benar adalah: {correct_option}")
                    
                    st.info(f"**Penjelasan:** {q['explanation']}")

                    st.session_state.quiz_index += 1
                    if st.session_state.quiz_index >= len(quiz_items):
                        st.session_state.quiz_finished = True
                    st.rerun()
        else:
            st.session_state.quiz_finished = True
            st.rerun()

    # Page 4: Quiz Finished
    elif st.session_state.quiz_finished:
        st.title("🎉 Terima Kasih Telah Berpartisipasi!")
        st.balloons()
        
        st.write("Anda telah menyelesaikan semua pertanyaan kuis dan menu navigasi telah dibuka kembali.")
        
        result_container = st.container(border=True)
        with result_container:
            st.subheader("Ringkasan Hasil Kuis Anda")
            st.write(f"Jawaban Benar : **{st.session_state.quiz_score} dari {len(quiz_items)}**")
            st.write(f"Total Poin Akhir : **{st.session_state.points} Poin**")
            st.write(f"Pencapaian Lencana : **{get_badge(st.session_state.points)}**")
            
        st.write("")
        if st.button("🔄 Kerjakan Ulang Kuis", type="secondary"):
            st.session_state.quiz_index = 0
            st.session_state.quiz_answered_ids = set()
            st.session_state.quiz_score = 0
            st.session_state.quiz_finished = False
            st.session_state.quiz_started = False # Remove quiz lock to allow retaking
            st.rerun()