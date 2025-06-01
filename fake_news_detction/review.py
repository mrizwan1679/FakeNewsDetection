from flask import Blueprint, render_template, request, redirect, session, url_for
import pyodbc

# Create a blueprint for reviews
reviews_bp = Blueprint('reviews', __name__)

# Route to handle the submission of reviews
@reviews_bp.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    if 'user' not in session or 'email' not in session['user']:
        return redirect(url_for('login'))  # Still protect the route

    if request.method == 'POST':
        user_email = session['user']['email']  # Get email from nested dict
        content = request.form.get('review_text')

        if content:
            conn = pyodbc.connect(  "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:goldb.database.windows.net,1433;"
        "DATABASE=FakeNewsdb;"
        "UID=Rizi;"
        "PWD=Rizw@n123.;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Reviews (user_email, content, created_at, is_verified) VALUES (?, ?, GETDATE(), 0)",
                (user_email, content)
            )
            conn.commit()
            conn.close()

    return render_template('reviews.html')






