import requests
from datetime import date, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY") 
BASE_URL = "https://newsapi.org/v2/everything"

categories = {
    "Gold": "gold price OR gold market",
    "Sports": "sports OR football OR cricket",
    "Politics": "politics OR government OR election",
    "Environment": "climate OR environment OR pollution"
}

def fetch_news_count(keyword):
    today = date.today()
    start_date = today - timedelta(days=2)

    params = {
        'q': keyword,
        'from': start_date.isoformat(),
        'to': today.isoformat(),
        'sortBy': 'publishedAt',
        'language': 'en',
        'pageSize': 100,
        'apiKey': API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if response.status_code == 200:
        return data.get('totalResults', 0)
    else:
        print(f"Error: {data}")
        return 0

if __name__ == "__main__":
    news_counts = {category: fetch_news_count(keyword) for category, keyword in categories.items()}
    print(news_counts)
