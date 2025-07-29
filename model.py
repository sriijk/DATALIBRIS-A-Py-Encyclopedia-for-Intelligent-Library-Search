import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

data = pd.read_csv('encyclopedia_updated.csv')
X = data['content']
y = data['category']

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression(max_iter=1000))
])

pipeline.fit(X, y)

with open('model.pkl', 'wb') as f:
    pickle.dump(pipeline, f)

print("✅ Model trained and saved as model.pkl")

from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report

# Add evaluation
from sklearn.model_selection import StratifiedKFold

cv = StratifiedKFold(n_splits=3)
scores = cross_val_score(pipeline, X, y, cv=cv)
print(f"✅ Stratified CV accuracy: {scores.mean():.4f}")

# Optionally print detailed classification report on full data
pipeline.fit(X, y)
print(classification_report(y, pipeline.predict(X), zero_division=0))
