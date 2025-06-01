import joblib
import numpy as np,os
import pandas as pd
from scipy.sparse import hstack
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import requests
from dotenv import load_dotenv

# Load pickled models and vectorizer
LR = joblib.load('LR_model.pkl')
PAC = joblib.load('PAC_model.pkl')
ensemble_model = joblib.load('ensemble_model.pkl')
vectorization = joblib.load('vectorizer.pkl')

# Load BERT model and tokenizer
bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Utility functions
def wordopt(text):
    # Clean text (as per your existing preprocessing)
    text = text.lower()
    text = ''.join([char for char in text if char.isalnum() or char.isspace()])
    return text

def polarity_score(text):
    from textblob import TextBlob
    return TextBlob(text).sentiment.polarity

def add_extra_features(text_series):
    excl = text_series.apply(lambda x: x.count('!')).values.reshape(-1, 1)
    upper = text_series.apply(lambda x: sum(1 for c in x if c.isupper())).values.reshape(-1, 1)
    clickbait = text_series.apply(lambda x: int('you won’t believe' in x.lower() or 'shocking' in x.lower())).values.reshape(-1, 1)
    return excl, upper, clickbait

def output_label(label):
    return "Fake News" if label == 0 else "Not A Fake News"

# BERT prediction
def predict_with_bert(news_text):
    inputs = bert_tokenizer(news_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1).numpy()
        label = np.argmax(probs, axis=1)[0]
        confidence = probs[0][label]
    return output_label(label), confidence

# Function to fetch real news based on the input news headline

def extract_keywords(text, top_n=5):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
    X = vectorizer.fit_transform([text])
    indices = X.toarray().argsort()[0][-top_n:]
    features = vectorizer.get_feature_names_out()
    keywords = [features[i] for i in indices[::-1] if i < len(features)]
    return " ".join(keywords)

def fetch_related_news(news_text):
    query = extract_keywords(news_text)
    if not query.strip():
        query = news_text[:100]  # fallback: first 100 characters
    load_dotenv()
    API_KEY = os.getenv("NEWS_API_KEY") 
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={API_KEY}"
    
    response = requests.get(url)
    data = response.json()

    if data.get('status') == 'ok' and data.get('articles'):
        articles = [{
            'title': a['title'],
            'description': a['description'],
            'url': a['url'],
            'publishedAt': a['publishedAt']
        } for a in data['articles'][:5]]
        return articles
    else:
        print("NewsAPI response:", data)  # helpful for debugging
        return []

# Main prediction function
def predict_news(news_text):
    # Prediction Process
    df = pd.DataFrame({'text': [news_text]})
    df['text'] = df['text'].apply(wordopt)

    tfidf_vec = vectorization.transform(df['text'])
    sentiment = df['text'].apply(polarity_score).values.reshape(-1, 1)
    excl, upper, clickbait = add_extra_features(df['text'])

    final_vec = hstack([tfidf_vec, sentiment, excl, upper, clickbait])

    # Traditional models
    pred_lr = LR.predict(final_vec)[0]
    pred_pac = PAC.predict(final_vec)[0]
    pred_ens = ensemble_model.predict(final_vec)[0]

    # BERT prediction
    bert_pred, bert_conf = predict_with_bert(news_text)

    # Fetch related real news articles
    real_news = fetch_related_news(news_text) if output_label(pred_ens) == "Fake News" else []

    return {
        "logistic_regression": output_label(pred_lr),
        "passive_aggressive": output_label(pred_pac),
        "ensemble": output_label(pred_ens),
        "bert": bert_pred,
        "bert_confidence": round(bert_conf * 100, 2),
        "conflict": output_label(pred_ens) != bert_pred,
        "real_news": real_news 
    }
