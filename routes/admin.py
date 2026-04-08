# routes/admin.py
# All admin-only routes: dashboard, book management, issue management

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, User, Book, IssueRecord
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__)


# ---- Helper: Admin-only access decorator ----
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # If user is not admin, block access
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admins only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ---- Admin Dashboard ----
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Collect simple stats for the dashboard
    total_books = Book.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_issued = IssueRecord.query.filter_by(status='issued').count()
    pending_requests = IssueRecord.query.filter_by(status='pending').count()
    total_returned = IssueRecord.query.filter_by(status='returned').count()

    # Get recent 5 issue records for a quick overview
    recent_issues = IssueRecord.query.order_by(IssueRecord.issue_date.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_books=total_books,
                           total_students=total_students,
                           total_issued=total_issued,
                           pending_requests=pending_requests,
                           total_returned=total_returned,
                           recent_issues=recent_issues)


# ---- View All Books ----
@admin_bp.route('/books')
@login_required
@admin_required
def books():
    all_books = Book.query.order_by(Book.added_at.desc()).all()
    return render_template('admin/books.html', books=all_books)


# ---- Add a New Book ----
@admin_bp.route('/add-book', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        isbn = request.form.get('isbn', '').strip()
        copies = request.form.get('copies', '1').strip()

        # Basic validation
        if not title or not author or not category:
            flash('Title, author, and category are required.', 'error')
            return render_template('admin/add_book.html')

        # Validate copies is a number
        try:
            copies = int(copies)
            if copies < 1:
                raise ValueError()
        except ValueError:
            flash('Number of copies must be a positive number.', 'error')
            return render_template('admin/add_book.html')

        # Save the book to the database
        book = Book(
            title=title,
            author=author,
            category=category,
            isbn=isbn,
            total_copies=copies,
            available_copies=copies
        )
        db.session.add(book)
        db.session.commit()

        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/add_book.html')


# ---- Edit a Book ----
@admin_bp.route('/edit-book/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        isbn = request.form.get('isbn', '').strip()
        copies = request.form.get('copies', '1').strip()

        if not title or not author or not category:
            flash('Title, author, and category are required.', 'error')
            return render_template('admin/edit_book.html', book=book)

        try:
            copies = int(copies)
            if copies < 1:
                raise ValueError()
        except ValueError:
            flash('Number of copies must be a positive number.', 'error')
            return render_template('admin/edit_book.html', book=book)

        # Update book details
        # Adjust available copies proportionally if total copies changed
        diff = copies - book.total_copies
        book.title = title
        book.author = author
        book.category = category
        book.isbn = isbn
        book.total_copies = copies
        book.available_copies = max(0, book.available_copies + diff)

        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/edit_book.html', book=book)


# ---- Delete a Book ----
@admin_bp.route('/delete-book/<int:book_id>', methods=['POST'])
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    # Don't delete if there are active (issued) records
    active = IssueRecord.query.filter_by(book_id=book_id, status='issued').count()
    if active > 0:
        flash('Cannot delete: this book is currently issued to students.', 'error')
        return redirect(url_for('admin.books'))

    # Delete related issue records first, then the book
    IssueRecord.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted successfully.', 'success')
    return redirect(url_for('admin.books'))


# ---- View All Issue Records ----
@admin_bp.route('/issued-books')
@login_required
@admin_required
def issued_books():
    # Get filter from query string (e.g. ?status=pending)
    status_filter = request.args.get('status', 'all')

    if status_filter == 'all':
        records = IssueRecord.query.order_by(IssueRecord.issue_date.desc()).all()
    else:
        records = IssueRecord.query.filter_by(status=status_filter)\
                                   .order_by(IssueRecord.issue_date.desc()).all()

    return render_template('admin/issued_books.html', records=records, status_filter=status_filter)


# ---- Approve a Book Request (pending → issued) ----
@admin_bp.route('/approve/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def approve_issue(record_id):
    record = IssueRecord.query.get_or_404(record_id)

    if record.status != 'pending':
        flash('This request is not in pending state.', 'error')
        return redirect(url_for('admin.issued_books'))

    # Approve: mark as issued, set a 14-day due date
    record.status = 'issued'
    record.issue_date = datetime.utcnow()
    record.due_date = datetime.utcnow() + timedelta(days=14)

    # Reduce available copies
    record.book.available_copies = max(0, record.book.available_copies - 1)

    db.session.commit()
    flash('Book request approved. Student can now collect the book.', 'success')
    return redirect(url_for('admin.issued_books'))


# ---- Reject a Book Request ----
@admin_bp.route('/reject/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def reject_issue(record_id):
    record = IssueRecord.query.get_or_404(record_id)

    if record.status not in ('pending',):
        flash('Only pending requests can be rejected.', 'error')
        return redirect(url_for('admin.issued_books'))

    db.session.delete(record)
    db.session.commit()

    flash('Request rejected and removed.', 'info')
    return redirect(url_for('admin.issued_books'))


# ---- Confirm Book Return ----
@admin_bp.route('/confirm-return/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def confirm_return(record_id):
    record = IssueRecord.query.get_or_404(record_id)

    if record.status != 'return_requested':
        flash('No return request found for this record.', 'error')
        return redirect(url_for('admin.issued_books'))

    # Mark as returned, update book availability
    record.status = 'returned'
    record.return_date = datetime.utcnow()
    record.book.available_copies = min(record.book.total_copies,
                                       record.book.available_copies + 1)

    db.session.commit()
    flash('Return confirmed. Book is now available again.', 'success')
    return redirect(url_for('admin.issued_books'))


# ---- View All Students ----
@admin_bp.route('/students')
@login_required
@admin_required
def students():
    all_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    return render_template('admin/students.html', students=all_students)
