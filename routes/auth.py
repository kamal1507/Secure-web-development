# routes/auth.py
# Handles user registration, login, and logout

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User
import re

auth_bp = Blueprint('auth', __name__)


# ---- Home page - redirect to login ----
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Send user to their respective dashboard
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


# ---- Login Page ----
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Basic validation
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')

        # Look up the user by email
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # start the session
            flash(f'Welcome back, {user.name}!', 'success')

            # Send to correct dashboard based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash('Incorrect email or password. Please try again.', 'error')

    return render_template('login.html')


# ---- Register Page (students only) ----
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Simple validations
        if not name or not email or not password or not confirm:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(name) < 2:
            flash('Name must be at least 2 characters.', 'error')
            return render_template('register.html')

        # Basic email format check
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        # Check if email is already registered
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')

        # Create the new student user
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),  # never store plain passwords!
            role='student'
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ---- Logout ----
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
