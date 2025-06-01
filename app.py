from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google.oauth2 import id_token
from google.auth.transport import requests
import model
from model import fetch_related_news  
import pyodbc

from dotenv import load_dotenv
import os
from Count import fetch_news_count, categories
from gold import get_gold_news  
from gold import get_admin_gold_headlines
from goldfavourite import goldfavourite_bp
from admin import admin_bp,get_db_connection
from gold import headline_bp
from sport import get_sports_news,get_admin_sports_headlines
from sportfavourite import sportfavourite_bp
from politic import get_politics_news,get_admin_politics_headlines
from politicfavorite import politicsfavourite_bp
from environment import get_environment_news,get_admin_environment_headlines
from environmentfavorite import environmentfavourite_bp
from favorites import favorites_bp
from review import reviews_bp

app = Flask(__name__)
app.register_blueprint(goldfavourite_bp,url_prefix='')
app.register_blueprint(admin_bp,url_prefix='')
app.register_blueprint(sportfavourite_bp,url_prefix='')
app.register_blueprint(politicsfavourite_bp,url_prefix='')
app.register_blueprint(environmentfavourite_bp,url_prefix='')
app.register_blueprint(favorites_bp,url_prefix='')
app.register_blueprint(headline_bp, url_prefix='')
app.register_blueprint(reviews_bp,url_prefix='')
for rule in app.url_map.iter_rules():
    print(rule)





load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

@app.route("/")
def home():
    user = session.get('user')  # Check if the user is logged in
    news_articles = []  # Empty list for now, you will fill it with real NewsAPI or database later
    
    # Fetch verified reviews from the database
    conn = pyodbc.connect(  "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:goldb.database.windows.net,1433;"
        "DATABASE=FakeNewsdb;"
        "UID=Rizi;"
        "PWD=Rizw@n123.;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_email, content, created_at
        FROM Reviews
        WHERE is_verified = 1
        ORDER BY created_at DESC
    """)
    reviews = cursor.fetchall()
    conn.close()
    
    # Pass the fetched reviews to the template
    return render_template("index.html", user=user, news_articles=news_articles, reviews=reviews)


@app.route("/dashboard")
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('home'))

    # Fetch dynamic news data
    news_counts = {cat: fetch_news_count(q) for cat, q in categories.items()}

    return render_template("dashboard.html", user=user, news_counts=news_counts)

@app.route("/login")
def login():
    return render_template("googlelogin.html")

# Route for the news prediction dashboard
@app.route("/news")
def news():
    return render_template("board.html",active_page='news')

@app.route("/visualization")
def visualization():    
    # Ensure the paths match the saved images
    return render_template("visualization.html")
    

@app.route('/oauth2callback', methods=['POST'])
def oauth2callback():
    try:
        # Get the token from the frontend
        data = request.get_json()
        token = data.get('credential')
        
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        # Extract user information
        user_name = idinfo.get('name', 'Unknown User')
        user_email = idinfo.get('email')
        
        # Save user info in the session
        session['user'] = {'name': user_name, 'email': user_email}
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT id FROM Usersmanagement WHERE email = ?", (user_email,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # Insert new user
            cursor.execute("""
                INSERT INTO Usersmanagement (email, registration_date, is_active)
                VALUES (?, ?, ?)
            """, (user_email, datetime.now(), 1))
            conn.commit()
        
        # Respond with success and the user's name
        return jsonify({'status': 'success', 'name': user_name})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 400

@app.route("/logout")
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('home'))

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_logged_in' in session:
        return render_template('admin-dashboard.html',username=session['admin_username'])
    else:
        return redirect(url_for('index'))



@app.route("/predict", methods=["POST"])
def predict():
    """
    Handle user input for fake news prediction and fetch real news if it's fake.
    """
    if request.method == "POST":
        # Get news content from form input
        news = request.form.get("news", "").strip()

        if not news:
            return render_template("results.html", error="Please enter a news article to check.")

        # Call prediction function from model.py
        result = model.predict_news(news)  # This function will return a dictionary with predictions

        # Extract prediction results
        prediction_label = result["logistic_regression"]  # Example from one of the models
        bert_confidence = result["bert_confidence"]
        conflict = result["conflict"]

        # If the prediction is fake, try to fetch similar real articles
        articles =fetch_related_news(news) if prediction_label == "Fake News" else []
        
        
        

        # Render result page with the prediction and any real articles
        return render_template(
            "results.html",
            news=news,
            prediction=prediction_label,
            confidence=bert_confidence,
            conflict=conflict,
            articles=articles  # List of real news articles if the prediction is fake
        )

@app.route('/board')
def board():
    return render_template('board.html')



@app.route("/goldnews")
def gold_news():
    try:
        headlines = get_admin_gold_headlines()       
        news_articles = get_gold_news() 
                    

      

        return render_template("gold_news.html", headlines=headlines, news_articles=news_articles, active_page="gold")
    except Exception as e:
        print("Error in gold_news route:", e)
        return "Internal Server Error", 500
    
@app.route("/sportsnews")
def sports_news():
    try:
              # Optional: Admin-submitted sports headlines
        sports_articles = get_sports_news()             # Fetched from NewsAPI or similar source
        headlines = get_admin_sports_headlines()  

        return render_template("sports_news.html",  headlines=headlines, sports_articles=sports_articles, active_page="sports")
    except Exception as e:
        print("Error in sports_news route:", e)
        return "Internal Server Error", 500

@app.route("/politicnews")
def politics_news():
    try:
        articles=get_politics_news()
        headlines=get_admin_politics_headlines()
        return render_template("politic_news.html",headlines=headlines,politics_articles=articles,active_page="politics")
    except Exception as e:
        print("Error in Politics_news route:", e)
        return "Internal Server Error", 500

@app.route("/environmentnews")
def environment_news():
    try:
        articles = get_environment_news()
        headlines=get_admin_environment_headlines()
        return render_template("environment_news.html",headlines=headlines ,environment_articles=articles, active_page="environment")
    except Exception as e:
        print("Error in environment_news route:", e)
        return "Internal Server Error", 500


@app.route("/admin/gold-news-form")
def gold_news_form():
    if 'admin_logged_in' in session:
        return render_template("admin-goldnews.html")
    else:
        return redirect(url_for("login"))
    
@app.route("/admin/sports-news-form")
def sports_news_form():
    if 'admin_logged_in' in session:
        return render_template("admin-sportsnews.html")
    else:
        return redirect(url_for("login"))


@app.route("/admin/politics-news-form")
def politics_news_form():
    if 'admin_logged_in' in session:
        return render_template("admin-politicsnews.html")
    else:
        return redirect(url_for("login"))
    
@app.route("/admin/environment-news-form")
def environment_news_form():
    if 'admin_logged_in' in session:
        return render_template("admin-environmentnews.html")
    else:
        return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
