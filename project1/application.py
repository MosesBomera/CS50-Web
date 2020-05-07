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
        full_name = session['full_name']
        # check database for the user
        # perhaps check password too for better security
        # full_name = db.execute("SELECT full_name FROM users WHERE username = :username",
        #                         {'username': username}).fetchone()
        # if full_name == None:
        #     """Redirect to login page."""
        #     return render_template("index.html")
        # else:
        """Redirect to home page."""
        return render_template("home.html", full_name=full_name)

    # regular login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # retrieve details based on the username
        user = db.execute("SELECT full_name, username, password FROM users WHERE username = :username",
                    {'username': username}).fetchone()
        # if user doesn't exist
        if user is None:
            return render_template("index.html", error="Invalid Crendentials")
        else:
            password_check = verify_password(user.password, password)
            if password_check:
                session['username'] = user.username
                session['full_name'] = user.full_name
                return render_template("home.html", full_name=user.full_name)

    # normal page visit, uses GET method
    if request.method == "GET":
        return render_template('index.html')

@app.route("/register", methods=["POST", "GET"])
def register():
    """Allows a new user to register to the website."""
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        # get registrants Crendentials
        username = request.form.get("username")
        full_name = request.form.get("full_name")
        password = request.form.get("password")

        # create a hash password
        password = hash_password(password)

        # add user to database
        db.execute("INSERT INTO users (full_name, username, password) VALUES (:full_name, :username, :password)",
                    {"full_name": full_name, "username": username, "password": password})
        db.commit()

        # login into your account
        return render_template('index.html', message="Account Created, Please Login")

@app.route("/home")
def home():
    """The home page on the website with the search functionality."""
    # check if user is logged in, and get full name
    if 'username' not in session:
        return render_template("index.html")

    username = session['username']
    full_name = session['full_name']
    if full_name:
        # if a search
        search_term = request.args.get('search')
        if search_term:
            books = db.execute("SELECT * FROM books WHERE isbn LIKE :search_term or title LIKE :search_term or author LIKE :search_term",
                                        {'search_term': f"%{search_term}%"}).fetchall()
            if books != None:
                return render_template("home.html", full_name=full_name, books=books)
            else:
                error = "Your search did not return any results."
                return render_template("home.html", full_name=full_name, error=error)
        else:
            # regular home page
            return render_template("home.html", full_name=full_name)



@app.route("/book/<string:isbn>")
def book():
    """Show book details (including reviews from the Goodreads API)."""
    return render_template("book.html")

@app.route("/api/<string:isbn>")
def api():
    """Handles api requests to the website."""
