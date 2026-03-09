from skillytics.models import Student, Enrollment, TechnicalSkillScore, Course, Staff, TechnicalSkillCategory,Part, StudentSemesterCluster, Feedback, StudentPartGPA, Notification
from sqlalchemy.sql import case, func
from skillytics import db, bcrypt
from collections import Counter
from datetime import datetime
import pytz
import humanize
from collections import defaultdict
from scipy.cluster.hierarchy import linkage
from flask import flash, url_for, current_app, session
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from flask_mail import Message
from skillytics import mail
import random
from skillytics.utils import format_time_sent

from datetime import datetime


def send_otp_email(email):
    otp_code = f"{random.randint(100000, 999999)}"
    session['otp_code'] = otp_code
    session['otp_email'] = email

    msg = Message('Your Verification Code',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f'Your verification code is: {otp_code}'
    mail.send(msg)

def send_staff_email(email, staff_id, password):
    msg = Message('Account Successfully Created!',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[email])

    msg.body = (
        f"Dear Staff,\n\n"
        f"Your account has been created successfully.\n"
        f"Here are your credentials:\n"
        f"Staff ID: {staff_id}\n"
        f"Password: {password}\n\n"
        f"Please log in and change your password after first login.\n\n"
        f"Regards,\nSkillytics Team"
    )

    mail.send(msg)

## forgot password
def send_reset_email(user):
    
    token = generate_reset_token(user.email)

    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.body = f'To reset your password, visit the following link: {reset_url}'
    mail.send(msg)

def activate_student_acc(email):
    msg = Message(
        subject="Your Account Has Been Activated",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg.body = (
        f"Hello,\n\n"
        f"Welcome to Skillytics! Your student account has been successfully activated.\n\n"
        f"You can now log in and begin using the platform.\n\n"
        f"If you did not request this activation, please contact the Skillytics support team immediately.\n\n"
        f"Best regards,\n"
        f"Skillytics Team"
    )

    mail.send(msg)

def send_warning_email(email, academic_message, technical_message):
    msg = Message(
        subject="Performance Warning - Skillytics",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg.body = (
        f"Dear Student,\n\n"
        f"We would like to bring to your attention some concerns regarding your performance:\n\n"
        f"{academic_message}\n"
        f"{technical_message}\n"
        f"Please take necessary actions to improve your performance. You can:\n"
        f"1. Meet with your academic advisor\n"
        f"2. Attend additional tutoring sessions\n"
        f"3. Participate in skill development workshops\n"
        f"4. Review and improve your study habits\n\n"
        f"Remember, we are here to support your academic journey. Don't hesitate to reach out to your lecturers or academic advisors for guidance.\n\n"
        f"Best regards,\n"
        f"Skillytics Team"
    )

    mail.send(msg)


from itsdangerous import URLSafeTimedSerializer
# Serializer for generating and verifying tokens
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except Exception:
        return None
    return email

def get_user_by_email(email):
    user = Student.query.filter_by(email=email).first()
    if user:
        return user

    return Staff.query.filter_by(email=email).first()


def update_user_password(user, new_password):
    hashed_pw = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_pw
    db.session.commit()

##########      CREATE      ##############

def update_last_online(user):
    malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')
    user.last_online = datetime.now(malaysia_time)
    db.session.commit()


def save_feedback(category, message, student_id=None, staff_id=None):
    malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')

    feedback = Feedback(
        category=category,
        message=message,
        time_sent = datetime.now(malaysia_time),
        student_id=student_id,
        staff_id=staff_id
    )
    db.session.add(feedback)
    db.session.commit()


def send_feedback_email(sender_email, category, message):
    msg = Message(
        subject="New Feedback Received!",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=['aqiman1312@gmail.com']
    )

    msg.body = (
        f"Hello Admin,\n\n"
        f"You have received new feedback via the Skillytics platform.\n\n"
        f"📧 From: {sender_email}\n"
        f"📂 Category: {category}\n\n"
        f"📝 Message:\n{message}\n\n"
        f"---\nSkillytics Notification System"
    )

    mail.send(msg)


def add_staff_to_db(staff_id, email, first_name, last_name, gender, position, phone_number, address, picture_filename):

    # Set default password for staff
    hashed_password = bcrypt.generate_password_hash('123').decode('utf-8')

    # Set default picture if staff didnt enter picture
    if picture_filename is None:
        if gender == 'Male':
            picture_filename = 'default-staff-male.png'
        else:
            picture_filename = 'default-staff-female.png'

    # Check if the email or ID is already registered in either Student or Staff tables
    if Student.query.filter((Student.email == email) | (Student.student_id == staff_id)).first() or \
       Staff.query.filter((Staff.email == email) | (Staff.staff_id == staff_id)).first():
        flash("Email or ID already registered", "danger")
        return False  # Return False when the email or ID is already taken

    try:
        # Create a new Staff object
        new_staff = Staff(
            staff_id=staff_id,
            picture=picture_filename,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            position=position,
            phone_number=phone_number,
            address=address,
            institution_name='UiTM Kampus Jasin',
            faculty_name='FSKM'
        )
        
        # Add the new staff member to the database
        db.session.add(new_staff)
        db.session.commit()

        # Flash a success message
        flash("Staff added successfully!", "success")
        return True  # Return True when the staff is successfully added

    except Exception as e:
        # If there's an error (e.g., a database issue), flash the error message
        flash(f"Error adding staff: {str(e)}", "danger")
        db.session.rollback()  # Rollback the session in case of error
        return False  # Return False when an error occurs

##########    END CREATE    ##############



##########      READ      ##############

##      admin-list-feedback.html    ##

def get_all_feedbacks():
    feedback_rows = (
        Feedback.query
        .outerjoin(Student, Feedback.student_id == Student.student_id)
        .outerjoin(Staff, Feedback.staff_id == Staff.staff_id)
        .add_columns(
            Feedback.feedback_id,
            Feedback.category,
            Feedback.message,
            Feedback.time_sent,
            Student.email.label('student_email'),
            Staff.email.label('staff_email'),
        )
        .order_by(Feedback.time_sent.desc())
        .all()
    )

    feedbacks = []
    for row in feedback_rows:
        _, feedback_id, category, message, time_sent, student_email, staff_email = row
        date_sent, time_only = format_time_sent(time_sent)
        feedbacks.append({
            "feedback_id": feedback_id,
            "category": category,
            "message": message,
            "date_sent": date_sent,
            "time_sent": time_only,
            "student_email": student_email,
            "staff_email": staff_email
        })

    return feedbacks

##      end admin-list-feedback.html    ##


####     staff_dashboard.html     #####

def get_all_total_students():
    total_students = Student.query.count()
    return total_students


def get_all_academic_gauge_chart():
    total_gpa = 0
    count_part = 0

    for part_no in range(2, 8):  # part 2 hingga 7
        # Cari student yang sekarang di part_no
        students = db.session.query(Student.student_id).filter(Student.part_id == part_no).subquery()
        # Ambil GPA mereka pada previous part
        prev_part_no = part_no - 1
        gpas = db.session.query(StudentPartGPA.gpa).filter(
            StudentPartGPA.student_id.in_(students.select()),
            StudentPartGPA.part_id == prev_part_no
        ).all()
        gpa_list = [g[0] for g in gpas if g[0] is not None]
        if gpa_list:
            avg_gpa = sum(gpa_list) / len(gpa_list)
        else:
            avg_gpa = 0
        total_gpa += avg_gpa
        count_part += 1

    # Bahagi dengan 6 (part 2 hingga 7)
    if count_part > 0:
        final_avg = total_gpa / 6
        return round(final_avg, 2)
    else:
        return 0


def get_all_technical_gauge_chart():
    # Step 1: Average q1–q5 per student & category & part
    subquery = (
        db.session.query(
            TechnicalSkillScore.student_id,
            TechnicalSkillScore.part_id,
            TechnicalSkillScore.technical_skill_category_id,
            func.avg(
                (TechnicalSkillScore.q1_score +
                 TechnicalSkillScore.q2_score +
                 TechnicalSkillScore.q3_score +
                 TechnicalSkillScore.q4_score +
                 TechnicalSkillScore.q5_score) / 5.0
            ).label("avg_score")
        )
        .filter(
            TechnicalSkillScore.q1_score != None,
            TechnicalSkillScore.q2_score != None,
            TechnicalSkillScore.q3_score != None,
            TechnicalSkillScore.q4_score != None,
            TechnicalSkillScore.q5_score != None
        )
        .group_by(
            TechnicalSkillScore.student_id,
            TechnicalSkillScore.part_id,
            TechnicalSkillScore.technical_skill_category_id
        )
        .subquery()
    )

    # Step 2: Global average of all category scores
    global_avg = db.session.query(func.avg(subquery.c.avg_score)).scalar()
    return round(global_avg, 2) if global_avg is not None else 0


def get_all_student_status():
    # Fetch all statuses from the Student table
    status_list = [s.status for s in Student.query.all() if s.status]

    # Count how many of each status exists (e.g., Completed, Incomplete)
    status_counts = dict(Counter(status_list))

    # Define color mapping for different statuses
    status_colors = {
        "Completed": "#007bff",    # Blue
        "Incomplete": "#dc3545",   # Red
    }

    # Convert to Highcharts format with colors
    all_students_status = [
        {
            "name": status, 
            "y": count,
            "color": status_colors.get(status, "#6c757d")  # Default to gray if status not found
        } 
        for status, count in status_counts.items()
    ]
    
    return all_students_status


def gauge_academic_by_part(part_id):
    previous_part_id = part_id - 1

    # Cari student yang sekarang di part_id
    students = db.session.query(Student.student_id).filter(Student.part_id == part_id).subquery()
    # Ambil GPA mereka pada previous part
    gpas = db.session.query(StudentPartGPA.gpa).filter(
        StudentPartGPA.student_id.in_(students.select()),
        StudentPartGPA.part_id == previous_part_id
    ).all()
    gpa_list = [g[0] for g in gpas if g[0] is not None]
    avg_gpa = sum(gpa_list) / len(gpa_list) if gpa_list else 0
    print(f"Average GPA for part {part_id}: {avg_gpa}")
    return round(avg_gpa, 2)


def gauge_technical_by_part(part_id):
    previous_part_id = part_id - 1

    # Cari student yang sekarang di part_id
    students = db.session.query(Student.student_id).filter(Student.part_id == part_id).all()
    student_ids = [s[0] if isinstance(s, tuple) else s.student_id for s in students]

    if not student_ids:
        print(f"No students found for part {part_id}")
        return 0

    student_averages = []
    for student_id in student_ids:
        # Ambil semua skor technical untuk previous part
        scores = db.session.query(
            TechnicalSkillScore.technical_skill_category_id,
            TechnicalSkillScore.q1_score,
            TechnicalSkillScore.q2_score,
            TechnicalSkillScore.q3_score,
            TechnicalSkillScore.q4_score,
            TechnicalSkillScore.q5_score
        ).filter(
            TechnicalSkillScore.student_id == student_id,
            TechnicalSkillScore.part_id == previous_part_id
        ).all()

        category_avgs = []
        for s in scores:
            q_scores = [s[1], s[2], s[3], s[4], s[5]]
            valid_scores = [q for q in q_scores if q is not None]
            if valid_scores:
                category_avgs.append(sum(valid_scores) / len(valid_scores))
        if category_avgs:
            student_averages.append(sum(category_avgs) / len(category_avgs))

    avg_technical = sum(student_averages) / len(student_averages) if student_averages else 0
    print(f"Average technical score for part {part_id}: {avg_technical}")
    return round(avg_technical, 2)

def gauge_technical_by_current_part(part_id):

    # Step 1: Get students currently in part X
    students = db.session.query(Student.student_id).filter(
        Student.part_id == part_id,
        Student.status == 'Completed'
    ).subquery()

    # Step 2: For each student in that part, get their tech scores from previous part (per category)
    subquery = (
        db.session.query(
            TechnicalSkillScore.student_id,
            func.avg(
                (TechnicalSkillScore.q1_score +
                 TechnicalSkillScore.q2_score +
                 TechnicalSkillScore.q3_score +
                 TechnicalSkillScore.q4_score +
                 TechnicalSkillScore.q5_score) / 5.0
            ).label("avg_score")
        )
        .filter(TechnicalSkillScore.student_id.in_(students))
        .filter(TechnicalSkillScore.part_id == part_id)
        .filter(
            TechnicalSkillScore.q1_score != None,
            TechnicalSkillScore.q2_score != None,
            TechnicalSkillScore.q3_score != None,
            TechnicalSkillScore.q4_score != None,
            TechnicalSkillScore.q5_score != None
        )
        .group_by(TechnicalSkillScore.student_id, TechnicalSkillScore.technical_skill_category_id)
        .subquery()
    )

    # Step 3: Now average across all student-category scores
    final_avg = db.session.query(func.avg(subquery.c.avg_score)).scalar()
    print(f"Average technical score for current part {part_id}: {final_avg}")

    return round(final_avg or 0, 2)

def get_barchart_academic_staff(part_no=None):
    if not part_no:
        return []

    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    # Aggregate GPA per course in that part
    result = (
        db.session.query(
            Course.course_code,
            func.avg(grade_case).label('gpa')
        )
        .join(Enrollment, Enrollment.course_code == Course.course_code)
        .filter(Course.part_id == part_no)
        .filter(Enrollment.course_grade != None)
        .group_by(Course.course_code)
        .order_by(Course.course_code)
        .all()
    )

    return result

def get_barchart_technical_staff(part_no=None):
    if not part_no:
        return []

    # Average the 5 question scores per category
    avg_score_expr = (
        (func.coalesce(TechnicalSkillScore.q1_score, 0) +
         func.coalesce(TechnicalSkillScore.q2_score, 0) +
         func.coalesce(TechnicalSkillScore.q3_score, 0) +
         func.coalesce(TechnicalSkillScore.q4_score, 0) +
         func.coalesce(TechnicalSkillScore.q5_score, 0)) / 5.0
    )

    result = (
        db.session.query(
            TechnicalSkillCategory.ts_type.label('category'),
            func.avg(avg_score_expr).label('avg_score')
        )
        .join(TechnicalSkillScore, TechnicalSkillScore.technical_skill_category_id == TechnicalSkillCategory.technical_skill_category_id)
        .filter(TechnicalSkillScore.part_id == part_no)
        .group_by(TechnicalSkillCategory.ts_type)
        .order_by(TechnicalSkillCategory.ts_type)
        .all()
    )

    return result


def count_students_by_part(part_id):
    return Student.query.filter_by(part_id=part_id).count()


def get_student_status_pie_data_by_part(part_id):
    status_list = [
        s.status for s in Student.query.filter_by(part_id=part_id).all()
        if s.status
    ]
    status_counts = dict(Counter(status_list))
    
    # Define color mapping for different statuses
    status_colors = {
        "Completed": "#007bff",    # Blue
        "Incomplete": "#dc3545",   # Red
    }
    
    return [
        {
            "name": status, 
            "y": count,
            "color": status_colors.get(status, "#6c757d")  # Default to gray if status not found
        } 
        for status, count in status_counts.items()
    ]


def get_relative_last_online(last_online):
    if not last_online:
        return "Never"

    malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')

    # Ensure both times are timezone-aware
    if last_online.tzinfo is None:
        last_online = malaysia_time.localize(last_online)

    now = datetime.now(malaysia_time)
    return humanize.naturaltime(now - last_online)

####    End staff-dashboard.html    ######


####    student-dashboard.html  ####

def get_student_gpa_all_parts(part_id):
    # Retrieve all unique GPAs for a given student across all parts, excluding the current part
    student_gpa_data = db.session.query(
        StudentPartGPA.part_id, StudentPartGPA.gpa
    ).join(Part, Part.part_id == StudentPartGPA.part_id).filter(
        StudentPartGPA.student_id == current_user.student_id,
        StudentPartGPA.part_id < part_id
    ).distinct(StudentPartGPA.part_id).all()  # Ensure unique part_id entries

    return student_gpa_data

## for staff
def get_student_gpa_all_parts_for_staffs(selected_student, part_id):
    # Retrieve all unique GPAs for a given student across all parts, excluding the current part
    student_gpa_data = db.session.query(
        StudentPartGPA.part_id, StudentPartGPA.gpa
    ).join(Part, Part.part_id == StudentPartGPA.part_id).filter(
        StudentPartGPA.student_id == selected_student.student_id,
        StudentPartGPA.part_id < part_id
    ).distinct(StudentPartGPA.part_id).all()  # Ensure unique part_id entries

    return student_gpa_data

def get_barchart_academic_student(part_no):

    # Map letter grades to GPA points
    grade_map = {
        'A+': 4.00, 'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00, 'C-': 1.67,
        'D+': 1.33, 'D': 1.00, 'E': 0.67,
        'F': 0.00
    }

    # Get part object
    part = Part.query.filter_by(part_no=part_no).first()
    if not part:
        return []

    # Get all courses for this part
    courses = Course.query.filter_by(part_id=part.part_id).all()
    if not courses:
        return []

    course_codes = [course.course_code for course in courses]

    # Get student's enrollments for these courses
    enrollments = Enrollment.query.filter(
        Enrollment.student_id == current_user.student_id,
        Enrollment.course_code.in_(course_codes)
    ).all()

    # Build map course_code -> grade for quick lookup
    enrollment_map = {en.course_code: en.course_grade for en in enrollments}

    result = []
    for course in courses:
        grade_letter = enrollment_map.get(course.course_code)
        if grade_letter:
            grade_letter_clean = grade_letter.strip().upper()
            gpa = grade_map.get(grade_letter_clean, 0.0)
            result.append((course.course_name, gpa, grade_letter_clean))
        else:
            result.append((course.course_name, 0.0, 'N/A'))

    return result


## for staffs
def get_barchart_academic_student_for_staffs(selected_student, part_no):

    # Map letter grades to GPA points
    grade_map = {
        'A+': 4.00, 'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00, 'C-': 1.67,
        'D+': 1.33, 'D': 1.00, 'E': 0.67,
        'F': 0.00
    }

    # Get part object
    part = Part.query.filter_by(part_no=part_no).first()
    if not part:
        return []

    # Get all courses for this part
    courses = Course.query.filter_by(part_id=part.part_id).all()
    if not courses:
        return []

    course_codes = [course.course_code for course in courses]

    # Get student's enrollments for these courses
    enrollments = Enrollment.query.filter(
        Enrollment.student_id == selected_student.student_id,
        Enrollment.course_code.in_(course_codes)
    ).all()

    # Build map course_code -> grade for quick lookup
    enrollment_map = {en.course_code: en.course_grade for en in enrollments}

    result = []
    for course in courses:
        grade_letter = enrollment_map.get(course.course_code)
        if grade_letter:
            grade_letter_clean = grade_letter.strip().upper()
            gpa = grade_map.get(grade_letter_clean, 0.0)
            result.append((course.course_name, gpa, grade_letter_clean))
        else:
            result.append((course.course_name, 0.0, 'N/A'))

    return result


def get_technical_scores_by_all_parts(student_id, current_part_no):
    # Fetch parts up to current part_no
    parts = Part.query.filter(
        (Part.part_no <= current_part_no)
    ).order_by(Part.part_no).all()

    if not parts:
        return {}

    categories = TechnicalSkillCategory.query.all()
    data = {}

    for part in parts:
        scores_by_category = {}
        scores = TechnicalSkillScore.query.filter_by(student_id=student_id, part_id=part.part_id).all()

        for cat in categories:
            cat_scores = [s for s in scores if s.technical_skill_category_id == cat.technical_skill_category_id]
            if cat_scores:
                total_score = 0
                count = 0
                for s in cat_scores:
                    q_scores = [s.q1_score, s.q2_score, s.q3_score, s.q4_score, s.q5_score]
                    valid_scores = [q for q in q_scores if q is not None]
                    if valid_scores:
                        total_score += sum(valid_scores) / len(valid_scores)
                        count += 1
                avg_score = total_score / count if count > 0 else 0
            else:
                avg_score = 0
            scores_by_category[cat.ts_type] = round(avg_score, 2)

        data[part.part_no] = {
            'categories': list(scores_by_category.keys()),
            'scores': list(scores_by_category.values())
        }

    return data

def get_accumulated_technical_scores_by_all_parts(student_id, current_part_no):
    """
    Get cumulative technical scores from part 1 to current part.
    Each part shows the accumulated average from part 1 up to that part.
    """
    # Fetch parts up to current part_no within the current session only
    parts = Part.query.filter(
        (Part.part_no <= current_part_no)
    ).order_by(Part.part_no).all()

    if not parts:
        return {}

    categories = TechnicalSkillCategory.query.all()
    data = {}

    for current_part in parts:
        # Get all parts from 1 to current part for cumulative calculation
        parts_up_to_current = [p for p in parts if p.part_no <= current_part.part_no]
        part_ids_up_to_current = [p.part_id for p in parts_up_to_current]
        
        # Get all scores from part 1 to current part
        all_scores = TechnicalSkillScore.query.filter(
            TechnicalSkillScore.student_id == student_id,
            TechnicalSkillScore.part_id.in_(part_ids_up_to_current)
        ).all()

        cumulative_scores_by_category = {}
        
        for cat in categories:
            # Get all scores for this category from part 1 to current part
            cat_scores = [s for s in all_scores if s.technical_skill_category_id == cat.technical_skill_category_id]
            
            if cat_scores:
                total_score = 0
                count = 0
                
                for score_record in cat_scores:
                    # Calculate average for each score record (q1-q5)
                    q_scores = [
                        score_record.q1_score, 
                        score_record.q2_score, 
                        score_record.q3_score, 
                        score_record.q4_score, 
                        score_record.q5_score
                    ]
                    valid_scores = [q for q in q_scores if q is not None]
                    
                    if valid_scores:
                        record_avg = sum(valid_scores) / len(valid_scores)
                        total_score += record_avg
                        count += 1
                
                # Calculate cumulative average for this category
                cumulative_avg = total_score / count if count > 0 else 0
            else:
                cumulative_avg = 0
            
            cumulative_scores_by_category[cat.ts_type] = round(cumulative_avg, 2)

        data[current_part.part_no] = {
            'categories': list(cumulative_scores_by_category.keys()),
            'scores': list(cumulative_scores_by_category.values())
        }

    return data

def get_student_cgpa(student_id):
    """
    Calculate CGPA for UiTM student using the official formula:
    CGPA = Sum of all Total Grade Points for all semesters / Sum of all credits for all semesters
    
    Where Total Grade Points = Grade Point Value x Credit Hours
    """
    
    # UiTM Grade Point mapping
    grade_point_map = {
        'A+': 4.00, 'A': 4.00, 'A-': 3.70,
        'B+': 3.30, 'B': 3.00, 'B-': 2.70,
        'C+': 2.30, 'C': 2.00, 'C-': 1.70,
        'D+': 1.30, 'D': 1.00, 'E': 0.70,
        'F': 0.00
    }
    
    # Get all enrollments for the student with grades
    enrollments = Enrollment.query.filter(
        Enrollment.student_id == student_id,
        Enrollment.course_grade.isnot(None),
        Enrollment.course_grade != ''
    ).all()
    
    if not enrollments:
        return None  # No enrollment records with grades found
    
    total_grade_points = 0.0
    total_credit_hours = 0
    
    for enrollment in enrollments:
        # Get course details to get credit hours
        course = Course.query.filter_by(course_code=enrollment.course_code).first()
        
        if not course or not course.credit_hour:
            continue  # Skip if course not found or no credit hours
            
        # Clean and get grade
        grade = enrollment.course_grade.strip().upper()
        
        if grade not in grade_point_map:
            continue  # Skip invalid grades
            
        # Calculate grade points for this course
        grade_point_value = grade_point_map[grade]
        credit_hours = course.credit_hour
        course_grade_points = grade_point_value * credit_hours
        
        # Add to totals
        total_grade_points += course_grade_points
        total_credit_hours += credit_hours
    
    if total_credit_hours == 0:
        return None  # No valid courses with credit hours
    
    # Calculate CGPA using UiTM formula
    cgpa = total_grade_points / total_credit_hours
    return round(cgpa, 2)



###     End student-dashboard.html  ###


####    student-form-technical.html     ####

def get_student_ts_score_by_ts(student_id, ts_category_id, part_id):
    try:
        # Query to get the technical skill scores by student_id, ts_category_id, and part_id
        ts_scores = db.session.query(TechnicalSkillScore).filter_by(
            student_id=student_id,
            technical_skill_category_id=ts_category_id,
            part_id=part_id
        ).first()

        if ts_scores:
            # If the student has scores for this category and part, return them
            return {
                'q1_score': ts_scores.q1_score,
                'q2_score': ts_scores.q2_score,
                'q3_score': ts_scores.q3_score,
                'q4_score': ts_scores.q4_score,
                'q5_score': ts_scores.q5_score
            }
        else:
            print("No scores found for this student, category, and part")
            return None  # No scores found for this student, category, and part

    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    
from sqlalchemy import or_
def get_all_coordinators():
    return Staff.query.filter(
    or_(
        Staff.position == 'Coordinator',
        Staff.position == 'Admin'
    )
).all()

def send_low_technical_score_email(part_id, avg_score):
    coordinators = get_all_coordinators()
    coordinator_emails = [staff.email for staff in coordinators if staff.email]

    if not coordinator_emails:
        print("No coordinator emails found")
        return

    subject = f"[ALERT] Low Technical Skill Score in Part {part_id}"
    body = (
        f"Dear Admin and Coordinator,\n\n"
        f"The average technical skill score for students in Part {part_id} is *{avg_score:.2f}*, "
        f"which is below the acceptable threshold (2.5).\n\n"
        f"Please review the dashboard or take appropriate actions.\n\n"
        f"Best regards,\nAcademic Monitoring System"
    )

    msg = Message(
        subject,
        recipients=coordinator_emails,
        body=body,
        sender=current_app.config['MAIL_USERNAME']
    )

    mail.send(msg)

def check_and_notify_low_technical_average(part_id, threshold=2.5):
    avg_score = gauge_technical_by_current_part(part_id)
    if avg_score < threshold:
        send_low_technical_score_email(part_id, avg_score)
        return True
    return False

####    End student-form-technical.html     ###


#####   analysis-clustering.html   #######

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pandas as pd


def get_academic_bubble_data_by_part(part_id=2):
    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    # Get courses and grades from previous part for students in the current part
    results = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            grade_case.label('grade_point'),
            StudentSemesterCluster.cluster_academic
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(StudentSemesterCluster, 
              (Student.student_id == StudentSemesterCluster.student_id) &
              (Student.part_id == StudentSemesterCluster.part_id))
        .filter(Student.part_id == part_id)
        .filter(Course.part_id == part_id - 1)
        .all()
    )

    if not results:
        return []

    # Cluster -> Course -> [grades]
    nested_data = defaultdict(lambda: defaultdict(list))

    for student_id, course_code, grade_point, cluster_label in results:
        if cluster_label is None or grade_point is None:
            continue
        cluster_key = f"Cluster {cluster_label}"
        nested_data[cluster_key][course_code].append(grade_point)

    # Format for Highcharts
    bubble_academic = []
    for cluster_name, course_grades in nested_data.items():
        # Flatten all grades for the cluster
        all_grades = [grade for grades in course_grades.values() for grade in grades]
        cluster_avg = round(sum(all_grades) / len(all_grades), 2) if all_grades else 0

        bubble_academic.append({
            "name": f"{cluster_name} (Avg: {cluster_avg})",  # 👈 Append avg to cluster name
            "data": [
                {
                    "name": course_code,
                    "value": round(sum(grades) / len(grades), 2)
                }
                for course_code, grades in course_grades.items() if grades
            ]
        })


    return bubble_academic


def get_academic_scatter_pca_by_part(part_id):
    previous_part = part_id - 1
    if previous_part < 1:
        return []

    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    results = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            grade_case.label("grade_point")
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (Student.student_id == StudentSemesterCluster.student_id) &
              (Student.part_id == StudentSemesterCluster.part_id))
        .filter(Course.part_id == previous_part)
        .filter(Student.part_id == part_id)
        .all()
    )

    if not results:
        return []

    df = pd.DataFrame(results, columns=['student_id', 'course_code', 'grade_point'])
    pivot = df.pivot_table(index='student_id', columns='course_code', values='grade_point', fill_value=0)

    # PCA only (no clustering)
    if len(pivot) < 2:
        return []

    scaler = StandardScaler()
    reduced = PCA(n_components=2).fit_transform(scaler.fit_transform(pivot))

    pivot['x'] = reduced[:, 0]
    pivot['y'] = reduced[:, 1]

    # 🔁 Use saved cluster from DB
    cluster_map = {
        s.student_id: s.cluster_academic
        for s in db.session.query(StudentSemesterCluster)
        .filter(StudentSemesterCluster.part_id == part_id)
        .all()
    }
    pivot['cluster'] = pivot.index.map(cluster_map)

    # 📊 Format for Highcharts
    scatter_academic = []
    for cluster_label, group in pivot.groupby('cluster'):
        scatter_academic.append({
            "name": f"Cluster {cluster_label}",
            "data": [
                {"x": round(row['x'], 2), "y": round(row['y'], 2), "name": f"Student {idx}",  "student_id": idx}
                for idx, row in group.iterrows()
            ]
        })

    return scatter_academic


def get_academic_linkage_by_part(part_id):

    # Grade conversion logic
    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    # Query academic grades of students for the previous part courses
    results = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            grade_case.label("grade_point")
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (Student.student_id == StudentSemesterCluster.student_id) &
              (Student.part_id == StudentSemesterCluster.part_id))
        .filter(Course.part_id == part_id-1)
        .filter(Student.part_id == part_id)
        .all()
    )

    if not results:
        return None, None, None

    # Build a pivot table: rows = student_id, columns = course_code, values = grade_point
    df = pd.DataFrame(results, columns=['student_id', 'course_code', 'grade_point'])
    pivot = df.pivot_table(index='student_id', columns='course_code', values='grade_point').fillna(0)

    # Standardize for clustering
    scaled = StandardScaler().fit_transform(pivot)

    # Generate hierarchical linkage matrix
    Z = linkage(scaled, method='ward', metric='euclidean')

    # List of student IDs for labeling
    labels = pivot.index.astype(str).tolist()

    # Build a dict of student_id → cluster from database
    cluster_map = {
        str(s.student_id): s.cluster_academic
        for s in db.session.query(StudentSemesterCluster)
        .filter(StudentSemesterCluster.part_id == part_id)
        .filter(StudentSemesterCluster.cluster_academic != None)
        .all()
    }

    return Z, labels, cluster_map


def get_technical_bubble_data_by_part(part_id=2):
    from collections import defaultdict

    scores = (
        db.session.query(
            TechnicalSkillScore.student_id,
            TechnicalSkillCategory.ts_type.label("category_name"),
            StudentSemesterCluster.cluster_technical_skills,
            TechnicalSkillScore.q1_score,
            TechnicalSkillScore.q2_score,
            TechnicalSkillScore.q3_score,
            TechnicalSkillScore.q4_score,
            TechnicalSkillScore.q5_score
        )
        .join(TechnicalSkillCategory, TechnicalSkillScore.technical_skill_category_id == TechnicalSkillCategory.technical_skill_category_id)
        .join(StudentSemesterCluster,
              (TechnicalSkillScore.student_id == StudentSemesterCluster.student_id) &
              (StudentSemesterCluster.part_id == part_id))
        .filter(StudentSemesterCluster.cluster_technical_skills != None)
        .all()
    )

    if not scores:
        return []

    nested_data = defaultdict(lambda: defaultdict(list))

    for student_id, category_name, cluster, q1, q2, q3, q4, q5 in scores:
        values = [q for q in [q1, q2, q3, q4, q5] if q is not None]
        if not values or cluster is None:
            continue
        avg_score = sum(values) / len(values)
        nested_data[f"Cluster {cluster}"][category_name].append(avg_score)

    bubble_technical = []
    for cluster_name, skills in nested_data.items():
        # Compute average for all skills in cluster
        all_scores = [score for skill_scores in skills.values() for score in skill_scores]
        cluster_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

        # Format each skill as a sub-bubble
        skill_bubbles = [
            {
                "name": skill_name,
                "value": round(sum(values) / len(values), 2)
            }
            for skill_name, values in skills.items()
        ]

        # Include cluster average in cluster name
        bubble_technical.append({
            "name": f"{cluster_name} (Avg: {cluster_avg})",
            "data": skill_bubbles
        })

    return bubble_technical


def get_technical_scatter_pca_by_part(part_id=2):
    scores = (
        db.session.query(
            TechnicalSkillScore.student_id,
            TechnicalSkillScore.technical_skill_category_id,
            TechnicalSkillScore.q1_score,
            TechnicalSkillScore.q2_score,
            TechnicalSkillScore.q3_score,
            TechnicalSkillScore.q4_score,
            TechnicalSkillScore.q5_score
        )
        .join(Student, TechnicalSkillScore.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (Student.student_id == StudentSemesterCluster.student_id) &
              (Student.part_id == StudentSemesterCluster.part_id))
        .filter(Student.part_id == part_id)
        .all()
    )

    if not scores:
        return []

    df = pd.DataFrame(scores, columns=[
        'student_id', 'category_id', 'q1', 'q2', 'q3', 'q4', 'q5'
    ])
    df['valid_score_count'] = df[['q1', 'q2', 'q3', 'q4', 'q5']].notnull().sum(axis=1)
    fully_null_students = df.groupby('student_id')['valid_score_count'].sum()
    fully_null_students = fully_null_students[fully_null_students == 0].index.tolist()
    df = df[~df['student_id'].isin(fully_null_students)]

    df['label'] = df['category_id'].astype(str) + '_'
    wide_df = df.pivot_table(
        index='student_id',
        columns='label',
        values=['q1', 'q2', 'q3', 'q4', 'q5'],
        fill_value=0
    )
    wide_df.columns = [f"{prefix}{q}" for q, prefix in wide_df.columns]
    clusterable_df = wide_df.dropna()
    if clusterable_df.shape[0] < 2:
        return []

    clusterable_df.index = clusterable_df.index.astype(str)  # ✅ important
    scaled = StandardScaler().fit_transform(clusterable_df)
    reduced = PCA(n_components=2).fit_transform(scaled)

    clusterable_df['x'] = reduced[:, 0]
    clusterable_df['y'] = reduced[:, 1]

    # ✅ Use cluster from DB
    cluster_map = {
        str(s.student_id): s.cluster_technical_skills
        for s in db.session.query(StudentSemesterCluster)
        .filter(StudentSemesterCluster.part_id == part_id)
        .filter(StudentSemesterCluster.cluster_technical_skills != None)
        .all()
    }

    clusterable_df['cluster'] = clusterable_df.index.map(cluster_map)
    clusterable_df = clusterable_df[clusterable_df['cluster'].notnull()]
    clusterable_df['cluster'] = clusterable_df['cluster'].astype(int)

    # 📊 Format output for Highcharts
    scatter_technical = []
    for label, group in clusterable_df.groupby('cluster'):
        scatter_technical.append({
            "name": f"Cluster {label}",
            "data": [
                {
                    "x": round(row.x, 2),
                    "y": round(row.y, 2),
                    "name": f"Student {idx}",
                    "student_id": idx
                }
                for idx, row in group.iterrows()
            ]
        })

    return scatter_technical


def get_technical_linkage_by_part(part_id):

    # 1️⃣ Query technical scores
    scores = (
        db.session.query(
            TechnicalSkillScore.student_id,
            TechnicalSkillScore.technical_skill_category_id,
            TechnicalSkillScore.q1_score,
            TechnicalSkillScore.q2_score,
            TechnicalSkillScore.q3_score,
            TechnicalSkillScore.q4_score,
            TechnicalSkillScore.q5_score
        )
        .join(Student, TechnicalSkillScore.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (TechnicalSkillScore.student_id == StudentSemesterCluster.student_id) &
              (StudentSemesterCluster.part_id == part_id))
        .filter(Student.part_id == part_id)
        .all()
    )

    if not scores:
        return None, None, None

    # 2️⃣ Prepare DataFrame
    df = pd.DataFrame(scores, columns=[
        'student_id', 'category_id', 'q1', 'q2', 'q3', 'q4', 'q5'
    ])
    df['valid_score_count'] = df[['q1', 'q2', 'q3', 'q4', 'q5']].notnull().sum(axis=1)
    df = df[df['valid_score_count'] > 0]

    df['label'] = df['category_id'].astype(str) + '_'
    pivot = df.pivot_table(index='student_id', columns='label', values=['q1', 'q2', 'q3', 'q4', 'q5'])
    pivot.columns = [f"{prefix}{q}" for q, prefix in pivot.columns]
    pivot = pivot.dropna()

    if pivot.shape[0] < 2:
        return None, None, None

    # 3️⃣ Standardize and Link
    scaled = StandardScaler().fit_transform(pivot)
    Z = linkage(scaled, method='ward', metric='euclidean')
    labels = pivot.index.astype(str).tolist()

    # 4️⃣ Cluster map from DB
    cluster_map = {
        str(s.student_id): s.cluster_technical_skills
        for s in db.session.query(StudentSemesterCluster)
        .filter(StudentSemesterCluster.part_id == part_id)
        .filter(StudentSemesterCluster.cluster_technical_skills != None)
        .all()
    }

    return Z, labels, cluster_map


def get_both_cluster_interpretations(part_id):
    """
    Generate interpretations for both (academic + technical) clustering results.
    Only includes students with both GPA and Technical scores.
    """
    try:
        scatter_response = get_both_scatter_by_part(part_id)
        scatter_data = scatter_response.get('scatter_data', [])
        if not scatter_data:
            return []

        cluster_stats = {}
        for point in scatter_data:
            x = point['x']
            y = point['y']
            cluster_id = point['cluster']

            # Skip if either academic or technical score is None
            if x is None or y is None:
                continue

            if cluster_id not in cluster_stats:
                cluster_stats[cluster_id] = {
                    'academic_scores': [],
                    'technical_scores': [],
                    'count': 0
                }

            cluster_stats[cluster_id]['academic_scores'].append(x)
            cluster_stats[cluster_id]['technical_scores'].append(y)
            cluster_stats[cluster_id]['count'] += 1

        interpretations = []
        for cluster_id, stats in cluster_stats.items():
            if not stats['academic_scores']:
                continue

            avg_academic = sum(stats['academic_scores']) / len(stats['academic_scores'])
            avg_technical = sum(stats['technical_scores']) / len(stats['technical_scores'])

            academic_level = "High" if avg_academic >= 3.0 else "Medium" if avg_academic >= 2.0 else "Low"
            technical_level = "High" if avg_technical >= 3.5 else "Medium" if avg_technical >= 2.5 else "Low"

            if academic_level == "High" and technical_level == "High":
                description = f"Cluster {cluster_id}: Excellent Overall Performance"
            elif academic_level == "High" and technical_level == "Medium":
                description = f"Cluster {cluster_id}: Strong Academic, Moderate Technical"
            elif academic_level == "High" and technical_level == "Low":
                description = f"Cluster {cluster_id}: Academic Focused, Needs Technical Support"
            elif academic_level == "Medium" and technical_level == "High":
                description = f"Cluster {cluster_id}: Technical Specialists"
            elif academic_level == "Medium" and technical_level == "Medium":
                description = f"Cluster {cluster_id}: Balanced Average Performance"
            elif academic_level == "Medium" and technical_level == "Low":
                description = f"Cluster {cluster_id}: Academic Leaning, Technical Growth Needed"
            elif academic_level == "Low" and technical_level == "High":
                description = f"Cluster {cluster_id}: Technical Experts, Academic Support Needed"
            elif academic_level == "Low" and technical_level == "Medium":
                description = f"Cluster {cluster_id}: Moderate Technical, Academic Improvement Needed"
            else:
                description = f"Cluster {cluster_id}: Requires Comprehensive Support"

            interpretations.append({
                'cluster_id': cluster_id,
                'academic_avg': round(avg_academic, 2),
                'technical_avg': round(avg_technical, 2),
                'academic_level': academic_level,
                'technical_level': technical_level,
                'student_count': stats['count'],
                'description': description
            })

        interpretations.sort(key=lambda x: x['cluster_id'])
        return interpretations

    except Exception as e:
        print(f"Error generating cluster interpretations: {e}")
        return []



def get_both_bubble_data_by_part(part_id):
    series = []

    prev_part = part_id - 1
    if prev_part < 1:
        return {"bubble": [], "score": None}

    # Step 1: Get actual distinct cluster numbers from DB
    cluster_values = db.session.query(StudentSemesterCluster.cluster_both)\
        .filter(StudentSemesterCluster.part_id == part_id)\
        .distinct().order_by(StudentSemesterCluster.cluster_both).all()

    cluster_numbers = [c[0] for c in cluster_values if c[0] is not None]

    for cluster in cluster_numbers:
        # Get students in this cluster & part
        student_ids = db.session.query(StudentSemesterCluster.student_id)\
            .filter(StudentSemesterCluster.cluster_both == cluster,
                    StudentSemesterCluster.part_id == part_id).subquery()

        # GPA from previous part only
        avg_gpa = db.session.query(func.avg(StudentPartGPA.gpa))\
            .filter(StudentPartGPA.student_id.in_(student_ids),
                    StudentPartGPA.part_id == prev_part)\
            .scalar() or 0

        # Technical score average: average per category, then mean of all categories
        categories = db.session.query(TechnicalSkillScore.technical_skill_category_id).\
            filter(TechnicalSkillScore.student_id.in_(student_ids),
                   TechnicalSkillScore.part_id == prev_part).\
            distinct().all()
        category_ids = [c[0] for c in categories]
        tech_avgs = []
        for cat_id in category_ids:
            q1 = db.session.query(func.avg(TechnicalSkillScore.q1_score)).\
                filter(TechnicalSkillScore.student_id.in_(student_ids),
                       TechnicalSkillScore.part_id == prev_part,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q2 = db.session.query(func.avg(TechnicalSkillScore.q2_score)).\
                filter(TechnicalSkillScore.student_id.in_(student_ids),
                       TechnicalSkillScore.part_id == prev_part,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q3 = db.session.query(func.avg(TechnicalSkillScore.q3_score)).\
                filter(TechnicalSkillScore.student_id.in_(student_ids),
                       TechnicalSkillScore.part_id == prev_part,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q4 = db.session.query(func.avg(TechnicalSkillScore.q4_score)).\
                filter(TechnicalSkillScore.student_id.in_(student_ids),
                       TechnicalSkillScore.part_id == prev_part,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q5 = db.session.query(func.avg(TechnicalSkillScore.q5_score)).\
                filter(TechnicalSkillScore.student_id.in_(student_ids),
                       TechnicalSkillScore.part_id == prev_part,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            scores = [q for q in [q1, q2, q3, q4, q5] if q is not None]
            if scores:
                tech_avgs.append(sum(scores) / len(scores))
        avg_tech = sum(tech_avgs) / len(tech_avgs) if tech_avgs else 0

        series.append({
            "name": f"Cluster {cluster}",
            "data": [
                {"name": "Academic", "value": round(avg_gpa, 2)},
                {"name": "Technical", "value": round(avg_tech, 2)}
            ]
        })

    return {
        "bubble": series,
        "score": None
    }


def get_both_scatter_by_part(part_id=2):
    # Get previous and current part
    sem_course = Part.query.filter_by(part_no=part_id - 1).first()  # previous part
    sem_student = Part.query.filter_by(part_no=part_id).first()    # current part
    if not sem_course or not sem_student:
        return {'scatter_data': []}

    # Only cluster records for the current part (student semester clusters)
    cluster_records = StudentSemesterCluster.query.filter_by(part_id=sem_student.part_id).all()
    
    # Build cluster_map excluding cluster -1 (unassigned)
    cluster_map = {
        (c.student_id, c.part_id): {'both': c.cluster_both}
        for c in cluster_records if c.cluster_both != -1
    }

    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    # Get GPA for students based on previous part courses
    course_part_id = sem_course.part_id
    student_grades = dict(
        Enrollment.query
        .join(Part, Enrollment.course.has(part_id=Part.part_id))
        .filter(Part.part_id == course_part_id)
        .with_entities(
            Enrollment.student_id,
            func.avg(grade_case).label('gpa')
        )
        .group_by(Enrollment.student_id)
        .all()
    )

    # Get technical skill scores for same students, filtered by previous part
    tech_scores = {}
    for student_id in student_grades.keys():
        categories = db.session.query(TechnicalSkillScore.technical_skill_category_id).\
            filter(TechnicalSkillScore.student_id == student_id,
                   TechnicalSkillScore.part_id == sem_course.part_id).\
            distinct().all()
        category_ids = [c[0] for c in categories]
        tech_avgs = []
        for cat_id in category_ids:
            q1 = db.session.query(func.avg(TechnicalSkillScore.q1_score)).\
                filter(TechnicalSkillScore.student_id == student_id,
                       TechnicalSkillScore.part_id == sem_course.part_id,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q2 = db.session.query(func.avg(TechnicalSkillScore.q2_score)).\
                filter(TechnicalSkillScore.student_id == student_id,
                       TechnicalSkillScore.part_id == sem_course.part_id,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q3 = db.session.query(func.avg(TechnicalSkillScore.q3_score)).\
                filter(TechnicalSkillScore.student_id == student_id,
                       TechnicalSkillScore.part_id == sem_course.part_id,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q4 = db.session.query(func.avg(TechnicalSkillScore.q4_score)).\
                filter(TechnicalSkillScore.student_id == student_id,
                       TechnicalSkillScore.part_id == sem_course.part_id,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            q5 = db.session.query(func.avg(TechnicalSkillScore.q5_score)).\
                filter(TechnicalSkillScore.student_id == student_id,
                       TechnicalSkillScore.part_id == sem_course.part_id,
                       TechnicalSkillScore.technical_skill_category_id == cat_id).scalar()
            scores = [q for q in [q1, q2, q3, q4, q5] if q is not None]
            if scores:
                tech_avgs.append(sum(scores) / len(scores))
        avg_tech = sum(tech_avgs) / len(tech_avgs) if tech_avgs else 0
        tech_scores[student_id] = avg_tech

    scatter_data = []
    for (student_id, part_id), cluster_info in cluster_map.items():
        x = student_grades.get(student_id)
        y = tech_scores.get(student_id)
        cluster = cluster_info['both']
        scatter_data.append({
            'student_id': student_id,
            'x': x,
            'y': y,
            'cluster': cluster
        })

    return {'scatter_data': scatter_data}



def get_both_linkage_by_part(part_id):
    # 1️⃣ Convert course grades to grade points
    grade_case = case(
        (Enrollment.course_grade == 'A+', 4.00),
        (Enrollment.course_grade == 'A', 4.00),
        (Enrollment.course_grade == 'A-', 3.67),
        (Enrollment.course_grade == 'B+', 3.33),
        (Enrollment.course_grade == 'B', 3.00),
        (Enrollment.course_grade == 'B-', 2.67),
        (Enrollment.course_grade == 'C+', 2.33),
        (Enrollment.course_grade == 'C', 2.00),
        (Enrollment.course_grade == 'C-', 1.67),
        (Enrollment.course_grade == 'D+', 1.33),
        (Enrollment.course_grade == 'D', 1.00),
        (Enrollment.course_grade == 'E', 0.67),
        (Enrollment.course_grade == 'F', 0.00),
        else_=None
    )

    # 2️⃣ Get academic performance (part_id - 1 courses, part_id students)
    academic_results = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            grade_case.label("grade_point")
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (Student.student_id == StudentSemesterCluster.student_id) &
              (Student.part_id == StudentSemesterCluster.part_id))
        .filter(Course.part_id == part_id - 1)
        .filter(Student.part_id == part_id)
        .all()
    )

    df_academic = pd.DataFrame(academic_results, columns=['student_id', 'course_code', 'grade_point'])
    pivot_academic = df_academic.pivot_table(index='student_id', columns='course_code', values='grade_point').fillna(0)

    # 3️⃣ Get technical skill scores (part_id - 1)
    tech_results = (
        db.session.query(
            TechnicalSkillScore.student_id,
            TechnicalSkillScore.technical_skill_category_id,
            TechnicalSkillScore.q1_score,
            TechnicalSkillScore.q2_score,
            TechnicalSkillScore.q3_score,
            TechnicalSkillScore.q4_score,
            TechnicalSkillScore.q5_score
        )
        .join(Student, TechnicalSkillScore.student_id == Student.student_id)
        .join(StudentSemesterCluster,
              (TechnicalSkillScore.student_id == StudentSemesterCluster.student_id) &
              (StudentSemesterCluster.part_id == part_id))
        .filter(Student.part_id == part_id)
        .filter(TechnicalSkillScore.part_id == part_id - 1)
        .all()
    )

    df_tech = pd.DataFrame(tech_results, columns=[
        'student_id', 'category_id', 'q1', 'q2', 'q3', 'q4', 'q5'
    ])
    df_tech['valid_score_count'] = df_tech[['q1', 'q2', 'q3', 'q4', 'q5']].notnull().sum(axis=1)
    df_tech = df_tech[df_tech['valid_score_count'] > 0]

    df_tech['label'] = df_tech['category_id'].astype(str) + '_'
    pivot_tech = df_tech.pivot_table(index='student_id', columns='label', values=['q1', 'q2', 'q3', 'q4', 'q5'])
    pivot_tech.columns = [f"{prefix}{q}" for q, prefix in pivot_tech.columns]

    # 4️⃣ Combine academic + technical
    combined = pivot_academic.join(pivot_tech, how='inner').dropna()
    if combined.shape[0] < 2:
        return None, None, None

    scaled = StandardScaler().fit_transform(combined)
    Z = linkage(scaled, method='ward', metric='euclidean')
    labels = combined.index.astype(str).tolist()

    # 5️⃣ Get cluster labels from DB
    cluster_map = {
        str(s.student_id): s.cluster_both
        for s in db.session.query(StudentSemesterCluster)
        .filter(StudentSemesterCluster.part_id == part_id)
        .filter(StudentSemesterCluster.cluster_both != None)
        .all()
    }

    return Z, labels, cluster_map

#####   End analysis-clustering.html    ####

#####   staff-staffs.html   ######

def get_all_staff_users():
    return Staff.query.filter(Staff.position != 'Admin').all()

def get_all_student_users():
    results = (
        db.session.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.email,
            Student.status,
            Student.phone_number,
            Student.picture,
            Student.part_id.label("student_part_id"),
            StudentSemesterCluster.cluster_both,
            StudentSemesterCluster.cluster_academic,
            StudentSemesterCluster.cluster_technical_skills,
        )
        .outerjoin(
            StudentSemesterCluster,
            (Student.student_id == StudentSemesterCluster.student_id) &
            (Student.part_id == StudentSemesterCluster.part_id)
        )
        .order_by(Student.part_id.asc())
        .all()
    )

    students = []
    for row in results:
        students.append({
            "id": row.student_id,
            "name": f"{row.first_name} {row.last_name}",
            "email": row.email,
            "status": row.status,
            "phone_number": row.phone_number,
            "picture": row.picture,
            "student_part": row.student_part_id,
            "cluster_both": row.cluster_both,
            "cluster_academic": row.cluster_academic,
            "cluster_technical_skills": row.cluster_technical_skills
        })

    return students


#####   End staff-staffs.html   #####


###    staff-students.html     ####

def get_filtered_students(part_id=None, cluster_type=None, cluster_no=None):
    query = (
        db.session.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.email,
            Student.status,
            Student.phone_number,
            Student.picture,
            Student.part_id.label("student_part"),
            StudentSemesterCluster.cluster_both,
            StudentSemesterCluster.cluster_academic,
            StudentSemesterCluster.cluster_technical_skills,
        )
        .outerjoin(
            StudentSemesterCluster,
            (Student.student_id == StudentSemesterCluster.student_id) &
            (Student.part_id == StudentSemesterCluster.part_id)
        )
    )

    if part_id:
        query = query.filter(Student.part_id == part_id)

    if cluster_type and cluster_no is not None:
        if cluster_type == "Academic + Technical":
            query = query.filter(StudentSemesterCluster.cluster_both == cluster_no)
        elif cluster_type == "Academic Performance":
            query = query.filter(StudentSemesterCluster.cluster_academic == cluster_no)
        elif cluster_type == "Technical Skills":
            query = query.filter(StudentSemesterCluster.cluster_technical_skills == cluster_no)

    query = query.order_by(Student.part_id).all()

    students = []
    for row in query:
        students.append({
            "id": row.student_id,
            "name": f"{row.first_name} {row.last_name}",
            "email": row.email,
            "status": row.status,
            "phone_number": row.phone_number,
            "picture": row.picture,
            "student_part": row.student_part,
            "cluster_both": row.cluster_both,
            "cluster_academic": row.cluster_academic,
            "cluster_technical_skills": row.cluster_technical_skills
        })

    return students


###     End staff-students.html


####    view-notification.html  ####

def get_notifications_by_staff_id(staff_id):
    return Notification.query.filter_by(staff_id=staff_id).order_by(Notification.time_sent.desc()).all()

def get_all_notifications():
    return Notification.query.order_by(Notification.time_sent.desc()).all()

def get_notifications_for_student(student_id):
    student_clusters = StudentSemesterCluster.query.filter_by(student_id=student_id).all()
    matched_notifications = []

    for sc in student_clusters:
        notifications = Notification.query.filter_by(part_id=sc.part_id).filter(
            db.or_(
                db.and_(
                    Notification.cluster_type == 'Academic Performance',
                    Notification.cluster_no == sc.cluster_academic
                ),
                db.and_(
                    Notification.cluster_type == 'Technical Skills',
                    Notification.cluster_no == sc.cluster_technical_skills
                ),
                db.and_(
                    Notification.cluster_type == 'Academic + Technical',
                    Notification.cluster_no == sc.cluster_both,
                )
            )
        ).all()
        matched_notifications.extend(notifications)

    # Remove duplicates
    unique_notifications = {n.notification_id: n for n in matched_notifications}.values()

    # Format time
    formatted_notifications = []
    for n in unique_notifications:
        date_sent, time_sent = format_time_sent(n.time_sent)
        formatted_notifications.append({
            "notification_id": n.notification_id,
            "subject": n.subject,
            "message": n.message,
            "staff": n.staff,
            "date_sent": date_sent,
            "time_sent": time_sent,
        })

    # Sort by time descending
    return sorted(formatted_notifications, key=lambda x: (x['date_sent'], x['time_sent']), reverse=True)


def save_notification(staff_id, subject, message, part_id, cluster_type, cluster_no):
    malaysia_time = pytz.timezone('Asia/Kuala_Lumpur')

    notification = Notification(
        staff_id=staff_id,
        subject=subject,
        message=message,
        time_sent = datetime.now(malaysia_time),
        part_id=part_id,
        cluster_type=cluster_type,
        cluster_no=cluster_no,
    )
    db.session.add(notification)
    db.session.commit()
    
####    End view-notification.html      ####

##########    END READ    ##############



##########      UPDATE      ##############

def change_user_password(user, current_password, new_password, confirm_password):
    # Check if the current password is correct
    if not bcrypt.check_password_hash(user.password, current_password):
        flash("Current password is incorrect", "danger")
        return False

    # Check if the new password matches the confirm password
    if new_password != confirm_password:
        flash("New password and confirm password do not match", "danger")
        return False

    # Validate new password strength
    if len(new_password) < 5:
        flash("New password should be at least 5 characters long", "danger")
        return False

    # Hash the new password and update the user record
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password
    db.session.commit()

    flash("Your password has been successfully changed!", "success")
    return True


def send_change_password_email(email):
    msg = Message(
        subject="Your Password Has Been Changed",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg.body = (
        f"Hello,\n\n"
        f"This is to confirm that your account password was successfully changed.\n\n"
        f"If you did not perform this change, please contact the Skillytics support team immediately.\n\n"
        f"Best regards,\n"
        f"Skillytics Team"
    )

    mail.send(msg)


def update_profile(user, phone_number, address):
    # Update the user profile with the new information
    try:
        # Update the fields
        user.phone_number = phone_number
        user.address = address

        # Commit the changes to the database
        db.session.commit()

        flash("Your profile has been successfully updated!", "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating your profile: {e}", "danger")
        return False
    

def update_picture(user, picture):
    # Update the user profile with the new information
    try:
        # Update the field
        user.picture = picture

        # Commit the changes to the database
        db.session.commit()

        flash("Your picture has been successfully updated!", "success")
        return True  # Indicates success
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating your profile: {e}", "danger")
        return False


def update_student_ts_score(student_id, ts_category_id, updated_scores, part_id):
    try:
        # Try to find existing record for the specific part
        ts_score = db.session.query(TechnicalSkillScore).filter_by(
            student_id=student_id,
            technical_skill_category_id=ts_category_id,
            part_id=part_id
        ).first()

        if ts_score:
            # Update existing fields
            if 'q1_score' in updated_scores:
                ts_score.q1_score = updated_scores['q1_score']
            if 'q2_score' in updated_scores:
                ts_score.q2_score = updated_scores['q2_score']
            if 'q3_score' in updated_scores:
                ts_score.q3_score = updated_scores['q3_score']
            if 'q4_score' in updated_scores:
                ts_score.q4_score = updated_scores['q4_score']
            if 'q5_score' in updated_scores:
                ts_score.q5_score = updated_scores['q5_score']
        else:
            # Create new record with all fields and part_id
            ts_score = TechnicalSkillScore(
                student_id=student_id,
                technical_skill_category_id=ts_category_id,
                part_id=part_id,
                q1_score=updated_scores.get('q1_score', 0),
                q2_score=updated_scores.get('q2_score', 0),
                q3_score=updated_scores.get('q3_score', 0),
                q4_score=updated_scores.get('q4_score', 0),
                q5_score=updated_scores.get('q5_score', 0)
            )
            db.session.add(ts_score)

        db.session.commit()
        return True

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return False

def check_and_update_ts_completion(student_id):
    required_categories = {1, 2, 3}  # Adjust if needed

    student = Student.query.get(student_id)
    if not student:
        return False

    # Use student's current part_id
    current_part_id = student.part_id

    # Get scores only for the required categories and current part
    scores = TechnicalSkillScore.query.filter(
        TechnicalSkillScore.student_id == student_id,
        TechnicalSkillScore.part_id == current_part_id,
        TechnicalSkillScore.technical_skill_category_id.in_(required_categories)
    ).all()

    # Initialize category completion mapping
    category_completion = {cat_id: False for cat_id in required_categories}

    for score in scores:
        if score.technical_skill_category_id in required_categories:
            all_answered = all([
                score.q1_score is not None,
                score.q2_score is not None,
                score.q3_score is not None,
                score.q4_score is not None,
                score.q5_score is not None
            ])
            category_completion[score.technical_skill_category_id] = all_answered

    if all(category_completion.values()):
        if student.status != "Completed":
            student.status = "Completed"
            db.session.commit()

        check_and_notify_low_technical_average(current_part_id)
        
        return True

    return False


##########    END UPDATE    ##############



##########      DELETE      ##############

def delete_feedback(feedback_id):
    try:
        # Convert feedback_id to integer
        feedback_id = int(feedback_id)
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            db.session.delete(feedback)
            db.session.commit()
            return True
        return False
    except (ValueError, TypeError) as e:
        print(f"Error converting feedback_id: {str(e)}")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting feedback: {str(e)}")
        return False
    
def delete_notification(notification_id):
    try:
        # Convert notification_id to integer
        notification_id = int(notification_id)
        notification = Notification.query.get(notification_id)
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False
    except (ValueError, TypeError) as e:
        print(f"Error converting notification_id: {str(e)}")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting notification: {str(e)}")
        return False

##########    END DELETE    ##############

def get_academic_cluster_interpretations(part_id):
    try:
        # Using the same grade point calculation as the bubble chart
        grade_case = case(
            (Enrollment.course_grade == 'A+', 4.00),
            (Enrollment.course_grade == 'A', 4.00),
            (Enrollment.course_grade == 'A-', 3.67),
            (Enrollment.course_grade == 'B+', 3.33),
            (Enrollment.course_grade == 'B', 3.00),
            (Enrollment.course_grade == 'B-', 2.67),
            (Enrollment.course_grade == 'C+', 2.33),
            (Enrollment.course_grade == 'C', 2.00),
            (Enrollment.course_grade == 'C-', 1.67),
            (Enrollment.course_grade == 'D+', 1.33),
            (Enrollment.course_grade == 'D', 1.00),
            (Enrollment.course_grade == 'E', 0.67),
            (Enrollment.course_grade == 'F', 0.00),
            else_=None
        )

        # Get all grades for students in the specified part, based on their previous part's performance
        results = (
            db.session.query(
                Enrollment.student_id,
                grade_case.label('grade_point'),
                StudentSemesterCluster.cluster_academic
            )
            .join(Course, Enrollment.course_code == Course.course_code)
            .join(Student, Enrollment.student_id == Student.student_id)
            .join(StudentSemesterCluster, 
                  (Student.student_id == StudentSemesterCluster.student_id) &
                  (Student.part_id == StudentSemesterCluster.part_id))
            .filter(Student.part_id == part_id)
            .filter(Course.part_id == part_id - 1)  # Grades from the previous part
            .filter(StudentSemesterCluster.cluster_academic.isnot(None))
            .filter(grade_case.isnot(None))
            .all()
        )

        if not results:
            return []

        # Group grades and students by cluster
        cluster_data = defaultdict(lambda: {'grades': [], 'students': set()})
        for student_id, grade_point, cluster_id in results:
            cluster_data[cluster_id]['grades'].append(grade_point)
            cluster_data[cluster_id]['students'].add(student_id)

        interpretations = []
        for cluster_id, data in sorted(cluster_data.items()):
            if not data['grades']:
                continue

            # Calculate average academic score for the cluster
            avg_academic = sum(data['grades']) / len(data['grades'])
            student_count = len(data['students'])
            
            # Determine performance level based on the average
            if avg_academic >= 3.5:
                academic_level = "Outstanding"
                description = f"Cluster {cluster_id}: First Class"
            elif 3.0 <= avg_academic < 3.5:
                academic_level = "Very Good"
                description = f"Cluster {cluster_id}: Second Class Upper"
            elif 2.5 <= avg_academic < 3.0:
                academic_level = "Fair"
                description = f"Cluster {cluster_id}: Second Class Lower"
            elif 2.0 <= avg_academic < 2.5:
                academic_level = "Pass"
                description = f"Cluster {cluster_id}: Third Class" 
            elif avg_academic < 2.0:
                academic_level = "Academic Failure"
                description = f"Cluster {cluster_id}: Fail"

            interpretations.append({
                'cluster_id': cluster_id,
                'academic_avg': round(avg_academic, 2),
                'academic_level': academic_level,
                'student_count': student_count,
                'description': description
            })
            
        return interpretations

    except Exception as e:
        print(f"Error generating academic cluster interpretations: {e}")
        return []

def get_technical_cluster_interpretations(part_id):
    try:
        # Replicating the logic from get_technical_bubble_data_by_part
        # to ensure consistency, as requested.
        scores = (
            db.session.query(
                TechnicalSkillScore.student_id,
                StudentSemesterCluster.cluster_technical_skills,
                TechnicalSkillScore.q1_score,
                TechnicalSkillScore.q2_score,
                TechnicalSkillScore.q3_score,
                TechnicalSkillScore.q4_score,
                TechnicalSkillScore.q5_score
            )
            .join(StudentSemesterCluster,
                  (TechnicalSkillScore.student_id == StudentSemesterCluster.student_id) &
                  (StudentSemesterCluster.part_id == part_id))
            .filter(StudentSemesterCluster.cluster_technical_skills.isnot(None))
            .all()
        )

        if not scores:
            return []

        # Group scores and students by cluster
        cluster_data = defaultdict(lambda: {'scores': [], 'students': set()})

        for student_id, cluster_id, q1, q2, q3, q4, q5 in scores:
            q_scores = [q for q in [q1, q2, q3, q4, q5] if q is not None]
            if not q_scores:
                continue
            
            # Calculate the average score for this particular entry
            avg_entry_score = sum(q_scores) / len(q_scores)
            
            cluster_data[cluster_id]['scores'].append(avg_entry_score)
            cluster_data[cluster_id]['students'].add(student_id)

        interpretations = []
        for cluster_id, data in sorted(cluster_data.items()):
            if not data['scores']:
                continue

            # Calculate the overall average technical score for the cluster
            # This calculation now matches the logic for the bubble chart's cluster average.
            avg_technical = sum(data['scores']) / len(data['scores'])
            student_count = len(data['students'])

            # Determine performance level
            if avg_technical > 4.5:
                technical_level = "Excellent"
                description = f"Cluster {cluster_id}: Mastery"
            elif 3.5 < avg_technical <= 4.5:
                technical_level = "Proficient"
                description = f"Cluster {cluster_id}: Advanced"
            elif 2.5 < avg_technical <= 3.5:
                technical_level = "Competent"
                description = f"Cluster {cluster_id}: Skilled"
            elif 1.5 < avg_technical <= 2.5:
                technical_level = "Developing"
                description = f"Cluster {cluster_id}: Emerging"
            else:
                technical_level = "Beginner"
                description = f"Cluster {cluster_id}: Novice"

            interpretations.append({
                'cluster_id': cluster_id,
                'technical_avg': round(avg_technical, 2),
                'technical_level': technical_level,
                'student_count': student_count,
                'description': description
            })

        return interpretations

    except Exception as e:
        print(f"Error generating technical cluster interpretations: {e}")
        return []