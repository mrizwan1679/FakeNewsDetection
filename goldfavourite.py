from flask import Blueprint, request, jsonify
from flask import session
import pyodbc
import uuid


goldfavourite_bp = Blueprint('sportfavourite', __name__)

# SQL Server connection setup
conn = pyodbc.connect(
      "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:goldb.database.windows.net,1433;"
        "DATABASE=FakeNewsdb;"
        "UID=Rizi;"
        "PWD=Rizw@n123.;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
)
cursor = conn.cursor()



@goldfavourite_bp.route('/save-favorite', methods=['POST'])
def save_favorite():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    article_id = data.get('article_id') or str(uuid.uuid4())
    title = data['title']
    description = data['description']
    url = data.get('url')
    image_url = data.get('image_url')
    published_at = data.get('published_at')
    user_email = session['user']['email']
    category = data.get('category', 'Gold')  # Default to 'General'

    cursor.execute("""
    INSERT INTO Favorites (UserEmail, ArticleID, Title, Description, Url, ImageUrl, PublishedAt, Category)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (user_email, article_id, title, description, url, image_url, published_at, category))

    conn.commit()

    return jsonify({"message": "Favorite saved!", "article_id": article_id}), 200


@goldfavourite_bp.route('/get-news', methods=['GET'])
def get_news():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_email = session['user']['email']
    category = request.args.get('category')

    cursor.execute("""
    SELECT ArticleID, Title, Description, Url, ImageUrl, PublishedAt
    FROM Favorites
    WHERE UserEmail = ? AND LOWER(Category) = LOWER(?)
""", (user_email, category))

    news = cursor.fetchall()

    results = []
    for row in news:
        results.append({
            "article_id": row.ArticleID,
            "title": row.Title,
            "description": row.Description,
            "url": row.Url,
            "image_url": row.ImageUrl,  # New: Include image URL
            "published_at": row.PublishedAt,  # New: Include published date
            "category": category 
        })

    return jsonify(results), 200



@goldfavourite_bp.route('/delete-favorite', methods=['POST'])
def delete_favorite():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    article_id = data.get('article_id')
    category = data.get('category', 'Gold')  # Default to 'Gold' if not provided
    user_email = session['user']['email']

    if not article_id:
        return jsonify({"error": "Missing article_id"}), 400

    # Delete only if the article belongs to the current user and category
    cursor.execute("""
        DELETE FROM Favorites 
        WHERE ArticleID = ? AND UserEmail = ? AND Category = ?
    """, (article_id, user_email, category))

    rows_deleted = cursor.rowcount
    conn.commit()

    if rows_deleted > 0:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Favorite not found."}), 404
