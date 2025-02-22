from flask import *
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
import pandas as pd
from sklearn.metrics import jaccard_score
from sklearn.preprocessing import MultiLabelBinarizer

app = Flask(__name__)

# -----------------------------------------------------------------------------------
# 1) BASIC CONFIG
# -----------------------------------------------------------------------------------
app.secret_key = 'YOUR_SECRET_KEY_HERE'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'AppleC30'
app.config['MYSQL_DB'] = 'stumble'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dictionaries

mysql = MySQL(app)
bcrypt = Bcrypt(app)

#######################################################################
# ROUTES
#######################################################################

@app.route('/')
def root():
    """Redirect to home or show landing page."""
    # If you want to auto-redirect when logged in:
    # if 'user_id' in session:
    #     return redirect(url_for('home'))
    return render_template('index.html')


# ------------------------------
# 2.1) REGISTER
# ------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user with multi-step fields."""
    if request.method == 'POST':
        # Slab 1: Basic info
        full_name = request.form.get('full_name') or request.form.get('name')
        email = request.form.get('email')
        password_plain = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Slab 2: Personal details
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        occupation = request.form.get('occupation')
        other_occupation = request.form.get('other_occupation')
        education = request.form.get('education')
        other_education = request.form.get('other_education')

        # Slab 3: Skills & preferences
        strengths = request.form.get('strengths', '')
        weaknesses = request.form.get('weaknesses', '')
        bio = request.form.get('bio', '')
        learning_style = request.form.get('learning-style')
        other_learning = request.form.get('other-learning')
        teaching_style = request.form.get('teaching-style')
        other_teaching = request.form.get('other-teaching')

        # 1) Validate passwords match
        if password_plain != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        # 2) Handle "Other" occupation
        if occupation == 'Other' and other_occupation:
            occupation = other_occupation

        # 3) Handle "Other" education
        if education == 'Other' and other_education:
            education = other_education

        # 4) Handle "Other" learning style
        if learning_style == 'Other' and other_learning:
            learning_style = other_learning

        # 5) Handle "Other" teaching style
        if teaching_style == 'Other' and other_teaching:
            teaching_style = other_teaching

        # 6) Convert date_of_birth if provided
        date_of_birth = None
        if dob_str:
            from datetime import datetime
            try:
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('register'))

        # 7) Hash the password
        password_hashed = bcrypt.generate_password_hash(password_plain).decode('utf-8')

        # 8) Insert into database
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

    # If GET request, just render the form template
    return render_template('register.html')


# ------------------------------
# 2.2) LOGIN
# ------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    if request.method == 'POST':
        # Retrieve form data
        email = request.form['email']
        password_plain = request.form['password']

        # Check if user exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Verify password
            if bcrypt.check_password_hash(user['password'], password_plain):
                # Login successful
                session['user_id'] = user['user_id']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid email/password combination', 'danger')
        else:
            flash('Invalid email/password combination', 'danger')

    return render_template('login.html')


# ------------------------------
# 2.3) LOGOUT
# ------------------------------
@app.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ------------------------------
# 2.4) HOME PAGE
# ------------------------------
@app.route('/home')
def home():
    """Render home page with user details."""
    if 'user_id' not in session:
        flash('Please log in to access your home page.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('home.html', user=user)


# ------------------------------
# 2.5) EDIT PROFILE - STRENGTHS / WEAKNESSES / BIO
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


### ADD / DELETE WEAKNESS ###
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


### UPDATE BIO ###
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
# 2.6) EDIT PROFILE - LEARNING / TEACHING STYLES
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
        cur.execute("UPDATE user SET learning_style=%s WHERE user_id=%s", (updated_styles, user_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('home'))


# ------------------------------
# 2.7) FOR YOU PAGE ROUTE
# ------------------------------
@app.route("/foryou")
def foryou_page():
    """Render the foryou.html template."""
    return render_template("foryou.html")


# ------------------------------
# 2.8) RECOMMENDATION /api/foryou
# ------------------------------
@app.route("/api/foryou")
def api_foryou():
    """
    Returns recommended profiles, excluding:
      - the current user
      - anyone already in buddies (like/dislike)
    """
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user_id"]

    # ✅ Fetch all users except the logged-in user
    cursor = mysql.connection.cursor()
    
    # Exclude current user + those already recorded in "buddies"
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

    # Fetch the current user's data
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
        return jsonify([])  # No recommendations

    # Extract user attributes
    user_strengths   = user_data.get("strengths", "")
    user_weaknesses  = user_data.get("weaknesses", "")
    user_learning    = user_data.get("learning_style", "")
    user_teaching    = user_data.get("teaching_style", "")

    # Convert user list to DataFrame
    df = pd.DataFrame(users)
    df.fillna("", inplace=True)

    # Combine the other user's "strengths + teaching_style"
    df["combined_features"] = df["strengths"] + " " + df["teaching_style"]
    # The current user: "weaknesses + learning_style"
    user_features = user_weaknesses + " " + user_learning

    # Convert to sets for Jaccard
    df["combined_features_set"] = df["combined_features"].apply(lambda x: set(x.lower().split()))
    user_features_set = set(user_features.lower().split())

    # One-hot encode for Jaccard
    mlb = MultiLabelBinarizer()
    mlb.fit(df["combined_features_set"].tolist() + [user_features_set])
    binary_matrix = mlb.transform(df["combined_features_set"])
    user_vector   = mlb.transform([user_features_set])

    # Compute Jaccard Score
    df["match_score"] = [
        jaccard_score(user_vector[0], binary_matrix[i]) for i in range(len(df))
    ]

    # Sort descending by match_score, take top 10
    recommendations = (
        df.sort_values(by="match_score", ascending=False)
          .head(10)[["user_id", "full_name", "bio", "match_score"]]
          .to_dict(orient="records")
    )

    return jsonify(recommendations)


# ------------------------------
# 2.9) BUDDIES (Like/Dislike + Matching)
# ------------------------------

@app.route('/api/buddies', methods=['POST'])
def manage_buddy_relationship():
    """
    Inserts or updates a buddy record in the buddies table.
    If a mutual like is detected, sets matched=TRUE in both directions.
    """
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    user_id = session['user_id']
    buddy_id = data.get('buddy_id')
    liked = data.get('liked')

    # Validate the input
    if buddy_id is None or liked is None:
        return jsonify({"error": "buddy_id and liked are required"}), 400

    liked = bool(liked)  # Ensure liked is a boolean

    cur = mysql.connection.cursor()

    try:
        # 1) Insert or update the record for the current user's action
        #    NOTE: We explicitly keep matched = matched on update,
        #    so we don't lose a prior matched=TRUE.
        cur.execute("""
            INSERT INTO buddies (user_id, buddy_id, liked, matched)
            VALUES (%s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE 
                liked = VALUES(liked),
                matched = matched
        """, (user_id, buddy_id, liked))

        match_made = False

        # 2) If the user "liked," check if buddy also liked them
        if liked:
            cur.execute("""
                SELECT liked, matched 
                FROM buddies
                WHERE user_id = %s AND buddy_id = %s
            """, (buddy_id, user_id))
            buddy_record = cur.fetchone()

            # If buddy already liked us => mutual like
            if buddy_record and buddy_record['liked'] == 1:
                match_made = True
                # Set matched=TRUE for both rows
                cur.execute("""
                    UPDATE buddies
                    SET matched = TRUE
                    WHERE (user_id = %s AND buddy_id = %s)
                       OR (user_id = %s AND buddy_id = %s)
                """, (user_id, buddy_id, buddy_id, user_id))

        mysql.connection.commit()
        cur.close()

        return jsonify({"status": "success", "match_made": match_made})

    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({"error": str(e)}), 500


# ------------------------------
# 2.10) CHAT ROUTES
# ------------------------------
@app.route('/chat')
def chat():
    """Render Chat page."""
    return render_template('chat.html')


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    sender_id = session['user_id']
    receiver_id = data.get('receiver_id')
    message = data.get('message')

    if not receiver_id or not message:
        return jsonify({'error': 'Receiver ID and message are required'}), 400

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO chats (sender_id, receiver_id, message) 
            VALUES (%s, %s, %s)
        """, (sender_id, receiver_id, message))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': 'Message sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_messages/<int:receiver_id>', methods=['GET'])
def get_messages(receiver_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    sender_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT sender_id, receiver_id, message, sent_at 
        FROM chats
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY sent_at ASC
        """,
        (sender_id, receiver_id, receiver_id, sender_id)
    )
    messages = cursor.fetchall()
    cursor.close()
    return jsonify(messages)


# ------------------------------
# 2.11) CALENDAR ROUTES
# ------------------------------
@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Only fetch BUDDIES who have 'matched=TRUE' for this user
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
    """Return all scheduled meetings for the current user (by year/month)."""
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = session['user_id']

        cur = mysql.connection.cursor()
        # We join the 'user' table TWICE: 
        #   - user_ for m.user_id
        #   - buddy for m.buddy_id
        # Then pick the correct "buddy_name" based on which side is our user.
        query = """
            SELECT 
                m.meeting_id,
                m.meeting_date,
                m.meeting_time,
                m.description,
                CASE 
                    WHEN m.user_id = %s 
                        THEN buddy.full_name  -- If I'm the user, show buddy's name
                    ELSE user_.full_name   -- If I'm the buddy, show the user's name
                END AS buddy_name
            FROM meetings m
            JOIN user user_  ON user_.user_id  = m.user_id
            JOIN user buddy ON buddy.user_id = m.buddy_id
            WHERE YEAR(m.meeting_date) = %s
              AND MONTH(m.meeting_date) = %s
              AND (%s IN (m.user_id, m.buddy_id))
            ORDER BY m.meeting_date, m.meeting_time
        """
        cur.execute(query, (user_id, year, month, user_id))
        meetings = cur.fetchall()
        cur.close()

        # Group them by date for easy front-end consumption
        # { "YYYY-MM-DD": [ {meeting_id, buddy_name, time, description}, ... ], ... }
        from collections import defaultdict
        meetings_dict = defaultdict(list)

        for mtg in meetings:
            # Convert date/time to strings
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
    """Insert a new meeting."""
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
    """Delete a scheduled meeting."""
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


# -----------------------------------------------------------------------------------
# 3) RUN THE APP
# -----------------------------------------------------------------------------------
if __name__ == '__main__':
    # Use host='0.0.0.0' for external access
    app.run(debug=True, host='0.0.0.0', port=5000)
