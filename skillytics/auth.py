from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from skillytics import bcrypt
from skillytics.models import Student, Staff
from skillytics.CRUD import send_change_password_email


auth = Blueprint('auth', __name__)

@auth.route('/user-login', methods=['POST', 'GET'])
def user_login():

    if current_user.is_authenticated:  # If already logged in
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        
        user_email_or_id = request.form['user-id-or-email']
        user_password = request.form['user-password']
        
        # Try matching Student by student_id or email
        user = Student.query.filter(
            (Student.student_id == user_email_or_id) | (Student.email == user_email_or_id)
        ).first()
        
        # If not found in Student, try Staff by staff_id or email
        if not user:
            user = Staff.query.filter(
                (Staff.staff_id == user_email_or_id) | (Staff.email == user_email_or_id)
            ).first()

        # Check user existence and password hash
        if user and bcrypt.check_password_hash(user.password, user_password):
            login_user(user)
            flash("Logged in successfully!", "success")

            return redirect(url_for('main.dashboard'))

        else:
            flash("Invalid ID/email or password", "danger")
            return redirect(url_for('auth.user_login'))

    return render_template('user-login.html')


from skillytics.CRUD import get_user_by_email, send_reset_email
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_by_email(email)
        if user and user.position != 'Admin':
            send_reset_email(user)
            flash('An email with password reset instructions has been sent to your email.', 'success')
        
        else:
            flash('Email address not found.', 'danger')

        return redirect(url_for('auth.forgot_password'))
        
    return render_template('forgot-password.html')


from skillytics.CRUD import verify_reset_token, update_user_password
@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('That is an invalid or expired token', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')

        if new_password != confirm_password:
            flash("Passwords don't match.", 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        user = get_user_by_email(email)
        if user:
            update_user_password(user, new_password)
            send_change_password_email(email)
            flash('Your password has been updated! You can now log in.', 'success')
            return redirect(url_for('auth.user_login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('reset-password.html', token=token)