/* create.sql */
/* users tables */
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);

/* books table */
CREATE TABLE books (
    isbn VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year VARCHAR NOT NULL
);

/* reviews table */
CREATE TABLE reviews  (
    id SERIAL PRIMARY KEY,
    review VARCHAR NOT NULL,
    rating INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id),
    book_isbn VARCHAR REFERENCES books(isbn)
);