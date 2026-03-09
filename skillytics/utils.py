from flask_login import current_user
from flask import flash, redirect, url_for

def is_student():
    return current_user.is_authenticated and current_user.get_role() == 'Student'

def is_staff():
    return current_user.is_authenticated and current_user.get_role() == 'Staff' and current_user.get_position() != 'Admin'

def is_admin():
    return current_user.is_authenticated and current_user.get_role() == 'Staff' and current_user.get_position() == 'Admin'

def format_time_sent(dt):
   
    month = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    date_str = f"{dt.day} {month[dt.month]} {dt.year}"
    time_str = dt.strftime("%I:%M %p")  # 12-hour format with AM/PM
    return date_str, time_str

def staffs_only():
    if not current_user.is_authenticated:
        flash('Please login to access this page', 'danger')
        return redirect(url_for('auth.user_login'))

    if not (is_admin() or is_staff()):
        flash('Invalid Access', 'danger')
        return redirect(url_for('main.dashboard'))

def admin_only():
    if not current_user.is_authenticated:
        flash('Please login to access this page', 'danger')
        return redirect(url_for('auth.user_login'))

    if not is_admin():
        flash('Invalid Access', 'danger')
        return redirect(url_for('main.dashboard'))
    
def student_only():
    if not current_user.is_authenticated:
        flash('Please login to access this page', 'danger')
        return redirect(url_for('auth.user_login'))

    if not is_student():
        flash('Invalid Access', 'danger')
        return redirect(url_for('main.dashboard'))
    
def authenticated():
    if not current_user.is_authenticated:
        flash('Please login to access this page', 'danger')
        return redirect(url_for('auth.user_login'))
