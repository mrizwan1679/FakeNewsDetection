from flask import Blueprint, jsonify, request, session
import pyodbc
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
cursor = conn.cursor()  # adjust if needed

favorites_bp = Blueprint('favorites_bp', __name__)

@favorites_bp.route('/get-favorites', methods=['GET'])
def get_all_favorites():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_email = session['user']['email']

    cursor.execute("""
        SELECT ArticleID, Title, Description, Url, ImageUrl, PublishedAt, Category
        FROM Favorites
        WHERE UserEmail = ?
    """, (user_email,))

    favorites = cursor.fetchall()
    results = [{
        "article_id": row.ArticleID,
        "title": row.Title,
        "description": row.Description,
        "url": row.Url,
        "image_url": row.ImageUrl,
        "published_at": row.PublishedAt,
        "category": row.Category
    } for row in favorites]

    return jsonify(results), 200


@favorites_bp.route('/delete-favorite', methods=['POST'])
def delete_favorite():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    article_id = data.get('article_id')
    category = data.get('category')
    user_email = session['user']['email']

    if not article_id or not category:
        return jsonify({"error": "Missing data"}), 400

    cursor.execute("""
        DELETE FROM Favorites
        WHERE ArticleID = ? AND UserEmail = ? AND Category = ?
    """, (article_id, user_email, category))

    conn.commit()
    if cursor.rowcount > 0:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Favorite not found"}), 404
