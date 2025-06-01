from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import pyodbc

admin_bp = Blueprint('admin', __name__)

# Database connection function (Azure SQL)
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=tcp:goldb.database.windows.net,1433;'
        'DATABASE=FakeNewsdb;'
        'UID=Rizi;'
        'PWD=Rizw@n123.;'
        'Encrypt=yes;'
        'TrustServerCertificate=no;'
        'Connection Timeout=30;'
    )
    return conn

@admin_bp.route('/admin-login', methods=['POST'])
def admin_login_route():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        action = data.get('action')

        conn = get_db_connection()
        cursor = conn.cursor()

        if action == 'login':
            cursor.execute("SELECT ID, Username FROM Admins WHERE Username = ? AND Password = ?", (username, password))
            admin = cursor.fetchone()
            conn.close()
            if admin:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                session['admin_id'] = admin[0]
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "fail"})

        elif action == 'register':
            try:
                cursor.execute("INSERT INTO Admins (Username, Password) VALUES (?, ?)", (username, password))
                conn.commit()
                conn.close()
                return jsonify({"status": "success"})
            except pyodbc.IntegrityError:
                conn.close()
                return jsonify({"status": "fail", "message": "Username already exists"})

        return jsonify({"status": "fail", "message": "Invalid action"})

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)})

@admin_bp.route('/admin-dashboard')
def admin_user_summary():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, registration_date, is_active
        FROM Usersmanagement
        ORDER BY registration_date DESC
    """)

    users = []
    for row in cursor.fetchall():
        users.append({
            'id': row[0],
            'email': row[1],
            'registration_date': row[2],
            'is_active': row[3]
        })

    conn.close()
    return render_template('admin-dashboard.html', users=users, username=session['admin_username'])

# Reusable function to submit headlines
def submit_news_category(category, headline, admin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Headlines (headline, category, admin_id) VALUES (?, ?, ?)",
        (headline, category, admin_id)
    )
    conn.commit()
    conn.close()

@admin_bp.route('/admin/submit-gold-news', methods=['POST'])
def submit_gold_news():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    submit_news_category('Gold', request.form.get('headline'), session.get('admin_id'))
    return redirect(url_for('admin.admin_user_summary'))


@admin_bp.route('/admin/submit-sports-news', methods=['POST'])
def submit_sports_news():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    submit_news_category('Sports', request.form.get('headline'), session.get('admin_id'))
    return redirect(url_for('admin.admin_user_summary'))

@admin_bp.route('/admin/submit-politics-news', methods=['POST'])
def submit_politics_news():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    submit_news_category('Politics', request.form.get('headline'), session.get('admin_id'))
    return redirect(url_for('admin.admin_user_summary'))

@admin_bp.route('/admin/submit-environment-news', methods=['POST'])
def submit_environment_news():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    submit_news_category('Environment', request.form.get('headline'), session.get('admin_id'))
    return redirect(url_for('admin.admin_user_summary'))

@admin_bp.route('/admin/reviews')
def admin_reviews():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_email, content, created_at
        FROM Reviews
        WHERE is_verified = 0
        ORDER BY created_at DESC
    """)
    reviews = cursor.fetchall()
    conn.close()
    return render_template('admin-reviewsverification.html', reviews=reviews)

@admin_bp.route('/admin/review/verify/<int:review_id>', methods=['POST'])
def verify_review(review_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    admin_id = session.get('admin_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Reviews
        SET is_verified = 1, verified_by_admin_id = ?
        WHERE id = ?
    """, (admin_id, review_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_reviews'))

@admin_bp.route('/admin/review/delete/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_reviews'))

@admin_bp.route('/admin-logout', methods=['GET'])
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('login'))
