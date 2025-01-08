from flask import *
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'stumble'

mysql = MySQL(app)

@app.route('/home')
def index():
    return render_template('home.html')

app.run(debug=True, port=5000)