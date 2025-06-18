import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Load intents
with open(os.path.join('dataset','intents.json'), encoding='utf-8') as f:
    data = json.load(f)['intents']

# Prepare training data
X, y = [], []
for intent, info in data.items():
    for ex in info['examples']:
        X.append(ex)
        y.append(intent)

# Train vectorizer and classifier
vect = TfidfVectorizer(analyzer='char', ngram_range=(2,4))
Xv = vect.fit_transform(X)
clf = LogisticRegression(max_iter=200)
clf.fit(Xv, y)

# Save model
os.makedirs('model', exist_ok=True)
joblib.dump(vect, 'model/vectorizer.pkl')
joblib.dump(clf, 'model/classifier.pkl')

def classify_intent(text):
    vect = joblib.load('model/vectorizer.pkl')
    clf = joblib.load('model/classifier.pkl')
    X = vect.transform([text])
    return clf.predict(X)[0]
