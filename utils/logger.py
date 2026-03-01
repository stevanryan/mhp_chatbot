import csv
import os
from datetime import datetime


def log_interaction(
    filepath: str,
    session_id: str,
    event_type: str,
    user_query: str = "",
    matched_id: str = "",
    similarity_score: float = 0.0,
    bot_reply: str = "",
    total_points: int = 0,
    badge: str = "",
    extra: str = "",
):
    file_exists = os.path.isfile(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "session_id",
                    "event_type",
                    "user_query",
                    "matched_id",
                    "similarity_score",
                    "bot_reply",
                    "total_points",
                    "badge",
                    "extra",
                ]
            )
        writer.writerow(
            [
                datetime.now().isoformat(),
                session_id,
                event_type,
                user_query,
                matched_id,
                similarity_score,
                bot_reply,
                total_points,
                badge,
                extra,
            ]
        )
