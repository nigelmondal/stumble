from flask import *
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
from psutil import users

app = Flask(__name__)

# Set a secret key for session management
# In production, keep this secret and do not commit it to version control.
app.secret_key = 'YOUR_SECRET_KEY_HERE'

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'cs6191$a'
app.config['MYSQL_DB'] = 'stumble'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dictionaries

mysql = MySQL(app)
bcrypt = Bcrypt(app)

#######################################################################
# ROUTES
#######################################################################

@app.route('/')
def root():
    """Redirect to home or login depending on session."""
    #if 'user_id' in session:
    #    return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user with multi-step fields."""
    if request.method == 'POST':
        # Slab 1: Basic info
        full_name = request.form.get('full_name') or request.form.get('name')  # Match your HTML input name/id
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


@app.route('/home')
def home():
    """Home page: only accessible if logged in."""
    if 'user_id' not in session:
        flash('Please log in to access your home page.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    print(user)
    cur.close()

    return render_template('home.html', user=user)


@app.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_strength', methods=['POST'])
def add_strength():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    new_strength = request.form.get('newStrength')
    user_id = session['user_id']

    # Append the new strength to the existing list
    cur = mysql.connection.cursor()
    cur.execute("SELECT strengths FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if row and new_strength:
        old_strengths = row['strengths'] or ''
        updated_strengths = (old_strengths + ',' + new_strength).strip(',')  # handle edge cases
        cur.execute("UPDATE user SET strengths=%s WHERE user_id=%s", (updated_strengths, user_id))
        mysql.connection.commit()
    cur.close()

    return redirect(url_for('home'))


@app.route('/add_weakness', methods=['POST'])
def add_weakness():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    new_weakness = request.form.get('newWeakness')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT weaknesses FROM user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if row and new_weakness:
        old_weaknesses = row['weaknesses'] or ''
        updated_weaknesses = (old_weaknesses + ',' + new_weakness).strip(',')
        cur.execute("UPDATE user SET weaknesses=%s WHERE user_id=%s", (updated_weaknesses, user_id))
        mysql.connection.commit()
    cur.close()

    return redirect(url_for('home'))

@app.route('/update_bio', methods=['POST'])
def update_bio():
    new_bio = request.form['bio']

    # Update the user's bio in the database
    users['bio'] = new_bio
    mysql.session.commit()
    return redirect(url_for('home'))

@app.route("/get_recommendations")
def get_recommendations():
    """Fetch top 3 recommended profiles based on user strengths and weaknesses from the database."""
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user_id"]

    # Fetch the current user's strengths and weaknesses
    cur = mysql.connection.cursor()
    cur.execute("SELECT strengths, weaknesses FROM user WHERE user_id = %s", (user_id,))
    user_data = cur.fetchone()
    
    if not user_data:
        return jsonify([])  # No user data found

    user_strengths = user_data['strengths'].split(",") if user_data['strengths'] else []
    user_weaknesses = user_data['weaknesses'].split(",") if user_data['weaknesses'] else []

    # Fetch other users
    query = """
        SELECT user_id, full_name, age, bio, strengths, weaknesses, collab_count 
        FROM user 
        WHERE user_id != %s
    """
    cur.execute(query, (user_id,))
    all_profiles = cur.fetchall()
    
    cur.close()

    # Calculate match score and sort profiles
    profiles = []
    for profile in all_profiles:
        profile_strengths = profile['strengths'].split(",") if profile['strengths'] else []
        profile_weaknesses = profile['weaknesses'].split(",") if profile['weaknesses'] else []
        match_score = len(set(user_strengths) & set(profile_strengths)) + len(set(user_weaknesses) & set(profile_weaknesses))
        
        profiles.append({
            "id": profile['user_id'],
            "name": profile['full_name'],
            "age": profile['age'],
            "bio": profile['bio'],
            "match_score": match_score,
            "collab_count": profile['collab_count'],
        })
    
    # Sort by highest match score, then by collaboration count, and take top 3
    profiles = sorted(profiles, key=lambda x: (x["match_score"], x["collab_count"]), reverse=True)[:3]

    print(profiles)
    return jsonify(profiles)

@app.route("/api/foryou")
def api_foryou():
    """Fetch top 3 recommended profiles based on user strengths and weaknesses from the database."""
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user_id"]

    # Fetch the current user's strengths and weaknesses
    cur = mysql.connection.cursor()
    cur.execute("SELECT strengths, weaknesses FROM user WHERE user_id = %s", (user_id,))
    user_data = cur.fetchone()
    
    if not user_data:
        return jsonify([])  # No user data found

    user_strengths = user_data['strengths'].split(",") if user_data['strengths'] else []
    user_weaknesses = user_data['weaknesses'].split(",") if user_data['weaknesses'] else []

    # Fetch other users
    query = """
        SELECT user_id, full_name, age, bio, strengths, weaknesses, collab_count 
        FROM user 
        WHERE user_id != %s
    """
    cur.execute(query, (user_id,))
    all_profiles = cur.fetchall()
    
    cur.close()

    # Calculate match score and sort profiles
    profiles = []
    for profile in all_profiles:
        profile_strengths = profile['strengths'].split(",") if profile['strengths'] else []
        profile_weaknesses = profile['weaknesses'].split(",") if profile['weaknesses'] else []
        match_score = len(set(user_strengths) & set(profile_strengths)) + len(set(user_weaknesses) & set(profile_weaknesses))
        
        profiles.append({
            "id": profile['user_id'],
            "name": profile['full_name'],
            "age": profile['age'],
            "bio": profile['bio'],
            "match_score": match_score,
            "collab_count": profile['collab_count']
        })
    
    # Sort by highest match score, then by collaboration count, and take top 3
    profiles = sorted(profiles, key=lambda x: (x["match_score"], x["collab_count"]), reverse=True)[:3]

    return jsonify(profiles)


@app.route('/get_meetings')
def get_meetings():
    """Return all scheduled meetings for the current user."""
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT m.meeting_id, m.meeting_date, m.meeting_time, m.description, 
                   u.full_name AS buddy_name
            FROM meetings m
            JOIN user u ON m.buddy_id = u.user_id
            WHERE YEAR(m.meeting_date) = %s AND MONTH(m.meeting_date) = %s AND m.user_id = %s
            ORDER BY m.meeting_date, m.meeting_time
        """, (year, month, user_id))

        meetings = cur.fetchall()
        cur.close()

        meetings_dict = {}
        for meeting in meetings:
            date_key = meeting["meeting_date"].strftime("%Y-%m-%d")

            # ✅ FIX: Convert timedelta to string if necessary
            meeting_time = meeting["meeting_time"]
            if isinstance(meeting_time, timedelta):
                meeting_time = (datetime.min + meeting_time).time().strftime("%H:%M")
            else:
                meeting_time = meeting_time.strftime("%H:%M")

            if date_key not in meetings_dict:
                meetings_dict[date_key] = []

            meetings_dict[date_key].append({
                "meeting_id": meeting["meeting_id"],
                "buddy": meeting["buddy_name"],
                "time": meeting_time,
                "description": meeting["description"]
            })

        return jsonify(meetings_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return JSON on errors


@app.route('/add_meeting', methods=['POST'])
def add_meeting():
    """Insert a new meeting into the database."""
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



@app.route("/foryou")
def foryou_page():
    return render_template("foryou.html")

# Route for 'Chat' Page
@app.route('/chat')
def chat():
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
        cursor.execute("INSERT INTO chats (sender_id, receiver_id, message) VALUES (%s, %s, %s)", 
                       (sender_id, receiver_id, message))
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
        "SELECT sender_id, receiver_id, message, sent_at FROM chats "
        "WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) "
        "ORDER BY sent_at ASC",
        (sender_id, receiver_id, receiver_id, sender_id)
    )
    messages = cursor.fetchall()
    cursor.close()
    return jsonify(messages)


# Route for 'Calendar' Page
@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, full_name FROM user WHERE user_id != %s", (user_id,))
    buddies = cur.fetchall()
    cur.close()

    return render_template("calendar.html", buddies=buddies)



#######################################################################
# RUN
#######################################################################

if __name__ == '__main__':
    # Use host='0.0.0.0' to allow external access on your network
    app.run(debug=True, host='0.0.0.0', port=5000)
