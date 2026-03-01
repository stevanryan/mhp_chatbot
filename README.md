# MHP Educational Tourism Chatbot

A lightweight FAQ-based educational tourism chatbot for mini hydropower (MHP), built with Streamlit.

## Features
- Chat UI using Streamlit chat elements
- FAQ retrieval using TF-IDF + cosine similarity
- Keyword fallback matching
- Gamification with points, badges, and quiz
- CSV interaction logs

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `app.py` - main app
- `data/faq_data.json` - FAQ dataset
- `data/quiz_data.json` - quiz bank
- `utils/matcher.py` - retrieval engine
- `utils/gamification.py` - points and badges
- `utils/logger.py` - CSV logger

## Notes
- FAQ points are awarded once per matched FAQ ID per session.
- Quiz questions award 20 points per correct answer.
- Logs are written to `data/interaction_logs.csv`.
