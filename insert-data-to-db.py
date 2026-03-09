import pandas as pd
import numpy as np
import random

from skillytics.models import (
    Part, Course, TechnicalSkillCategory, Staff, Student, Enrollment, TechnicalSkillScore, StudentPartGPA
)
from skillytics import db, bcrypt

def create_db_and_load_data():
    print("📦 Creating database tables and loading data ...")
    db.create_all()

    clean_data = 'C:/Users/aqima/OneDrive/Desktop/PROJECT/skillytics/data/clean-data.csv'
    df = pd.read_csv(clean_data)

    df = df.replace({np.nan: None})

    # Convert student_id to int
    try:
        df['student_id'] = df['student_id'].astype(int)
    except Exception as e:
        print(f"Warning converting student_id to int: {e}")

    return df


def insert_part_data():
    part_id_counter = 1
    total_semester = 7
    
    for part_no in range(1, total_semester + 1):
        if not db.session.get(Part, part_id_counter):
            part = Part(part_id=part_id_counter, part_no=part_no)
            db.session.add(part)
        part_id_counter += 1

    db.session.commit()
    print("✅ Parts inserted sucessfully.")


def insert_course_data():
    course_data = [
        # Add all courses as tuples: (code, name, part_id, credit_hour)
        ('CSC402', 'PROGRAMMING I', 1, 3),
        ('CSC413', 'INTRODUCTION TO INTERACTIVE MULTIMEDIA', 1, 3),
        ('CSC429', 'COMPUTER ORGANIZATION AND ARCHITECTURE', 1, 3),
        ('CTU552', 'PHILOSOPHY AND CURRENT ISSUES', 1, 2),
        ('C1', 'CO-CURRICULAR (E.G., HBU111, ETC)', 1, 1),
        ('ICT450', 'DATABASE DESIGN AND DEVELOPMENT', 1, 3),
        ('MAT406', 'FOUNDATION MATHEMATICS', 1, 3),

        ('CSC404', 'PROGRAMMING II', 2, 3),
        ('CTU554', 'VALUES AND CIVILIZATION II', 2, 2),
        ('C2', 'CO-CURRICULAR (E.G., HBU121, ETC)', 2, 1),
        ('ICT502', 'DATABASE ENGINEERING', 2, 3),
        ('ITT400', 'INTRODUCTION TO DATA COMMUNICATION AND NETWORKING', 2, 3),
        ('MAT421', 'CALCULUS I', 2, 3),
        ('STA416', 'APPLIED PROBABILITY AND STATISTICS', 2, 3),

        ('CSC435', 'OBJECT ORIENTED PROGRAMMING', 3, 3),
        ('CSC510', 'DISCRETE STRUCTURES', 3, 3),
        ('CSC520', 'PRINCIPLES OF OPERATING SYSTEMS', 3, 3),
        ('CSC583', 'ARTIFICIAL INTELLIGENCE ALGORITHMS', 3, 3),
        ('ELC501', 'ENGLISH FOR CRITICAL ACADEMIC READING', 3, 2),
        ('C3', 'CO-CURRICULAR (E.G., HBU131, ETC)', 3, 1),
        ('MAT423', 'LINEAR ALGEBRA I', 3, 3),
        ('FL1', 'FOREIGN LANGUAGE (E.G., TMC401, ETC)', 3, 2),

        ('CSC508', 'DATA STRUCTURES', 4, 3),
        ('CSC569', 'PRINCIPLES OF COMPILERS', 4, 3),
        ('CSC577', 'SOFTWARE ENGINEERING - THEORIES AND PRINCIPLES', 4, 3),
        ('CSC584', 'ENTERPRISE PROGRAMMING', 4, 3),
        ('ELC650', 'ENGLISH FOR PROFESSIONAL INTERACTION', 4, 2),
        ('E1', 'ELECTIVE (ISP565 - DATA MINING, CSC566 - IMAGE PROCESSING)', 4, 3),
        ('FL2', 'FOREIGN LANGUAGE (E.G., TMC451, ETC)', 4, 2),

        ('CSC580', 'PARALLEL PROCESSING', 5, 3),
        ('CSC645', 'ALGORITHM ANALYSIS AND DESIGN', 5, 3),
        ('CSC649', 'SPECIAL TOPICS IN COMPUTER SCIENCE', 5, 3),
        ('CSP600', 'PROJECT FORMULATION', 5, 3),
        ('ENT600', 'TECHNOLOGY ENTREPRENEURSHIP', 5, 3),
        ('E2', 'ELECTIVE (STA404 - STATISTICS FOR BUSINESS AND SOCIAL SCIENCES, CSC557 - MOBILE PROGRAMMING)', 5, 3),
        ('FL3', 'FOREIGN LANGAUGE (E.G., TMC501, ETC)', 5, 2),

        ('E3', 'ELECTIVE (DSC651 - DATA REPRESENTATION AND REPORTING TECHNIQUES, CSC683 - GAME DEVELOPMENT)', 6, 3),
        ('CSC662', 'COMPUTER SECURITY', 6, 3),
        ('E4', 'ELECTIVE (ISP610 - BUSINESS DATA ANALYTICS, CSC574 - DYNAMIC WEB APPLICATION DEVELOPMENT)', 6, 3),
        ('CSC650', 'PROJECT', 6, 6),
        ('ICT652', 'ETHICAL, SOCIAL, AND PROFESSIONAL ISSUES IN ICT', 6, 3),
    ]

    for code, name, part_id, credit_hour in course_data:
        if not db.session.get(Course, code):
            course = Course(course_code=code, course_name=name, part_id=part_id, credit_hour=credit_hour)
            db.session.add(course)
    db.session.commit()
    print("✅ Courses inserted.")


def insert_technical_data():
    categories = ['Digital Literacy', 'Programming', 'Data Science and Machine Learning']
    for ts_type in categories:
        if not TechnicalSkillCategory.query.filter_by(ts_type=ts_type).first():
            db.session.add(TechnicalSkillCategory(ts_type=ts_type))
    db.session.commit()
    print("✅ Technical skill categories inserted.")


def insert_admin_data():
    gender = 'Female'
    picture = 'default-admin.svg'
    first = 'Huda'
    last = 'Nik Zulkipli'
    email = 'aqiman1312@gmail.com'
    phone = f"01{random.randint(0,9)}-{random.randint(1000000,9999999)}"
    password = bcrypt.generate_password_hash("123").decode('utf-8')

    last_staff = Staff.query.order_by(Staff.staff_id.desc()).first()
    next_id = 100000 if not last_staff else last_staff.staff_id + 1

    admin = Staff(
        staff_id=next_id,
        first_name=first,
        last_name=last,
        email=email,
        gender=gender,
        position="Admin",
        phone_number=phone,
        address="Universiti Teknologi MARA",
        institution_name="UiTM Kampus Jasin",
        faculty_name="FSKM",
        password=password,
        picture=picture
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin inserted.")

def insert_coordinator_data():
    gender = 'Female'
    picture = 'default-staff-female.png'
    first = 'Feirusz'
    last = 'Ahmad Fesol'
    email = 'aqimanfauzi@gmail.com'
    phone = f"01{random.randint(0,9)}-{random.randint(1000000,9999999)}"
    password = bcrypt.generate_password_hash("123").decode('utf-8')

    last_staff = Staff.query.order_by(Staff.staff_id.desc()).first()
    next_id = 100000 if not last_staff else last_staff.staff_id + 1

    coordinator = Staff(
        staff_id=next_id,
        first_name=first,
        last_name=last,
        email=email,
        gender=gender,
        position="Coordinator",
        phone_number=phone,
        address="Universiti Teknologi MARA",
        institution_name="UiTM Kampus Jasin",
        faculty_name="FSKM",
        password=password,
        picture=picture
    )
    db.session.add(coordinator)
    db.session.commit()
    print("✅ Coordinator inserted.")

def insert_random_staff_data(n=5):
    male_names = ['Ahmad', 'Aqil', 'Danial', 'Faiz', 'Hakim', 'Irfan']
    female_names = ['Aisyah', 'Nurul', 'Siti', 'Zulaikha', 'Farah', 'Amira']
    last_names = ['Ismail', 'Rahman', 'Hassan', 'Yusof', 'Abdullah', 'Khalid']
    positions = ['Lecturer', 'Senior Lecturer', 'Advisor']
    genders = ['Male', 'Female']

    for _ in range(n):
        gender = random.choice(genders)
        picture = 'default-staff-male.png' if gender == 'Male' else 'default-staff-female.png'
        first = random.choice(male_names if gender == 'Male' else female_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}{random.randint(10,99)}@staff.uitm.edu.my"
        phone = f"01{random.randint(0,9)}-{random.randint(1000000,9999999)}"
        password = bcrypt.generate_password_hash("123").decode('utf-8')

        last_staff = Staff.query.order_by(Staff.staff_id.desc()).first()
        next_id = 100000 if not last_staff else last_staff.staff_id + 1

        staff = Staff(
            staff_id=next_id,
            first_name=first,
            last_name=last,
            email=email,
            gender=gender,
            position=random.choice(positions),
            phone_number=phone,
            address="Universiti Teknologi MARA",
            institution_name="UiTM Kampus Jasin",
            faculty_name="FSKM",
            password=password,
            picture=picture
        )
        if not Staff.query.filter_by(email=staff.email).first():
            db.session.add(staff)

    db.session.commit()
    print(f"✅ {n} staff members inserted.")


def insert_student_data(df):
    students_to_insert = []
    for _, row in df.iterrows():
        if db.session.get(Student, row['student_id']) or Student.query.filter_by(email=row['email']).first():
            continue

        hashed_pw = bcrypt.generate_password_hash(str(row['password'])).decode('utf-8')
        gender = row['gender']
        picture = 'default-student-male.png' if str(gender).lower() == 'male' else 'default-student-female.png'

        student = Student(
            student_id=int(row['student_id']),
            email=row['email'],
            password=hashed_pw,
            first_name=row['first_name'],
            last_name=row['last_name'],
            gender=gender,
            phone_number=row['phone_number'],
            address=row['address'],
            part_id=int(row['part']),
            institution_name=row['institution_name'],
            faculty_name=row['faculty_name'],
            program_code=row['program_code'],
            status=row['status'],
            picture=picture
        )
        students_to_insert.append(student)

    db.session.bulk_save_objects(students_to_insert)
    db.session.commit()
    print(f"✅ Inserted {len(students_to_insert)} students.")


def insert_enrollment_data(df):
    # Fetch course codes from database for validation
    course_codes = [c[0] for c in db.session.query(Course.course_code).all()]

    for _, row in df.iterrows():
        student_id = int(row['student_id'])
        part_id = int(row['part'])

        for course_code in course_codes:
            course_grade = row.get(course_code)
            if course_grade and pd.notna(course_grade):
                if not Enrollment.query.filter_by(student_id=student_id, course_code=course_code).first():
                    enrollment = Enrollment(
                        student_id=student_id,
                        course_code=course_code,
                        part_id=part_id,
                        course_grade=course_grade.strip()
                    )
                    db.session.add(enrollment)
    db.session.commit()
    print("✅ Enrollments inserted.")


def insert_technical_score_data(df):
    skill_column_map = {
        'Digital Literacy': [f'dl_{i}_p{j}' for j in range(1, 7) for i in range(1, 6)],
        'Programming': [f'prog_{i}_p{j}' for j in range(1, 7) for i in range(1, 6)],
        'Data Science and Machine Learning': [f'ds_{i}_p{j}' for j in range(1, 7) for i in range(1, 6)]
    }

    category_map = {
        cat.ts_type: cat.technical_skill_category_id
        for cat in TechnicalSkillCategory.query.all()
    }

    for _, row in df.iterrows():
        student_id = int(row['student_id'])

        for ts_type, cols in skill_column_map.items():
            category_id = category_map.get(ts_type)
            if not category_id:
                print(f"❌ Missing category in DB: {ts_type}")
                continue

            for part_id in range(1, 7):
                # Get the 5 questions for this part
                part_cols = [col for col in cols if col.endswith(f"_p{part_id}")]

                # Ensure columns exist in dataframe
                valid_part_cols = [col for col in part_cols if col in df.columns]
                scores = [row.get(col) for col in valid_part_cols]

                # Only insert if at least one score is not NaN
                if any(pd.notna(score) for score in scores):
                    score_entry = TechnicalSkillScore(
                        student_id=student_id,
                        part_id=part_id,
                        technical_skill_category_id=category_id,
                        q1_score=int(scores[0]) if len(scores) > 0 and pd.notna(scores[0]) else None,
                        q2_score=int(scores[1]) if len(scores) > 1 and pd.notna(scores[1]) else None,
                        q3_score=int(scores[2]) if len(scores) > 2 and pd.notna(scores[2]) else None,
                        q4_score=int(scores[3]) if len(scores) > 3 and pd.notna(scores[3]) else None,
                        q5_score=int(scores[4]) if len(scores) > 4 and pd.notna(scores[4]) else None
                    )
                    db.session.add(score_entry)

    db.session.commit()
    print("✅ Technical skill scores inserted.")



def insert_student_gpa_data(df):
    grade_map = {
        'A+': 4.00, 'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00, 'C-': 1.67,
        'D+': 1.33, 'D': 1.00, 'E': 0.67,
        'F': 0.00
    }

    for _, row in df.iterrows():
        student_id = int(row['student_id'])
        current_part = int(row['part'])

        # Calculate GPA only for completed parts
        for part_id in range(1, current_part):
            # Get courses for this part
            courses = Course.query.filter_by(part_id=part_id).all()
            total_weighted_points = 0.0
            total_credits = 0.0

            for course in courses:
                grade = row.get(course.course_code)
                if grade and grade in grade_map:
                    grade_point = grade_map[grade]
                    total_weighted_points += grade_point * (course.credit_hour or 0)
                    total_credits += course.credit_hour or 0
            
            # Calculate GPA if total_credits > 0
            if total_credits > 0:
                gpa = round(total_weighted_points / total_credits, 2)
                gpa_entry = StudentPartGPA(
                    student_id=student_id,
                    part_id=part_id,
                    gpa=gpa
                )
                db.session.add(gpa_entry)

    db.session.commit()
    print("✅ Student GPA data inserted based on academic grades.")


if __name__ == "__main__":
    from skillytics import create_app
    from skillytics.clustering_utils import (
        perform_academic_clustering_by_part,
        perform_technical_clustering_by_part,
        perform_both_clustering_by_part
    )

    app = create_app()
    with app.app_context():
        df = create_db_and_load_data()

        insert_part_data()
        insert_course_data()
        insert_technical_data()

        insert_admin_data()
        insert_coordinator_data()
        insert_random_staff_data(n=5)

        insert_student_data(df)
        insert_enrollment_data(df)
        insert_technical_score_data(df)
        insert_student_gpa_data(df)

        for part in range(1, 8):
            perform_academic_clustering_by_part(part)
            perform_technical_clustering_by_part(part)
            perform_both_clustering_by_part(part)
