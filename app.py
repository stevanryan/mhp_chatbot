import streamlit as st
import pandas as pd
import base64
import random # Ditambahkan untuk mengacak kuis

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

# initialize additional state variables for quiz management
if "quiz_pool" not in st.session_state:
    st.session_state.quiz_pool = random.sample(quiz_items, min(10, len(quiz_items)))
if "quiz_round" not in st.session_state:
    st.session_state.quiz_round = 1

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
    
    PAGE_MAP = {
        "chatbot": "💬 Chatbot Utama",
        "belajar": "📖 Ruang Belajar",
        "kuis": "🧠 Kuis Interaktif"
    }
    INV_PAGE_MAP = {v: k for k, v in PAGE_MAP.items()}
    
    if "current_page" not in st.session_state:
        url_page = st.query_params.get("page", "chatbot") 
        st.session_state.current_page = PAGE_MAP.get(url_page, "💬 Chatbot Utama")
    
    def change_page(page_name):
        st.session_state.current_page = page_name
        st.query_params["page"] = INV_PAGE_MAP[page_name]
    # --------------------------------------------------------
    
    if st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.error("🔒 Ujian Berlangsung: Navigasi Terkunci")
        change_page("🧠 Kuis Interaktif")
        # Tombol statis (terkunci)
        st.button("🧠 Kuis Interaktif", use_container_width=True, type="primary")
        
    else:
        # check whether quiz just finished OR there's an instruction to stay on quiz page
        if st.session_state.quiz_finished or st.session_state.get("keep_quiz_page", False):
            change_page("🧠 Kuis Interaktif")
            if "keep_quiz_page" in st.session_state:
                del st.session_state["keep_quiz_page"]
        
        # Buat Navigasi dengan Tombol
        if st.button("💬 Chatbot Utama", use_container_width=True, type="primary" if st.session_state.current_page == "💬 Chatbot Utama" else "secondary"):
            change_page("💬 Chatbot Utama")
            st.rerun()
            
        if st.button("📖 Ruang Belajar", use_container_width=True, type="primary" if st.session_state.current_page == "📖 Ruang Belajar" else "secondary"):
            change_page("📖 Ruang Belajar")
            st.rerun()
            
        if st.button("🧠 Kuis Interaktif", use_container_width=True, type="primary" if st.session_state.current_page == "🧠 Kuis Interaktif" else "secondary"):
            change_page("🧠 Kuis Interaktif")
            st.rerun()

    page_selection = st.session_state.current_page
    
    st.divider()
    
    st.subheader("Status Anda")
    st.metric("Lencana", get_badge(st.session_state.points))
    st.metric("Total Poin", st.session_state.points)
    
    # only show quiz progress if quiz is in progress
    if st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.write(f"**🔢 Progres Kuis:** {st.session_state.quiz_index}/10 (Level {st.session_state.quiz_round})")
    
    st.divider()
    
    # Reset session button
    # if st.button("Mulai Ulang Sesi", use_container_width=True):
    #     reset_chat_and_game()
    #     st.session_state.quiz_started = False 
    #     st.session_state.quiz_pool = random.sample(quiz_items, min(10, len(quiz_items)))
    #     st.session_state.quiz_round = 1
        
    #     # Panggil fungsi helper agar URL juga ikut ter-reset!
    #     change_page("💬 Chatbot Utama") 
        
    #     st.session_state.messages = [
    #         {
    #             "role": "assistant",
    #             "content": "Sesi telah dimulai ulang. Tanyakan sesuatu tentang lokasi wisata atau PLTMH kepada saya.",
    #         }
    #     ]
    #     st.rerun()

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
    st.title("Ruang Belajar PLTMH")
    st.write("Selamat datang di pusat materi Edu-Wisata. Silakan pelajari informasi di bawah ini sebelum menguji pengetahuan Anda di halaman Kuis!")
    st.divider()
    
    st.header("Mengenal Kincir Air & Energi Terbarukan di Tegal Balong")
    
    img_kincir_path = "img/kincir_tukbulus.jpeg"
    try:
        kincir_base64 = get_base64_of_bin_file(img_kincir_path)
        
        img_html = f"""
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <img src="data:image/jpeg;base64,{kincir_base64}" 
                 style="width: 600px; max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        </div>
        <p style="text-align: center; color: #666; font-style: italic; font-size: 0.9em; margin-bottom: 20px;">
            Kincir Air PLTMH Tuk Bulus
        </p>
        """
        st.markdown(img_html, unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("⚠️ Gambar kincir_tukbulus.jpeg tidak ditemukan. Pastikan file sudah ada di dalam folder 'img/'.")
    # ----------------------------------------------
    
    st.markdown("""
    ### Pesona Tuk Bulus dan Edu-Wisata
    Dusun Tegal Balong di Desa Bimomartani memiliki potensi alam yang luar biasa, salah satunya adalah mata air Pancuran Tuk Bulus yang airnya mengalir tak pernah susut sepanjang tahun. Bersama Kelompok Sadar Wisata (Pokdarwis), potensi ini tidak hanya dikembangkan menjadi area kolam pemandian, tetapi juga menjadi pusat Edu-Wisata (Wisata Edukasi) Energi. Di sini, pengunjung dapat bersantai menikmati alam sekaligus belajar bagaimana aliran air dapat dimanfaatkan untuk menghasilkan listrik secara mandiri.

    ### Apa itu Kincir Air dan PLTMH?
    Kincir air yang ada di lokasi ini adalah bagian dari sistem PLTMH (Pembangkit Listrik Tenaga Mikro Hidro). PLTMH adalah sebuah sistem pembangkit listrik berskala kecil yang ramah lingkungan. Berbeda dengan bendungan raksasa yang membutuhkan area yang sangat luas, PLTMH beroperasi dalam skala kecil dan didesain khusus untuk memanfaatkan aliran air lokal (seperti Pancuran Tuk Bulus) untuk menerangi area sekitarnya.
    """)
    
    img_kincir_2 = "img/kincir_tukbulus_2.jpeg"
    img_kincir_3 = "img/kincir_tukbulus_3.jpeg"
    
    try:
        base64_1 = get_base64_of_bin_file(img_kincir_2)
        base64_2 = get_base64_of_bin_file(img_kincir_3)
        
        img_html = f"""
            <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                <div style="text-align: center;">
                    <img src="data:image/jpeg;base64,{base64_1}" style="height: 350px; width: auto; max-width: 100%; object-fit: cover; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                </div>
                <div style="text-align: center;">
                    <img src="data:image/jpeg;base64,{base64_2}" style="height: 350px; width: auto; max-width: 100%; object-fit: cover; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                </div>
            </div>
            <p style="text-align: center; color: #666; font-style: italic; font-size: 0.9em; margin-bottom: 20px;">
                Kincir Air PLTMH Tuk Bulus Pada Saat Malam Hari
            </p>
            """
        st.markdown(img_html, unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("⚠️ Salah satu atau kedua file gambar tidak ditemukan. Pastikan file ada di dalam folder 'img/'.")
    # ----------------------------------------------
    
    st.markdown("""
    ### Bagaimana Cara Kerja Kincir Air (PLTMH)?
    Proses perubahan energi air menjadi energi listrik ini sangat menarik dan melalui beberapa tahapan sederhana:
    * **Aliran Air Menggerakkan Turbin:** Air dari Pancuran Tuk Bulus dialirkan untuk menabrak baling-baling kincir (turbin). Energi dari aliran air ini diubah menjadi energi mekanik putar.
    * **Putaran Turbin Menggerakkan Generator:** Turbin yang berputar tersebut dihubungkan ke sebuah generator.
    * **Menghasilkan Listrik:** Generator inilah yang memegang peran utama untuk mengubah energi mekanik (putaran) menjadi energi listrik yang kemudian bisa digunakan untuk menyalakan lampu di sekitar area wisata.

    ### Faktor Penentu Kekuatan Listrik
    Besar kecilnya listrik yang dihasilkan oleh sistem PLTMH dipengaruhi oleh tiga hal utama:
    * **Debit Air:** Kecepatan dan jumlah volume aliran air.
    * **Head (Tinggi Jatuh Air):** Jarak ketinggian air jatuh sebelum mengenai turbin.
    * **Efisiensi Alat:** Kualitas dari sistem turbin dan generator yang terpasang.

    ### Wisata yang Bertanggung Jawab
    Karena PLTMH sangat bergantung pada alam, pelestarian lingkungan adalah kunci utamanya. Pengunjung diajak untuk turut serta menjaga kebersihan dengan tidak membuang sampah sembarangan di area aliran air, tidak merusak tanaman, dan mematuhi batas aman dari peralatan teknis pembangkit listrik.
    """)


# Page 3 & 4: Quiz In Progress & Quiz Finished
elif page_selection == "🧠 Kuis Interaktif":
    
    # Preparation page: Before quiz starts
    if not st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.title(f"🧠 Siap Menguji Pengetahuan Anda? (Level {st.session_state.quiz_round})")
        st.write("Anda akan mengerjakan 10 soal kuis acak untuk mendapatkan poin dan menaikkan lencana.")
        
        st.warning("🚨 **Perhatian:** Begitu kuis dimulai, menu navigasi akan dikunci. Anda tidak dapat kembali ke halaman Chatbot atau Materi hingga kuis selesai.")
        
        if st.button("🚀 Mulai Kuis Sekarang!", type="primary"):
            st.session_state.quiz_started = True
            st.rerun()

    # Page 3: Quiz In Progress
    elif st.session_state.quiz_started and not st.session_state.quiz_finished:
        st.title(f"🧠 Mengerjakan Kuis Level {st.session_state.quiz_round}")
        st.divider()
        
        current_idx = st.session_state.quiz_index
        if current_idx < len(st.session_state.quiz_pool):
            q = st.session_state.quiz_pool[current_idx]
            st.markdown(f"###### Pertanyaan {current_idx + 1} dari 10")
            st.markdown(f"#### {q['question']}")

            choice = st.radio(
                label="Pilih jawaban",
                options=q["options"],
                key=f"quiz_choice_{st.session_state.quiz_round}_{current_idx}",
                index=None,
                label_visibility="collapsed"
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
                    if st.session_state.quiz_index >= len(st.session_state.quiz_pool):
                        st.session_state.quiz_finished = True
                st.rerun()
        else:
            st.session_state.quiz_finished = True
            st.rerun()

    # Page 4: Quiz Finished
    elif st.session_state.quiz_finished:
        st.title(f"🎉 Level {st.session_state.quiz_round} Selesai!")
        st.balloons()
        
        st.write("Anda telah menyelesaikan 10 pertanyaan kuis")
        
        result_container = st.container(border=True)
        with result_container:
            st.subheader("Ringkasan Hasil Kuis Anda")
            st.write(f"Jawaban Benar : **{st.session_state.quiz_score} dari 10**")
            st.write(f"Total Poin Akhir : **{st.session_state.points} Poin**")
            st.write(f"Pencapaian Lencana : **{get_badge(st.session_state.points)}**")
            
            current_badge = get_badge(st.session_state.points)
            if current_badge in ["Mini Hydropower Ambassador"]:
                st.success("Luar biasa! Anda telah mencapai tingkat lencana tertinggi!")
            
        st.write("")
        if st.button("🔄 Lanjut Level Berikutnya", type="primary"):
            st.session_state.quiz_index = 0
            st.session_state.quiz_answered_ids = set() # Hapus histori jawaban agar bisa dapat poin lagi
            st.session_state.quiz_score = 0
            st.session_state.quiz_finished = False
            st.session_state.quiz_started = False
            st.session_state.quiz_round += 1
            st.session_state.quiz_pool = random.sample(quiz_items, min(10, len(quiz_items)))
            
            # make the sidebar to stay on the quiz page after rerun
            st.session_state.keep_quiz_page = True 
            
            st.rerun()