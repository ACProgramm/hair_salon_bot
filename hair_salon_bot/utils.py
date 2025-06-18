import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

def load_intents(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)['intents']

def load_dialogues(path):
    with open(path, encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    return list(zip(lines[::2], lines[1::2]))

def get_best_match(user_input, dialogues):
    user_input = user_input.lower().strip()
    best_score = 0
    best_answer = "Извините, я не знаю ответа на этот вопрос."

    for question, answer in dialogues:
        question = question.lower().strip()
        score = SequenceMatcher(None, user_input, question).ratio()
        if score > best_score:
            best_score = score
            best_answer = answer

    if best_score > 0.4:
        return best_answer
    return "Уточните, пожалуйста. Я пока плохо разбираюсь в этом."
