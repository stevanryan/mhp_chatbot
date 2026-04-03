import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman Admin
st.set_page_config(
    page_title="Dasbor Admin - Edu-Wisata",
    layout="wide"
)

st.title("Dasbor Analisis Log Chatbot")
st.markdown("Halaman ini khusus untuk admin meninjau hasil perhitungan algoritma, performa *chatbot*, dan riwayat aktivitas pengguna.")
st.divider()

LOG_PATH = "data/interaction_logs.csv"

# Cek apakah file log sudah ada
if os.path.exists(LOG_PATH):
    # Baca data menggunakan pandas
    df = pd.read_csv(LOG_PATH)
    
    # --- BAGIAN 1: METRIK UTAMA (KPI) ---
    st.subheader("Ringkasan Performa")
    
    # Memisahkan data chat dan kuis
    df_chat = df[df['event_type'] == 'chat']
    df_quiz = df[df['event_type'] == 'quiz']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Interaksi Keseluruhan", len(df))
    with col2:
        st.metric("Total Pertanyaan Chatbot", len(df_chat))
    with col3:
        st.metric("Total Jawaban Kuis", len(df_quiz))
    with col4:
        # Menghitung rata-rata skor kemiripan hanya dari interaksi chat yang valid
        avg_sim = df_chat['similarity_score'].mean() if not df_chat.empty else 0
        st.metric("Rata-rata Kemiripan (TF-IDF)", f"{avg_sim:.4f}")

    st.divider()

    # --- BAGIAN 2: TABEL FILTER AKTIVITAS ---
    st.subheader("Detail Log Interaksi")
    
    # Membuat Tab untuk merapikan tampilan
    tab1, tab2, tab3 = st.tabs(["Log Chatbot (FAQ)", "Log Kuis", "Semua Data Raw"])
    
    with tab1:
        st.write("**Riwayat Pertanyaan Pengunjung & Hasil Hitungan Algoritma:**")
        if not df_chat.empty:
            # FIX: Menggunakan kolom 'extra', lalu mengganti namanya khusus untuk tampilan tabel
            chat_display = df_chat[['timestamp', 'session_id', 'user_query', 'similarity_score', 'extra', 'bot_reply']].copy()
            chat_display.rename(columns={'extra': 'match_type'}, inplace=True)
            
            # Mengurutkan dari yang terbaru
            chat_display = chat_display.sort_values(by='timestamp', ascending=False)
            st.dataframe(chat_display, use_container_width=True)
        else:
            st.info("Belum ada data interaksi chat.")

    with tab2:
        st.write("**Riwayat Pengerjaan Kuis Pengunjung:**")
        if not df_quiz.empty:
            # FIX: Menggunakan kolom 'extra' untuk menampilkan penjelasan kuis
            quiz_display = df_quiz[['timestamp', 'session_id', 'user_query', 'bot_reply', 'total_points', 'badge', 'extra']].copy()
            quiz_display.rename(columns={'extra': 'penjelasan'}, inplace=True)
            
            quiz_display = quiz_display.sort_values(by='timestamp', ascending=False)
            st.dataframe(quiz_display, use_container_width=True)
        else:
            st.info("Belum ada data pengerjaan kuis.")

    with tab3:
        st.write("**Data Mentah (Raw Data) dari File CSV:**")
        st.dataframe(df.sort_values(by='timestamp', ascending=False), use_container_width=True)
        
        # Tombol untuk mengunduh log sebagai Excel/CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Data Log (CSV)",
            data=csv,
            file_name='log_interaksi_eduwisata.csv',
            mime='text/csv',
        )

else:
    st.warning("File log interaksi belum ditemukan. Pastikan pengunjung sudah mencoba mengobrol dengan chatbot atau mengerjakan kuis agar sistem membuat file `interaction_logs.csv`.")