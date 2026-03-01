import json


def load_faq_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_quiz_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
