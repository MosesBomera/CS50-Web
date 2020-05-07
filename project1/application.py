import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from util import hash_password, verify_password

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.secret_key = 'u893j2wmsldrircsmc5encx'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['POST', 'GET'])
def index():
    """Renders the home page with the login form."""
    # if already logged in
    if 'username' in session:
        username = session['username']
        # check database for the user
        # perhaps check password too for better security
        user_id = db.execute("SELECT id FROM users WHERE username = :username",
                                {'username': username}).fetchone()
        if user_id == None:
            """Redirect to login page."""
            return render_template("index.html")
        else:
            """Redirect to home page."""
            return render_template("home.html")

    # regular login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # retrieve details based on the username
        user = db.execute("SELECT username, password FROM users WHERE username = :username",
                    {'username': username}).fetchone()
        # if user doesn't exist
        if user is None:
            return render_template("index.html", error="Invalid Crendentials")
        else:
            password_check = verify_password(user.password, password)
            if password_check:
                session['username'] = username
                return render_template("home.index")

    # normal page visit, uses GET method
    if request.method == "GET":
        return render_template('index.html')

@app.route("/register")
def register():
    """Allows a new user to register to the website."""
    return render_template("register.html")

@app.route("/home")
def home():
    """The home page on the website with the search functionality."""
    return render_template("home.index")

@app.route("/book/<string:isbn>")
def book():
    """Show book details (including reviews from the Goodreads API)."""
    return render_template("book.html")

@app.route("/api/<string:isbn>")
def api():
    """Handles api requests to the website."""
