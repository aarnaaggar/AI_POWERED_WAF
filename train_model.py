import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

print("--- Loading Strictly Balanced Dataset ---")
df = pd.read_csv('owasp_data.csv')

# Drop empty rows just in case
df = df.dropna()

X = df['payload']
y = df['label']

print("Vectorizing (TF-IDF Character N-Grams)...")
# Using char N-Grams is crucial for catching tricky syntax
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=10000)
X_vect = vectorizer.fit_transform(X)

print("Training Balanced Random Forest...")
# Split data: 80% for training, 20% for testing
X_train, X_test, y_train, y_test = train_test_split(X_vect, y, test_size=0.2, random_state=42)

# NEW: class_weight='balanced' forces the AI to pay extreme attention to both sides equally
model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

print("\n--- Model Evaluation ---")
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred))

# Save the brain
joblib.dump(model, 'model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')

print("\n✅ AI Engine Updated Successfully!")