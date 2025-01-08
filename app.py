from flask import *
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Set a secret key for session management
# In production, keep this secret and do not commit it to version control.
app.secret_key = 'YOUR_SECRET_KEY_HERE'

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
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
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        full_name = request.form['name']
        email = request.form['email']
        password_plain = request.form['password']
        gender = request.form['gender']
        bio = request.form.get('biography', '')
        strengths = request.form.get('strengths', '')
        weaknesses = request.form.get('weaknesses', '')

        # Hash the password using bcrypt
        password_hashed = bcrypt.generate_password_hash(password_plain).decode('utf-8')

        # Insert into database
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO user (full_name, email, password, gender, bio, strengths, weaknesses)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (full_name, email, password_hashed, gender, bio, strengths, weaknesses))
            mysql.connection.commit()
        except Exception as e:
            flash('Error: {}'.format(e), 'danger')
            return redirect(url_for('register'))
        finally:
            cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

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


#######################################################################
# RUN
#######################################################################

if __name__ == '__main__':
    # Use host='0.0.0.0' to allow external access on your network
    app.run(debug=True, host='0.0.0.0', port=5000)
