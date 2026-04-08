# routes/student.py
# All student-facing routes: dashboard, browse books, issue/return, profile

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, Book, IssueRecord
from datetime import datetime
from functools import wraps

student_bp = Blueprint('student', __name__)


# ---- Helper: Student-only access decorator ----
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Students only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ---- Student Dashboard ----
@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Count how many books this student currently has issued
    my_issued = IssueRecord.query.filter_by(user_id=current_user.id, status='issued').count()
    my_pending = IssueRecord.query.filter_by(user_id=current_user.id, status='pending').count()
    my_returned = IssueRecord.query.filter_by(user_id=current_user.id, status='returned').count()
    total_available = Book.query.filter(Book.available_copies > 0).count()

    return render_template('student/dashboard.html',
                           my_issued=my_issued,
                           my_pending=my_pending,
                           my_returned=my_returned,
                           total_available=total_available)


# ---- Browse / Search Books ----
@student_bp.route('/books')
@login_required
@student_required
def browse_books():
    # Get optional search query from the URL
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Book.query

    # Apply search filter if provided
    if search:
        query = query.filter(
            (Book.title.ilike(f'%{search}%')) |
            (Book.author.ilike(f'%{search}%')) |
            (Book.category.ilike(f'%{search}%'))
        )

    if category:
        query = query.filter_by(category=category)

    books = query.order_by(Book.title).all()

    # Get all categories for the filter dropdown
    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories]

    # Find books this student has already requested (to disable request button)
    my_pending_books = [r.book_id for r in
                        IssueRecord.query.filter_by(user_id=current_user.id)
                        .filter(IssueRecord.status.in_(['pending', 'issued'])).all()]

    return render_template('student/browse_books.html',
                           books=books,
                           search=search,
                           category=category,
                           categories=categories,
                           my_pending_books=my_pending_books)


# ---- Request / Issue a Book ----
@student_bp.route('/issue/<int:book_id>', methods=['POST'])
@login_required
@student_required
def issue_book(book_id):
    book = Book.query.get_or_404(book_id)

    # Check if book is available
    if book.available_copies < 1:
        flash('Sorry, this book is not available right now.', 'error')
        return redirect(url_for('student.browse_books'))

    # Check if student already has an active request for this book
    existing = IssueRecord.query.filter_by(
        book_id=book_id,
        user_id=current_user.id
    ).filter(IssueRecord.status.in_(['pending', 'issued'])).first()

    if existing:
        flash('You already have an active request for this book.', 'error')
        return redirect(url_for('student.browse_books'))

    # Create a new issue request (pending admin approval)
    record = IssueRecord(
        book_id=book_id,
        user_id=current_user.id,
        status='pending'
    )
    db.session.add(record)
    db.session.commit()

    flash(f'Book request submitted! Wait for admin approval.', 'success')
    return redirect(url_for('student.my_books'))


# ---- My Issued Books ----
@student_bp.route('/my-books')
@login_required
@student_required
def my_books():
    # Get all issue records for this student
    records = IssueRecord.query.filter_by(user_id=current_user.id)\
                               .order_by(IssueRecord.issue_date.desc()).all()
    return render_template('student/my_books.html', records=records)


# ---- Request to Return a Book ----
@student_bp.route('/return/<int:record_id>', methods=['POST'])
@login_required
@student_required
def return_book(record_id):
    record = IssueRecord.query.get_or_404(record_id)

    # Make sure this record belongs to the current student
    if record.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('student.my_books'))

    if record.status != 'issued':
        flash('This book cannot be returned at this time.', 'error')
        return redirect(url_for('student.my_books'))

    # Mark as return requested - admin will confirm
    record.status = 'return_requested'
    db.session.commit()

    flash('Return request submitted. Admin will confirm the return.', 'info')
    return redirect(url_for('student.my_books'))


# ---- Student Profile ----
@student_bp.route('/profile')
@login_required
@student_required
def profile():
    # Simple stats for profile page
    total_issued = IssueRecord.query.filter_by(user_id=current_user.id).count()
    currently_issued = IssueRecord.query.filter_by(user_id=current_user.id, status='issued').count()
    books_returned = IssueRecord.query.filter_by(user_id=current_user.id, status='returned').count()

    return render_template('student/profile.html',
                           total_issued=total_issued,
                           currently_issued=currently_issued,
                           books_returned=books_returned)
