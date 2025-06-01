from flask import Blueprint
import requests,pyodbc
import os
from dotenv import load_dotenv


headline_bp = Blueprint('headline', __name__)



load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY") 

def get_politics_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=politics &language=en&apiKey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            news_data = []
            for article in articles:
                news_data.append({
                    "title": article.get("title", "No Title"),
                    "description": article.get("description", "No Description"),
                    "image_url": article.get("urlToImage", ""),
                    "url": article.get("url", "#"),
                    "published_at": article.get("publishedAt", "No Date"),
                    "author": article.get("author", "Unknown"),
                    "source": article.get("source", {}).get("name", "Unknown Source")
                })
            return news_data
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception occurred while fetching politics news: {e}")
        return []

@headline_bp.route('/api/admin-politics-headlines', methods=['GET'])
def get_admin_politics_headlines():
    conn = pyodbc.connect(  "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:goldb.database.windows.net,1433;"
        "DATABASE=FakeNewsdb;"
        "UID=Rizi;"
        "PWD=Rizw@n123.;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;")
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 4 headline FROM Headlines WHERE category = 'Politics' ORDER BY created_at DESC")
    headlines = [row.headline for row in cursor.fetchall()]
    conn.close()
    return headlines
