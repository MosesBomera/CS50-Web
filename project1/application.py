import os

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from util import hash_password, verify_password
import requests

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
engine = create_engine(os.getenv("DATABASE_URL"), pool_size=20, max_overflow=0)
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['POST', 'GET'])
def index():
    """Renders the home page with the login form."""
    # if already logged in
    if 'username' in session:
        username = session['username']
        full_name = session['full_name']
        return render_template("home.html", full_name=full_name)

    # regular login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # retrieve details based on the username
        user = db.execute("SELECT id, full_name, username, password FROM users WHERE username = :username",
                    {'username': username}).fetchone()
        # if user doesn't exist
        if user is None:
            return render_template("index.html", error="Invalid Crendentials")
        else:
            password_check = verify_password(user.password, password)
            if password_check:
                session['username'] = user.username
                session['full_name'] = user.full_name
                session['id'] = user.id
                return render_template("home.html", full_name=user.full_name)

    # normal page visit, uses GET method
    if request.method == "GET":
        return render_template('index.html')

@app.route("/logout")
def logout():
    """Allows a user to logout of the website."""

    # remove all credentials associated to the user
    session.pop('username', None)
    session.pop('full_name', None)
    session.pop('id', None)

    return render_template("index.html")

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

@app.route("/book/<string:isbn>", methods=["POST", "GET"])
def book(isbn):
    """Show book details (including reviews from the Goodreads API)."""

    # check if user is logged in
    if 'username' not in session:
        return render_template('index.html')

    # Goodreads api access
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                        params={"key": "ocupx05S7CqcE2wULHregQ", "isbns": isbn})

    GOODREADS = dict()
    if res.status_code == 200:
        GOODREADS["average_rating"] = res.json()["books"][0]["average_rating"]
        GOODREADS["work_ratings_count"] = res.json()["books"][0]["work_ratings_count"]

    prompt = '' # for multiple submissions
    if request.method == "POST":
        user_id = session["id"]
        # bar multiple submissions
        check = db.execute("SELECT review FROM reviews where user_id = :id AND book_isbn =:isbn ",
                            {"id": user_id, "isbn": isbn})
        if check != None:
            prompt = "You have already submitted a review for this book."
        else:
            review = request.form.get("review")
            rating = request.form.get("rating")
            # add review to database
            db.execute("INSERT INTO reviews (review, rating, user_id, book_isbn)" \
                        "VALUES (:review, :rating, :user_id, :isbn)",
                        {"review": review, "rating": rating, "user_id": user_id, "isbn": isbn})
            # commit changes
            db.commit()

    # book details
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    reviews = db.execute("SELECT review, rating, full_name FROM reviews " \
                         "INNER JOIN users ON users.id = reviews.user_id where book_isbn = :isbn",
                         {"isbn": isbn}).fetchall()

    return render_template("book.html", goodreads=GOODREADS, prompt=prompt, book=book, reviews=reviews)

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    """Handles API requests to the website."""
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"Error": "ISBN not found"}), 404

    review_count = db.execute("SELECT COUNT(reviews) FROM reviews WHERE book_isbn = :isbn",
                                {"isbn": isbn}).fetchone() # possible it is none
    # return print(review_count)
    average_rating = db.execute("SELECT AVG(rating) FROM reviews WHERE book_isbn = :isbn",
                                {"isbn": isbn}).fetchone() # possible it is none

    # get book details
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": int(review_count.count),
        "average_rating": float(average_rating.avg)
    })
