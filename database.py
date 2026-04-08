# database.py
# This file sets up the database and defines our data models (tables).

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Create the database object - we'll connect it to the app later
db = SQLAlchemy()


# ---- User Model ----
# Represents both admin and student users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # stored as a hash, never plain text
    role = db.Column(db.String(20), default='student')    # either 'admin' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Link to issue records for this user
    issued_books = db.relationship('IssueRecord', backref='user', lazy=True)


# ---- Book Model ----
# Represents a book in the library
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(50), nullable=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Link to issue records for this book
    issue_records = db.relationship('IssueRecord', backref='book', lazy=True)


# ---- IssueRecord Model ----
# Tracks which student issued which book and when
class IssueRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)   # null means not yet returned
    due_date = db.Column(db.DateTime, nullable=True)
    # Status: 'pending' = student requested, 'issued' = admin approved, 'returned' = returned
    status = db.Column(db.String(20), default='pending')
