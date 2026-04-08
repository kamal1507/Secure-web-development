# app.py
# Main entry point for the Library Book Management System.
# Start the app by running: python app.py

from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from database import db, User
import os

# ---- Create and configure the Flask app ----
app = Flask(__name__)

# Secret key is used for session security and CSRF tokens
# In a real project, store this in an environment variable
app.config['SECRET_KEY'] = 'library_secret_key_2024'

# SQLite database - stored as a local file (easy for college projects)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect the database to the app
db.init_app(app)

# ---- Setup Flask-Login (handles sessions) ----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'       # redirect here if not logged in
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login calls this to find the logged-in user from the session
    return User.query.get(int(user_id))

# ---- Register route blueprints ----
# Each blueprint handles a section of the app
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(student_bp, url_prefix='/student')

# ---- Create tables and seed default admin ----
with app.app_context():
    db.create_all()  # creates all tables if they don't exist

    # Create a default admin account if there are no users yet
    if User.query.count() == 0:
        admin = User(
            name='Library Admin',
            email='admin@library.com',
            password=generate_password_hash('admin123'),  # hashed password
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin@library.com / admin123")

# ---- Run the app ----
if __name__ == '__main__':
    app.run(debug=True)  # debug=True gives helpful error messages during development
