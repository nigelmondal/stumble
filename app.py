from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
import pandas as pd
from sklearn.metrics import jaccard_score
from sklearn.preprocessing import MultiLabelBinarizer
import sqlite3
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY_HERE'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'AppleC30'
app.config['MYSQL_DB'] = 'stumble'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Base directory of project
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Optional: Automatically create folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/send_file', methods=['POST'])
def send_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    receiver_id = request.form['receiver_id']
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Save file message in DB
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO chats (sender_id, receiver_id, message, sent_at)
            VALUES (%s, %s, %s, NOW())
        ''', (session['user_id'], receiver_id, f'File: {filename}'))
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'File sent', 'filename': filename})
    else:
        return jsonify({'error': 'No file uploaded'}), 400

@app.route('/send_voice', methods=['POST'])
def send_voice():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    sender_id = session['user_id']  # ✅ ADD THIS LINE HERE!!
    receiver_id = request.form['receiver_id']
    voice = request.files['audio']

    if voice:
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'voice_{timestamp}_{unique_id}.webm'
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        voice.save(save_path)

        # Insert voice message into the correct table (chats table!)
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO chats (sender_id, receiver_id, message, sent_at)
            VALUES (%s, %s, %s, NOW())
        ''', (sender_id, receiver_id, f'Voice: {filename}'))
        mysql.connection.commit()
        cur.close()

        return jsonify({'filename': filename})

    return jsonify({'error': 'No voice message recorded!'}), 400


@app.route('/')
def root():
    return render_template('index.html')

# ------------------------------
# (2.1) REGISTER
# ------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name') or request.form.get('name')
        email = request.form.get('email')
        password_plain = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        occupation = request.form.get('occupation')
        other_occupation = request.form.get('other_occupation')
        education = request.form.get('education')
        other_education = request.form.get('other_education')

        strengths = request.form.get('strengths', '')
        weaknesses = request.form.get('weaknesses', '')
        bio = request.form.get('bio', '')
        learning_style = request.form.get('learning-style')
        other_learning = request.form.get('other-learning')
        teaching_style = request.form.get('teaching-style')
        other_teaching = request.form.get('other-teaching')

        # Password match check
        if password_plain != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        # Handle "Other" occupation
        if occupation == 'Other' and other_occupation:
            occupation = other_occupation

        # Handle "Other" education
        if education == 'Other' and other_education:
            education = other_education

        # Handle "Other" learning style
        if learning_style == 'Other' and other_learning:
            learning_style = other_learning

        # Handle "Other" teaching style
        if teaching_style == 'Other' and other_teaching:
            teaching_style = other_teaching

        # Convert DOB
        date_of_birth = None
        if dob_str:
            try:
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('register'))

        # Hash password
        password_hashed = bcrypt.generate_password_hash(password_plain).decode('utf-8')

        # Insert into DB
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO user (
                    full_name, email, password, gender,
                    date_of_birth, occupation, highest_education, bio,
                    strengths, weaknesses, learning_style, teaching_style
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                full_name,
                email,
                password_hashed,
                gender,
                date_of_birth,
                occupation,
                education,
                bio,
                strengths,
                weaknesses,
                learning_style,
                teaching_style
            ))
            mysql.connection.commit()
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            cur.close()
            return redirect(url_for('register'))
        finally:
            cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ------------------------------
# (2.2) LOGIN
# ------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_plain = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password'], password_plain):
            # Login successful
            session['user_id'] = user['user_id']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email/password combination', 'danger')

    return render_template('login.html')

# ------------------------------
# (2.3) LOGOUT
# ------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ------------------------------
# (2.4) HOME
# ------------------------------
@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in to access your home page.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT *, age FROM user WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('home.html', user=user)

# ------------------------------
# (2.5) EDIT PROFILE (strengths, weaknesses, bio)
# ------------------------------
@app.route('/add_strength', methods=['POST'])
def add_strength():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    new_strength = request.form.get('newStrength')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT strengths FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    
    if row and new_strength:
        old_strengths = row['strengths'] or ''
        updated_strengths = old_strengths + ',' + new_strength if old_strengths else new_strength
        cur.execute("UPDATE user SET strengths=%s WHERE user_id=%s", (updated_strengths, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/delete_strength', methods=['POST'])
def delete_strength():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    strength_to_delete = request.form.get('strengthToDelete')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT strengths FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    
    if row and strength_to_delete:
        strengths_list = row['strengths'].split(',') if row['strengths'] else []
        strengths_list = [s.strip() for s in strengths_list if s.strip() and s.strip() != strength_to_delete.strip()]
        updated_strengths = ",".join(strengths_list)
        cur.execute("UPDATE user SET strengths=%s WHERE user_id=%s", (updated_strengths, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/add_weakness', methods=['POST'])
def add_weakness():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    new_weakness = request.form.get('newWeakness')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT weaknesses FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and new_weakness:
        old_weaknesses = row['weaknesses'] or ''
        updated_weaknesses = old_weaknesses + ',' + new_weakness if old_weaknesses else new_weakness
        cur.execute("UPDATE user SET weaknesses=%s WHERE user_id=%s", (updated_weaknesses, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/delete_weakness', methods=['POST'])
def delete_weakness():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    weakness_to_delete = request.form.get('weaknessToDelete')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT weaknesses FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and weakness_to_delete:
        weaknesses_list = row['weaknesses'].split(',') if row['weaknesses'] else []
        weaknesses_list = [w.strip() for w in weaknesses_list if w.strip() and w.strip() != weakness_to_delete.strip()]
        updated_weaknesses = ",".join(weaknesses_list)
        cur.execute("UPDATE user SET weaknesses=%s WHERE user_id=%s", (updated_weaknesses, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/update_bio', methods=['POST'])
def update_bio():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    new_bio = request.form.get('newBio', '')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE user SET bio=%s WHERE user_id=%s", (new_bio, user_id))
    mysql.connection.commit()
    cur.close()

    flash('Bio updated successfully!', 'success')
    return redirect(url_for('home'))

# ------------------------------
# (2.6) EDIT PROFILE - LEARNING / TEACHING STYLES
# ------------------------------
@app.route('/add_learning_style', methods=['POST'])
def add_learning_style():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    new_style = request.form.get('newLearningStyle')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT learning_style FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and new_style:
        old_styles = row['learning_style'] or ''
        updated_styles = old_styles + ',' + new_style if old_styles else new_style
        cur.execute("UPDATE user SET learning_style=%s WHERE user_id=%s", (updated_styles, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/delete_learning_style', methods=['POST'])
def delete_learning_style():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    style_to_delete = request.form.get('styleToDelete')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT learning_style FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and style_to_delete:
        styles_list = row['learning_style'].split(',') if row['learning_style'] else []
        styles_list = [s.strip() for s in styles_list if s.strip() and s.strip() != style_to_delete.strip()]
        updated_styles = ",".join(styles_list)
        cur.execute("UPDATE user SET learning_style=%s WHERE user_id=%s", (updated_styles, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/add_teaching_style', methods=['POST'])
def add_teaching_style():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    new_style = request.form.get('newTeachingStyle')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT teaching_style FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and new_style:
        old_styles = row['teaching_style'] or ''
        updated_styles = old_styles + ',' + new_style if old_styles else new_style
        cur.execute("UPDATE user SET teaching_style=%s WHERE user_id=%s", (updated_styles, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

@app.route('/delete_teaching_style', methods=['POST'])
def delete_teaching_style():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    style_to_delete = request.form.get('styleToDelete')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT teaching_style FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if row and style_to_delete:
        styles_list = row['teaching_style'].split(',') if row['teaching_style'] else []
        styles_list = [s.strip() for s in styles_list if s.strip() and s.strip() != style_to_delete.strip()]
        updated_styles = ",".join(styles_list)
        cur.execute("UPDATE user SET teaching_style=%s WHERE user_id=%s", (updated_styles, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))

# ------------------------------
# (2.7) FOR YOU PAGE
# ------------------------------
@app.route("/foryou")
def foryou_page():
    return render_template("foryou.html")


# ------------------------------
# (2.8) RECOMMENDATION: /api/foryou
# ------------------------------
@app.route("/api/foryou")
def api_foryou():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user_id"]
    cursor = mysql.connection.cursor()
    
    # 1) Fetch potential users (exclude current user + those already in 'buddies')
    cursor.execute(
        """
        SELECT user_id, full_name, bio, strengths, weaknesses, 
               learning_style, teaching_style
        FROM user
        WHERE user_id != %s
          AND user_id NOT IN (
              SELECT buddy_id 
              FROM buddies 
              WHERE user_id = %s
          )
        """,
        (user_id, user_id)
    )
    users = cursor.fetchall()

    # 2) Fetch current user's data
    cursor.execute(
        """
        SELECT strengths, weaknesses, learning_style, teaching_style 
        FROM user 
        WHERE user_id = %s
        """,
        (user_id,),
    )
    user_data = cursor.fetchone()
    cursor.close()

    if not users or not user_data:
        return jsonify([])  # Return an empty list if no results

    # 3) Convert data to a pandas DataFrame for Jaccard-based matching
    import pandas as pd
    from sklearn.preprocessing import MultiLabelBinarizer
    from sklearn.metrics import jaccard_score

    df = pd.DataFrame(users)
    df.fillna("", inplace=True)  # Replace any None with empty string

    # 4) Build combined feature sets
    # Current user 'features'
    user_strengths  = user_data.get("strengths", "")
    user_weaknesses = user_data.get("weaknesses", "")
    user_learning   = user_data.get("learning_style", "")
    user_teaching   = user_data.get("teaching_style", "")

    # We'll treat "weaknesses + learning" as "what I'm looking for"
    user_features = user_weaknesses + " " + user_learning

    # For other users, we combine "strengths + teaching" as "what they offer"
    df["combined_features"] = df["strengths"] + " " + df["teaching_style"]

    # Turn them into sets for Jaccard scoring
    df["combined_features_set"] = df["combined_features"].apply(
        lambda x: set(x.lower().split())
    )
    user_features_set = set(user_features.lower().split())

    # 5) MultiLabelBinarizer for Jaccard
    mlb = MultiLabelBinarizer()
    mlb.fit(df["combined_features_set"].tolist() + [user_features_set])
    binary_matrix = mlb.transform(df["combined_features_set"])
    user_vector   = mlb.transform([user_features_set])

    # 6) Compute Jaccard match_score
    df["match_score"] = [
        jaccard_score(user_vector[0], binary_matrix[i])
        for i in range(len(df))
    ]

    # 7) Sort by match_score DESC, take top 10
    #    Return the fields you want in the final JSON
    recommendations = (
        df.sort_values(by="match_score", ascending=False)
          .head(10)[
              [
                  "user_id",
                  "full_name",
                  "bio",
                  "strengths",
                  "weaknesses",
                  "learning_style",
                  "teaching_style",
                  "match_score"
              ]
          ]
          .to_dict(orient="records")
    )

    # 8) Return as JSON
    return jsonify(recommendations)


# ------------------------------
# 2.10) CHAT ROUTES
# ------------------------------
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Fetch matched buddies dynamically
    cur.execute('''
        SELECT u.user_id, u.full_name
        FROM buddies b
        JOIN user u ON u.user_id = b.buddy_id
        WHERE b.user_id = %s AND b.matched = 1
    ''', (user_id,))
    buddies = cur.fetchall()

    cur.close()

    return render_template('chat.html', buddies=buddies)


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    sender_id = session['user_id']
    data = request.get_json()
    receiver_id = data['receiver_id']
    message = data['message']

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            INSERT INTO chats (sender_id, receiver_id, message, sent_at)
            VALUES (%s, %s, %s, NOW())
        ''', (sender_id, receiver_id, message))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({'error': str(e)}), 500

    cur.close()
    return jsonify({'status': 'Message sent'})


@app.route('/get_messages/<int:receiver_id>', methods=['GET'])
def get_messages(receiver_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    # Fetch all messages exchanged between sender and receiver (both directions)
    cur.execute('''
        SELECT sender_id, receiver_id, message, sent_at
        FROM chats
        WHERE (sender_id = %s AND receiver_id = %s)
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY sent_at
    ''', (user_id, receiver_id, receiver_id, user_id))
    
    messages = cur.fetchall()
    cur.close()

    return jsonify(messages)

# ------------------------------
# (2.11) CALENDAR
# ------------------------------
@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Only fetch buddies who have matched=TRUE
    cur.execute("""
        SELECT u.user_id, u.full_name
        FROM buddies b
        JOIN user u ON u.user_id = b.buddy_id
        WHERE b.user_id = %s
          AND b.matched = 1
    """, (user_id,))
    buddies = cur.fetchall()
    cur.close()

    return render_template("calendar.html", buddies=buddies)

@app.route('/get_meetings')
def get_meetings():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = session['user_id']

        cur = mysql.connection.cursor()
        query = """
            SELECT 
                m.meeting_id,
                m.meeting_date,
                m.meeting_time,
                m.description,
                CASE 
                    WHEN m.user_id = %s 
                        THEN buddy.full_name
                    ELSE user_.full_name
                END AS buddy_name
            FROM meetings m
            JOIN user user_  ON user_.user_id  = m.user_id
            JOIN user buddy ON buddy.user_id   = m.buddy_id
            WHERE YEAR(m.meeting_date) = %s
              AND MONTH(m.meeting_date) = %s
              AND (%s IN (m.user_id, m.buddy_id))
            ORDER BY m.meeting_date, m.meeting_time
        """
        cur.execute(query, (user_id, year, month, user_id))
        meetings = cur.fetchall()
        cur.close()

        from collections import defaultdict
        meetings_dict = defaultdict(list)
        for mtg in meetings:
            date_key = mtg["meeting_date"].strftime("%Y-%m-%d")
            meeting_time = mtg["meeting_time"].strftime("%H:%M")
            meetings_dict[date_key].append({
                "meeting_id": mtg["meeting_id"],
                "buddy": mtg["buddy_name"],
                "time": meeting_time,
                "description": mtg["description"]
            })

        return jsonify(meetings_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_meeting', methods=['POST'])
def add_meeting():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    user_id = session['user_id']
    buddy_id = data["buddy_id"]
    meeting_date = data["date"]
    meeting_time = data["time"]
    description = data["description"]

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO meetings (user_id, buddy_id, meeting_date, meeting_time, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, buddy_id, meeting_date, meeting_time, description))
    mysql.connection.commit()
    cur.close()

    return jsonify({"status": "success"})

@app.route('/delete_meeting', methods=['POST'])
def delete_meeting():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    meeting_id = data["meeting_id"]
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM meetings WHERE meeting_id = %s AND user_id = %s", (meeting_id, user_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({"status": "success"})

@app.route('/requests')
def requests_page():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.user_id AS liker_id, u.full_name, u.bio, u.strengths, u.weaknesses
        FROM buddies b
        JOIN user u ON b.user_id = u.user_id
        WHERE b.buddy_id = %s
          AND b.liked = 1
          AND b.matched = 0
    """, (user_id,))
    pending_requests = cur.fetchall()
    cur.close()

    return render_template('requests.html', requests=pending_requests)



@app.route('/api/requests', methods=['POST'])
def handle_requests():
    """
    Accept or reject a request from someone who 'liked' me.
    If accepted => we create (or update) user->buddy record as liked=1, 
       then check if the buddy->user record also has liked=1 => matched=1 for both.
    If rejected => we can simply remove or set liked=0 for the existing buddy->me record
       (or keep a record from me->buddy with liked=0 so it won't reappear).
    """
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    liker_id = data.get('liker_id')   # The one who liked me
    accepted = data.get('accepted')   # Boolean (True=accept, False=reject)
    user_id = session['user_id']      # me

    if liker_id is None or accepted is None:
        return jsonify({"error": "liker_id and accepted are required"}), 400

    cur = mysql.connection.cursor()

    try:
        if accepted:
            # 1) Mark that I like them back
            cur.execute("""
                INSERT INTO buddies (user_id, buddy_id, liked, matched)
                VALUES (%s, %s, %s, FALSE)
                ON DUPLICATE KEY UPDATE 
                    liked = VALUES(liked)
            """, (user_id, liker_id, True))

            # 2) Check if they already liked me => we can set matched=1 for both
            cur.execute("""
                SELECT liked 
                FROM buddies
                WHERE user_id = %s AND buddy_id = %s
            """, (liker_id, user_id))
            buddy_record = cur.fetchone()

            if buddy_record and buddy_record['liked'] == 1:
                # It's a match => update both rows
                cur.execute("""
                    UPDATE buddies
                    SET matched = TRUE
                    WHERE (user_id = %s AND buddy_id = %s)
                       OR (user_id = %s AND buddy_id = %s)
                """, (user_id, liker_id, liker_id, user_id))

            mysql.connection.commit()
            cur.close()
            return jsonify({"status": "success", "message": "Request accepted, potential match made."})

        else:
            # Rejection path
            # Option A: Just remove their 'like' row so it won't appear again
            cur.execute("""
                DELETE FROM buddies
                WHERE user_id = %s
                  AND buddy_id = %s
                  AND matched = 0
            """, (liker_id, user_id))

            # Option B: Or we can create a row from me->them with liked=0 
            # to note I've refused them. (Optional, depending on your logic)
            # cur.execute("""
            #   INSERT INTO buddies (user_id, buddy_id, liked, matched)
            #   VALUES (%s, %s, FALSE, FALSE)
            #   ON DUPLICATE KEY UPDATE liked=FALSE, matched=FALSE
            # """, (user_id, liker_id))

            mysql.connection.commit()
            cur.close()
            return jsonify({"status": "success", "message": "Request rejected (deleted)."})
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({"error": str(e)}), 500


# ------------------------------
# RUN APP
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
