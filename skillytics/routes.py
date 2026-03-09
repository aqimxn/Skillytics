from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, jsonify, current_app
from skillytics.models import Staff, Student, Notification, Feedback
from flask_login import current_user, logout_user, login_required
from skillytics.utils import is_student, is_staff, is_admin, format_time_sent, staffs_only, admin_only, student_only, authenticated
from skillytics.clustering_utils import perform_academic_clustering_by_part, perform_technical_clustering_by_part, perform_both_clustering_by_part
from werkzeug.utils import secure_filename
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io

##      READ    ##
from skillytics.CRUD import (
    get_all_total_students,
    get_all_academic_gauge_chart,
    get_all_technical_gauge_chart,
    get_all_student_status,
    count_students_by_part,
    gauge_academic_by_part,
    gauge_technical_by_part,
    gauge_technical_by_current_part,
    get_student_status_pie_data_by_part,

    # ADD
    update_last_online,
    get_relative_last_online,
    save_feedback,
    add_staff_to_db,
    send_staff_email,
    send_feedback_email,
    send_change_password_email,
    save_notification,

    # READ
    get_all_staff_users,
    get_all_student_users,
    get_student_gpa_all_parts,
    get_student_gpa_all_parts_for_staffs,
    get_student_cgpa,
    get_barchart_academic_student,
    get_barchart_academic_student_for_staffs,
    get_technical_scores_by_all_parts,
    get_accumulated_technical_scores_by_all_parts,
    get_barchart_academic_staff,
    get_barchart_technical_staff,
    get_filtered_students,

    get_both_cluster_interpretations,
    get_both_bubble_data_by_part,
    get_both_scatter_by_part,
    get_both_linkage_by_part,
    get_academic_bubble_data_by_part,
    get_academic_scatter_pca_by_part,
    get_technical_bubble_data_by_part,
    get_technical_scatter_pca_by_part,

    get_academic_linkage_by_part,
    get_technical_linkage_by_part,

    get_all_notifications,
    get_notifications_by_staff_id,
    get_notifications_for_student,

    # UPDATE
    update_picture,
    update_profile,
    change_user_password,
    get_student_ts_score_by_ts,
    update_student_ts_score,
    check_and_update_ts_completion,

    # DELETE
    delete_notification,
    delete_feedback
)

main = Blueprint('main', __name__)

############        USER        ##############

@main.route('/')
@main.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@login_required
@main.route('/dashboard', methods=['GET'])
def dashboard():

    check = authenticated()
    if check:
        return check

    part_id = request.args.get('part', type=int)
    last_online_display = get_relative_last_online(current_user.last_online)

    # ---------- STAFF / ADMIN ----------
    if is_staff() or is_admin():

        courses_barchart = []
        grades_barchart = []
        technical_categories = []
        technical_scores = []

        if part_id:
            total_students = count_students_by_part(part_id)
            all_academic_gauge = gauge_academic_by_part(part_id)
            all_technical_gauge = gauge_technical_by_part(part_id)
            all_student_status = get_student_status_pie_data_by_part(part_id)
            technicalGauge_current_part = gauge_technical_by_current_part(part_id)

            if part_id > 1:
                prev_part = part_id - 1
                # Academic bar chart
                barchart_data = get_barchart_academic_staff(prev_part)
                courses_barchart = [row[0] for row in barchart_data]
                grades_barchart = [float(row[1]) if row[1] is not None else 0 for row in barchart_data]

                # Technical bar chart
                tech_data = get_barchart_technical_staff(prev_part)
                technical_categories = [row[0] for row in tech_data]
                technical_scores = [float(row[1]) for row in tech_data]

        else:
            # All-parts data
            total_students = get_all_total_students()
            all_academic_gauge = get_all_academic_gauge_chart()
            all_technical_gauge = get_all_technical_gauge_chart()
            all_student_status = get_all_student_status()
            technicalGauge_current_part = 0

        # AJAX response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {
                "student_count": total_students,
                "academic_score": all_academic_gauge,
                "technical_score": all_technical_gauge,
                "technical_score_current_part": technicalGauge_current_part,
                "pie_chart_data": all_student_status,
                "courses_barchart": courses_barchart,
                "grades_barchart": grades_barchart,
                "technical_categories": technical_categories,
                "technical_scores": technical_scores
            }

        return render_template(
            'staff-dashboard.html',
            total_students=total_students,
            all_academic_gauge=all_academic_gauge,
            all_technical_gauge=all_technical_gauge,
            all_student_status=all_student_status,
            last_online_display=last_online_display,
            technicalGauge_current_part=technicalGauge_current_part,
            courses_barchart=courses_barchart,
            grades_barchart=grades_barchart,
            technical_categories=technical_categories,
            technical_scores=technical_scores
        )

    # ---------- STUDENT ----------
    elif is_student():
        student_id = current_user.student_id
        current_part = current_user.part.part_no if current_user.part else 1

        # GPA data
        cgpa = get_student_cgpa(student_id)
        gpa_data = get_student_gpa_all_parts(current_part)
        gpa_points = [{"x": p[0], "y": float(p[1])} for p in gpa_data if p[1] is not None]

        # Academic bar chart (previous part)
        prev_part = max(1, current_part - 1)
        academic_data = get_barchart_academic_student(part_no=prev_part)
        courses = [c[0] for c in academic_data] if academic_data else []
        grades = [float(c[1]) if c[1] is not None else 0 for c in academic_data] if academic_data else []
        letters = [c[2] for c in academic_data] if academic_data else []

        # Technical skill scores
        technical_scores_by_part = get_technical_scores_by_all_parts(student_id, current_part)
        tech_categories = next((info['categories'] for info in technical_scores_by_part.values() if info['categories']), [])

        accumulated_technical_scores_by_part = get_accumulated_technical_scores_by_all_parts(student_id, current_part)
        accumulated_tech_categories = next((info['categories'] for info in accumulated_technical_scores_by_part.values() if info['categories']), [])

        return render_template(
            'student-dashboard.html',
            last_online_display=last_online_display,
            cgpa=cgpa,
            gpa_points=gpa_points,
            courses=courses,
            grades=grades,
            letters=letters,
            max_part_for_filter=prev_part,
            technical_scores_by_part=technical_scores_by_part,
            tech_categories=tech_categories,
            accumulated_technical_scores_by_part=accumulated_technical_scores_by_part,
            accumulated_tech_categories=accumulated_tech_categories
        )

    # ---------- Unauthorized ----------
    return redirect(url_for("auth.user_login"))

@login_required
@main.route('/student/academic-data', methods=['GET'])
def get_academic_data():

    check = student_only()
    if check:
        return check
           
    part_no = request.args.get('part', type=int)

    # Default: current part if none selected or all parts (return combined)
    if not part_no:
        part_no = current_user.part.part_no

    academic_data = get_barchart_academic_student(part_no)

    courses = [x[0] for x in academic_data]
    grades = [x[1] for x in academic_data]
    letters = [x[2] for x in academic_data]  # Add this line to extract letters

    return jsonify({
        'courses': courses, 
        'grades': grades,
        'letters': letters  # Add this line to include letters in response
    })


## for staffs
@login_required
@main.route('/student/academic-data-details', methods=['GET'])
def get_academic_data_for_staffs():

    check = staffs_only()
    if check:
        return check
           
    part_no = request.args.get('part', type=int)
    selected_student_id = request.args.get("student_id")
    selected_student = Student.query.get(selected_student_id)

    # Default: current part if none selected or all parts (return combined)
    if not part_no:
        part_no = selected_student.part.part_no

    academic_data = get_barchart_academic_student_for_staffs(selected_student, part_no)

    courses = [x[0] for x in academic_data]
    grades = [x[1] for x in academic_data]
    letters = [x[2] for x in academic_data]  # Add this line to extract letters

    return jsonify({
        'courses': courses, 
        'grades': grades,
        'letters': letters  # Add this line to include letters in response
    })


@main.route('/logout')
def logout():

    if current_user.is_authenticated:
        update_last_online(current_user)  # Update last login before logout
        logout_user()
        flash('You have been logged out.', 'info')
    
    # Create a response that prevents caching of the login page
    response = redirect(url_for('auth.user_login'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@login_required
@main.route('/clustering-both', methods=['GET', 'POST'])
def clustering_both():

    check = staffs_only()
    if check:
        return check
    
    n_clusters, score = perform_both_clustering_by_part(2)
    return render_template('clustering-both.html', score=score, n_clusters=n_clusters)

@login_required
@main.route("/api/both-cluster-interpretations", methods=['GET'])
def clustering_both_interpretations():
    
    check = staffs_only()
    if check:
        return check
    
    part_id = int(request.args.get('part_id', 2))
    interpretations = get_both_cluster_interpretations(part_id)
    return jsonify(interpretations)

# Bubble for both
@login_required
@main.route("/api/both-bubble-charts", methods=['GET'])
def clustering_bubble_both():

    check = staffs_only()
    if check:
        return check

    part_id = int(request.args.get('part_id', 2))
    both_bubble_by_part = get_both_bubble_data_by_part(part_id)
    return jsonify(both_bubble_by_part)


# Scatter for both
@main.route("/api/both-charts", methods=["GET"])
def clustering_both_data():

    check = staffs_only()
    if check:
        return check
    
    try:
        part_id = int(request.args.get('part', 2))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid part number'}), 400

    scatter = get_both_scatter_by_part(part_id)
    n_clusters, score = perform_both_clustering_by_part(part_id)

    return jsonify({
        "scatter": scatter["scatter_data"],
        "score": round(score, 4) if score else None,
        "n_clusters": n_clusters
    })


@login_required
@main.route("/api/clustering-both-dendrogram", methods=["GET"])
def api_both_dendrogram():
    check = staffs_only()
    if check:
        return check

    part_id = int(request.args.get("part"))
    n_clusters, scores = perform_both_clustering_by_part(part_id)

    # Z: linkage matrix, labels: student IDs in order, cluster_map: {student_id: cluster_id from DB}
    Z, labels, cluster_map = get_both_linkage_by_part(part_id)

    if Z is None or labels is None:
        abort(404, "No data available for this part")

    # 🎨 Color mapping for known clusters (extend as needed)
    color_dict = {
        0: '#e74c3c',   # red
        1: '#2ecc71',   # green
        2: '#3498db',   # blue
        3: '#9b59b6',   # purple
        4: '#f1c40f',   # yellow
        5: '#1abc9c'    # teal
    }

    # 📈 Plot dendrogram
    fig, ax = plt.subplots(figsize=(14, 6))
    dendro = dendrogram(Z, labels=labels, leaf_rotation=90, leaf_font_size=8, ax=ax)

    # 🖍 Color each label based on its cluster in DB
    for lbl in ax.get_xmajorticklabels():
        student_id = lbl.get_text()
        cluster_id = cluster_map.get(student_id)
        lbl.set_color(color_dict.get(cluster_id, '#000000'))  # fallback black

    if n_clusters < len(Z):
        distances = [merge[2] for merge in Z[-(n_clusters - 1):]]
        max_d = max(distances)
        scaled_d = max_d * 0.95  # scale down to make it more centered visually

        ax.axhline(scaled_d, color='red', linestyle='--', linewidth=1, label=f"n_cluster (n = {n_clusters})")
        ax.legend(loc='upper right')


    # 📋 Final formatting
    ax.set_xlabel("Student ID")
    ax.set_ylabel("Distance")
    ax.set_title(f"Dendrogram for Part {part_id}")
    plt.tight_layout()

    # 📤 Output as image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

    
@login_required
@main.route('/clustering-academic', methods=['GET', 'POST'])
def clustering_academic():

    check = staffs_only()
    if check:
        return check
    
    n_clusters, score = perform_academic_clustering_by_part(2)

    return render_template('clustering-academic.html', score=score, n_clusters=n_clusters)

@login_required
@main.route("/api/academic-charts", methods=["GET"])
def api_academic_charts():
  
    check = staffs_only()
    if check:
        return check

    part_id = int(request.args.get("part", 2))
    
    scatter_data = get_academic_scatter_pca_by_part(part_id)
    bubble_data = get_academic_bubble_data_by_part(part_id)
    n_clusters, score = perform_academic_clustering_by_part(part_id) 

    return jsonify({
        "scatter": scatter_data,
        "bubble": bubble_data,
        "score": round(score, 4) if score else None,
        "n_clusters": n_clusters
    })

from flask import send_file
import io
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, fcluster

from flask import abort, send_file

import matplotlib
matplotlib.use('Agg')

@login_required
@main.route("/api/clustering-academic", methods=["GET"])
def api_academic_dendrogram():

    check = staffs_only()
    if check:
        return check
    
    part_id = int(request.args.get("part", 2))
    n_clusters, scores = perform_academic_clustering_by_part(part_id)

    # Retrieve linkage matrix, student labels, and cluster map from database or logic
    Z, labels, cluster_map = get_academic_linkage_by_part(part_id)

    if Z is None or labels is None:
        abort(404, "No data available for this part")

    # 🎨 Match frontend colors for consistency
    color_dict = {
        0: '#e74c3c',  # red
        1: '#2ecc71',  # green
        2: '#3498db'  # blue
    }

    # 📈 Plot dendrogram
    fig, ax = plt.subplots(figsize=(12, 6))
    dendro = dendrogram(Z, labels=labels, leaf_rotation=90, leaf_font_size=8, ax=ax)

    # 🖍 Color tick labels based on cluster assignments
    xlbls = ax.get_xmajorticklabels()
    for lbl in xlbls:
        student_id = lbl.get_text()
        cluster_id = cluster_map.get(student_id)
        lbl.set_color(color_dict.get(cluster_id, '#000000'))  # fallback to black

    if n_clusters < len(Z):
        distances = [merge[2] for merge in Z[-(n_clusters - 1):]]
        max_d = max(distances)
        scaled_d = max_d * 0.95  # scale down to make it more centered visually

        ax.axhline(scaled_d, color='red', linestyle='--', linewidth=1, label=f"n_cluster (n = {n_clusters})")
        ax.legend(loc='upper right')

    # 🖼 Labels and layout
    ax.set_xlabel("Student ID")
    ax.set_ylabel("Distance")
    ax.set_title(f"Dendrogram for Part {part_id}")
    plt.tight_layout()

    # 🔁 Convert to PNG image buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


@login_required
@main.route('/clustering-technical', methods=['GET', 'POST'])
def clustering_technical():
    
    check = staffs_only()
    if check:
        return check
    
    n_clusters, score = perform_technical_clustering_by_part(2)

    return render_template('clustering-technical.html', score=score, n_clusters=n_clusters)

@login_required
@main.route("/api/technical-charts", methods=["GET"])
def api_technical_charts():

    check = staffs_only()
    if check:
        return check
    
    part_id = int(request.args.get("part", 2))

    # 1️⃣ Perform clustering first to update the DB
    n_clusters, score = perform_technical_clustering_by_part(part_id)

    # 2️⃣ Then generate charts using the updated cluster data
    bubble_data = get_technical_bubble_data_by_part(part_id=part_id)
    scatter_data = get_technical_scatter_pca_by_part(part_id=part_id)

    return jsonify({
        "bubble": bubble_data,
        "scatter": scatter_data,
        "score": round(score, 4) if score else None,
        "n_clusters": n_clusters
    })

@login_required
@main.route("/api/clustering-technical", methods=["GET"])
def api_technical_dendrogram():
    check = staffs_only()
    if check:
        return check

    part_id = int(request.args.get("part"))

    # ⚠ This will recompute clustering every time
    n_clusters, scores = perform_technical_clustering_by_part(part_id)

    # Get existing linkage and cluster labels
    Z, labels, cluster_map = get_technical_linkage_by_part(part_id)

    if Z is None or labels is None:
        abort(404, "No data available for this part")

    # Extend as needed
    color_dict = {
        0: '#e74c3c',
        1: '#2ecc71',
        2: '#3498db',
        3: '#9b59b6',
        4: '#f1c40f',
        5: '#1abc9c'
    }

    fig, ax = plt.subplots(figsize=(12, 6))
    dendro = dendrogram(Z, labels=labels, leaf_rotation=90, leaf_font_size=8, ax=ax)

    for lbl in ax.get_xmajorticklabels():
        student_id = lbl.get_text()
        cluster_id = cluster_map.get(student_id)
        lbl.set_color(color_dict.get(cluster_id, "#000000"))

    if n_clusters < len(Z):
        distances = [merge[2] for merge in Z[-(n_clusters - 1):]]
        max_d = max(distances)
        scaled_d = max_d * 0.95  # scale down to make it more centered visually

        ax.axhline(scaled_d, color='red', linestyle='--', linewidth=1, label=f"n_cluster (n = {n_clusters})")
        ax.legend(loc='upper right')

    plt.xlabel("Student ID")
    plt.ylabel("Distance")
    plt.title(f"Technical Dendrogram for Part {part_id}")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@login_required
@main.route('/staff-staffs', methods=['GET', 'POST'])
def staff_staffs():

    check = admin_only()
    if check:
        return check

    staffs_data = get_all_staff_users()
    return render_template('staff-staffs.html', staffs_data=staffs_data)


@main.route('/api/staff/<int:staff_id>', methods=['GET'])
@login_required
def get_staff_by_id(staff_id):

    check = admin_only()
    if check:
        return check
    
    staff = Staff.query.get(staff_id)
    if not staff:
        return {"error": "Staff not found"}, 404

    return {
        "staff_id": staff.staff_id,
        "name": f"{staff.first_name} {staff.last_name}",
        "email": staff.email,
        "position": staff.position,
        "phone": staff.phone_number or "-",
        "address": staff.address or "-",
        "last_online": staff.last_online.strftime('%Y-%m-%d %H:%M') if staff.last_online else "Never",
        "picture": staff.picture or "static/images/default-avatar.png"
    }


@main.route('/staff-students', methods=['GET', 'POST'])
@login_required
def staff_students():

    check = staffs_only()
    if check:
        return check
    
    selected_status = request.args.get("status")
    selected_student = request.args.get("student_id")

    students = get_all_student_users()
    return render_template('staff-students.html', students=students, selected_status=selected_status, selected_student=selected_student)


@main.route('/staff-students-details', methods=['GET'])
@login_required
def staff_students_details():
    check = staffs_only()
    if check:
        return check
    
    selected_student_id = request.args.get("student_id")
    if not selected_student_id:
        return render_template('staff-students-details.html', error='Student ID is required')

    # Fetch the selected student from the database
    selected_student = Student.query.get(selected_student_id)
    if not selected_student:
        return render_template('staff-students-details.html', error='Student Not Found!')

    # Fetch student's part number, defaulting to 1 if not available
    current_part = selected_student.part.part_no if selected_student.part else 1

    # GPA data
    cgpa = get_student_cgpa(selected_student_id)  # Assuming this function works
    gpa_data = get_student_gpa_all_parts_for_staffs(selected_student, current_part)  # Assuming this function works
    gpa_points = [{"x": p[0], "y": float(p[1])} for p in gpa_data if p[1] is not None]

    # Academic bar chart (previous part)
    prev_part = max(1, current_part - 1)
    academic_data = get_barchart_academic_student_for_staffs(selected_student, prev_part)
    courses = [c[0] for c in academic_data] if academic_data else []
    grades = [float(c[1]) if c[1] is not None else 0 for c in academic_data] if academic_data else []
    letters = [c[2] for c in academic_data] if academic_data else []

    # Technical skill scores
    technical_scores_by_part = get_technical_scores_by_all_parts(selected_student_id, current_part)
    tech_categories = next((info['categories'] for info in technical_scores_by_part.values() if info['categories']), [])

    # Accumulated technical scores by part
    accumulated_technical_scores_by_part = get_accumulated_technical_scores_by_all_parts(selected_student_id, current_part)
    accumulated_tech_categories = next((info['categories'] for info in accumulated_technical_scores_by_part.values() if info['categories']), [])

    # Render template and pass all necessary data
    return render_template(
        'staff-students-details.html',
        cgpa=cgpa,
        gpa_points=gpa_points,
        courses=courses,
        grades=grades,
        letters=letters,
        max_part_for_filter=prev_part,
        technical_scores_by_part=technical_scores_by_part,
        tech_categories=tech_categories,
        accumulated_technical_scores_by_part=accumulated_technical_scores_by_part,
        accumulated_tech_categories=accumulated_tech_categories,
        selected_student=selected_student,
        selected_student_id=selected_student_id
    )


@main.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_by_id(student_id):

    check = staffs_only()
    if check:
        return check
    
    student = Student.query.get(student_id)
    cgpa = get_student_cgpa(student_id)
    if not student:
        return {"error": "Student not found"}, 404

    return {
        "student_id": student.student_id,
        "name": f"{student.first_name} {student.last_name}",
        "email": student.email,
        "phone": student.phone_number or "-",
        "address": student.address or "-",
        "cgpa": cgpa or "-",
        "last_online": student.last_online.strftime('%Y-%m-%d %H:%M') if student.last_online else "Never",
        "picture": student.picture or "static/images/students.svg"
    }

@login_required
@main.route('/feedback', methods=['GET', 'POST'])
def feedback():

    check = authenticated()
    if check:
        return check

    if request.method == 'POST':
        category = request.form.get('category')
        message = request.form.get('message')

        if not category or not message:
            flash("Category and message are required.", "error")
            return redirect(url_for('main.feedback'))

        student_id = current_user.student_id if is_student() else None
        staff_id = current_user.staff_id if is_staff() or is_admin() else None

        save_feedback(category, message, student_id, staff_id)
        send_feedback_email(current_user.email, category, message)

        flash("Feedback submitted successfully!", "success")
        return redirect(url_for('main.feedback'))

    return render_template('feedback.html')

from skillytics.CRUD import get_all_feedbacks
@login_required
@main.route('/admin-list-feedback', methods=['GET', 'POST', 'DELETE'])
def admin_list_feedback():

    check = admin_only()
    if check:
        return check

    if request.method == 'POST':
        feedback_id = request.form.get('feedback_id')
        
        if not feedback_id:
            flash('No feedback ID provided.', 'danger')
            return redirect(url_for('main.admin_list_feedback'))
            
        if delete_feedback(feedback_id):
            flash('Feedback deleted successfully.', 'success')
        else:
            flash('Failed to delete feedback.', 'danger')
        return redirect(url_for('main.admin_list_feedback'))
    
    feedbacks = get_all_feedbacks()
    return render_template('admin-list-feedback.html', feedbacks=feedbacks)


@login_required
@main.route('/view-notification', methods=['GET', 'POST', 'DELETE'])
def view_notification():

    check = authenticated()
    if check:
        return check

    notifications_to_students = []
    notifications_from_staffs = []

    if is_admin():
        notifications_to_students = get_all_notifications()
    elif is_staff():
        notifications_to_students = get_notifications_by_staff_id(current_user.staff_id)
    elif is_student():
        notifications_from_staffs = get_notifications_for_student(current_user.student_id)

    if request.method == 'POST':

        if request.form.get('send-notification'):
            subject = request.form.get('subject')
            message = request.form.get('message')
            part_id = request.form.get('part-id')
            cluster_type = request.form.get('cluster-type')
            cluster_no = request.form.get('cluster-no')

            if not all([subject, message, part_id, cluster_type, cluster_no]):
                flash('All fields are required to send a notification.', 'danger')
                return redirect(url_for('main.view_notification'))

            save_notification(
                staff_id=current_user.staff_id,
                subject=subject,
                message=message,
                part_id=part_id,
                cluster_type=cluster_type,
                cluster_no=cluster_no
            )
            flash('Announcement sent successfully!', 'success')
            return redirect(url_for('main.view_notification'))
        
        else:
            notification_id = request.form.get('notification_id')
            
            if not notification_id:
                flash('No announcement ID provided.', 'danger')
                return redirect(url_for('main.view_notification'))
                
            if delete_notification(notification_id):
                flash('Announcement deleted successfully.', 'success')
            else:
                flash('Failed to delete announcement.', 'danger')
            return redirect(url_for('main.view_notification'))

    return render_template(
        'view-notification.html',
        notifications_to_students=notifications_to_students,
        notifications_from_staffs=notifications_from_staffs
    )

@login_required
@main.route('/api/notification/<int:notification_id>', methods=['GET'])
def get_notification_by_id(notification_id):

    check = authenticated()
    if check:
        return check

    notification = Notification.query.get(notification_id)
    if not notification:
        return {"error": "Notification not found"}, 404

    date_sent, time_sent = format_time_sent(notification.time_sent)

    return {
        "subject": notification.subject,
        "message": notification.message,
        "date_sent": date_sent,
        "time_sent": time_sent
    }


@login_required
@main.route('/staff-add-staff', methods=['POST', 'GET'])
def add_staff():

    check = admin_only()
    if check:
        return check

    if request.method == 'POST':
        staff_id = request.form.get('staff-id')
        staff_email = request.form.get('staff-email')
        staff_first_name = request.form.get('staff-first-name')
        staff_last_name = request.form.get('staff-last-name')
        staff_gender = request.form.get('staff-gender')
        staff_position = request.form.get('staff-position')
        staff_phone_number = request.form.get('staff-phone-number')
        staff_address = request.form.get('staff-address')

        picture=None
        if 'staff-picture' in request.files:
            picture_file = request.files['staff-picture']
            if picture_file and picture_file.filename != '':
                # Secure the file name to prevent security issues
                filename = secure_filename(picture_file.filename)
                
                picture = filename
                picture_file.save(os.path.join(current_app.root_path, 'static/images/', picture))

        # If successfully added to database
        if add_staff_to_db(staff_id, staff_email, staff_first_name, staff_last_name, staff_gender, staff_position, staff_phone_number, staff_address, picture):
            send_staff_email(staff_email, staff_id, '123')
            return redirect(url_for('main.add_staff'))
        
        else:
            return redirect(url_for('main.add_staff'))
    
    # If the method is GET
    last_staff = Staff.query.order_by(Staff.staff_id.desc()).first()
    next_id = 100000 if not last_staff else last_staff.staff_id + 1

    return render_template('staff-add-staff.html', next_id=next_id)


@login_required
@main.route('/profile', methods=['POST', 'GET'])
def profile():

    check = authenticated()
    if check:
        return check
    
    if request.method == 'POST':

        # Get the current user
        if is_student():
            user = Student.query.get(current_user.student_id)
        else:
            user = Staff.query.get(current_user.staff_id)

        phone_number = request.form.get('phone-number')
        address = request.form.get('address')

        # Handle profile picture upload
        picture = current_user.picture  # default picture path if no new image is uploaded
        if 'profile-image' in request.files:
            picture_file = request.files['profile-image']
            if picture_file and picture_file.filename != '':
                # Secure the file name to prevent security issues
                filename = secure_filename(picture_file.filename)
                
                picture = filename
                picture_file.save(os.path.join(current_app.root_path, 'static/images/', picture))

                if update_picture(user, picture):
                    return redirect(url_for('main.profile'))

        # Call the update_profile function
        if update_profile(user, phone_number, address):
            return redirect(url_for('main.profile'))

    return render_template('profile.html')

@login_required
@main.route('/change-password', methods=['POST', 'GET'])
def change_password():

    check = authenticated()
    if check:
        return check

    if request.method == 'POST':
        current_password = request.form.get('current-password')
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')

        # Get the current user
        user = None
        if is_student():
            user = Student.query.get(current_user.student_id)
        else:
            user = Staff.query.get(current_user.staff_id)

        # Call the function from CRUD.py to handle the password change
        if change_user_password(user, current_password, new_password, confirm_password):
            send_change_password_email(current_user.email)
            return render_template('change-password.html')

    return render_template('change-password.html')
    

TS_CATEGORY_MAP = {
    'dl': {
        'id': 1,
        'label': 'Digital Literacy',
        'template': 'form-dl.html',
        'redirect': {'endpoint': 'main.form_ts_category', 'category': 'dl'}
    },
    'programming': {
        'id': 2,
        'label': 'Programming',
        'template': 'form-programming.html',
        'redirect': {'endpoint': 'main.form_ts_category', 'category': 'programming'}
    },
    'ds-ml': {
        'id': 3,
        'label': 'Data Science & Machine Learning',
        'template': 'form-ds-ml.html',
        'redirect': {'endpoint': 'main.form_ts_category', 'category': 'ds-ml'}
    }
}

@login_required
@main.route('/form-<category>', methods=['GET', 'POST'])
def form_ts_category(category):

    check = student_only()
    if check:
        return check

    cat = TS_CATEGORY_MAP.get(category)
    if not cat:
        flash("Invalid category", "danger")
        return redirect(url_for('main.dashboard'))

    scores = get_student_ts_score_by_ts(current_user.student_id, cat['id'], current_user.part_id)

    if request.method == 'POST':
        try:
            updated_scores = {}
            for i in range(1, 6):
                val = request.form.get(f'q{i}')
                if val is None or not val.strip().isdigit():
                    raise ValueError(f"Q{i} score must be a number.")
                updated_scores[f'q{i}_score'] = int(val.strip())

            update_student_ts_score(current_user.student_id, cat['id'], updated_scores, current_user.part_id)
            flash(f"Your {cat['label']} scores for part {current_user.part.part_no} have been updated!", "success")

            # Check and update completion
            check_and_update_ts_completion(current_user.student_id)
            
            return redirect(url_for(cat['redirect']['endpoint'], category=cat['redirect']['category']))

        except ValueError as e:
            flash(str(e), "danger")

    return render_template(cat['template'], scores=scores)

import csv
from io import StringIO
from flask import Response

## download file
@login_required
@main.route('/download-staffs-csv')
def download_staffs_csv():

    check = staffs_only()
    if check:
        return check

    si = StringIO()
    cw = csv.writer(si)

    # Write header
    cw.writerow(['Staff ID', 'Email', 'Name', 'Gender', 'Position', 'Phone Number', 'Address', 'Institution Name', 'Faculty Name'])

    # Query and write data
    staffs = Staff.query.filter(Staff.position != 'Admin').all()
    for staff in staffs:
        cw.writerow([
            staff.staff_id,
            staff.email,
            staff.first_name + ' ' + staff.last_name,
            staff.gender,
            staff.position,
            staff.phone_number,
            staff.address,
            staff.institution_name,
            staff.faculty_name
        ])

    # Create response
    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment; filename=staff_list.csv"
        }
    )

@login_required
@main.route('/download-staffs-pdf')
def download_staffs_pdf():

    check = staffs_only()
    if check:
        return check

    # Query staff data (excluding Admins)
    staffs = Staff.query.filter(Staff.position != 'Admin').all()

    # PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=0.3 * inch,
        rightMargin=0.3 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="Staff List",
        author="Skillytics System"
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading_style = styles['Heading1']

    # Column widths (must total < ~11.7 inches for landscape A4)
    col_widths = [
        1.8 * inch,  # Email
        1.5 * inch,  # Name
        0.8 * inch,  # Gender
        1.0 * inch,  # Position
        1.2 * inch,  # Phone
        1.8 * inch,  # Address
        1.5 * inch,  # Institution
        1.5 * inch   # Faculty
    ]

    # Table data with wrapped Paragraphs
    data = [[
        'Email', 'Name', 'Gender', 'Position', 'Phone Number', 'Address', 'Institution Name', 'Faculty Name'
    ]]

    for staff in staffs:
        data.append([
            Paragraph(staff.email, normal_style),
            Paragraph(f"{staff.first_name} {staff.last_name}", normal_style),
            Paragraph(staff.gender or 'N/A', normal_style),
            Paragraph(staff.position or 'N/A', normal_style),
            Paragraph(staff.phone_number or 'N/A', normal_style),
            Paragraph(staff.address or 'N/A', normal_style),
            Paragraph(staff.institution_name or 'N/A', normal_style),
            Paragraph(staff.faculty_name or 'N/A', normal_style),
        ])

    # Create table
    table = Table(data, colWidths=col_widths)

    # Table styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    # Build document
    elements = [
        Paragraph("Staff List", heading_style),
        Spacer(1, 12),
        table
    ]

    doc.build(elements)

    # Get PDF content
    pdf_value = buffer.getvalue()
    buffer.close()

    # Send PDF as response
    return Response(
        pdf_value,
        mimetype='application/pdf',
        headers={
            "Content-Disposition": "attachment; filename=staff_list.pdf"
        }
    )

@login_required
@main.route('/download-students-pdf')
def download_students_pdf():

    check = staffs_only()
    if check:
        return check

    # Get filter parameters
    part_id = request.args.get('part_id', type=int)
    cluster_type = request.args.get('cluster_type')
    cluster_no = request.args.get('cluster_no', type=int)

    if not (part_id and cluster_type and cluster_no is not None):
        flash("Missing filter parameters.", "danger")
        return redirect(url_for('main.student_list'))

    # Get students
    students = get_filtered_students(part_id, cluster_type, cluster_no)

    # Resolve label and field
    cluster_label = {
        "Academic + Technical": "Both",
        "Academic Performance": "Academic",
        "Technical Skills": "Technical"
    }.get(cluster_type, "Cluster")

    # Setup PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=0.3 * inch,
        rightMargin=0.3 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    heading = styles["Heading1"]
    normal = styles["Normal"]

    # Header
    data = [['Student ID', 'Name', 'Part', cluster_label]]

    for s in students:
        cluster_val = {
            "Academic + Technical": s['cluster_both'],
            "Academic Performance": s['cluster_academic'],
            "Technical Skills": s['cluster_technical_skills']
        }.get(cluster_type)

        data.append([
            Paragraph(str(s['id']), normal),
            Paragraph(s['name'], normal),
            Paragraph(str(s['student_part']), normal),
            Paragraph(str(cluster_val) if cluster_val is not None else 'N/A', normal),
        ])

    # Table formatting
    table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1.0*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black)
    ]))

    elements = [
        Paragraph(f"Student List – Part {part_id}, {cluster_label} Cluster {cluster_no}", heading),
        Spacer(1, 12),
        table
    ]
    doc.build(elements)

    pdf_value = buffer.getvalue()
    buffer.close()

    return Response(
        pdf_value,
        mimetype='application/pdf',
        headers={"Content-Disposition": "attachment; filename=student_list_filtered.pdf"}
    )

@login_required
@main.route('/download-students-csv')
def download_students_csv():

    check = staffs_only()
    if check:
        return check

    # Get filter parameters
    part_id = request.args.get('part_id', type=int)
    cluster_type = request.args.get('cluster_type')
    cluster_no = request.args.get('cluster_no', type=int)

    if not (part_id and cluster_type and cluster_no is not None):
        flash("Missing filter parameters.", "danger")
        return redirect(url_for('main.student_list'))

    # Get students
    students = get_filtered_students(part_id, cluster_type, cluster_no)

    # Determine field
    cluster_field = {
        "Academic + Technical": "cluster_both",
        "Academic Performance": "cluster_academic",
        "Technical Skills": "cluster_technical_skills"
    }.get(cluster_type)

    cluster_label = {
        "Academic + Technical": "Both",
        "Academic Performance": "Academic",
        "Technical Skills": "Technical"
    }.get(cluster_type)

    # Write to CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Student ID', 'Name', 'Part', cluster_label])

    for s in students:
        cluster_val = s[cluster_field]
        writer.writerow([
            s['id'],
            s['name'],
            s['student_part'],
            cluster_val if cluster_val is not None else 'N/A'
        ])

    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=student_list_filtered.csv"}
    )

@login_required
@main.route('/download-feedbacks-csv')
def download_feedbacks_csv():
    
    check = staffs_only()
    if check:
        return check

    # Query feedback data
    feedbacks = get_all_feedbacks()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row - matching PDF columns
    writer.writerow([
        'Date',
        'Time', 
        'Sender Email',
        'Category',
        'Message'
    ])
    
    # Write data rows
    for feedback in feedbacks:
        # Determine sender email (student or staff) - same logic as PDF
        sender_email = feedback['student_email'] if feedback['student_email'] else feedback['staff_email']
        
        writer.writerow([
            feedback['date_sent'] or '',
            feedback['time_sent'] or '',
            sender_email or '',
            feedback['category'] or '',
            feedback['message'] or ''
        ])
    
    # Get CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Send CSV as response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment; filename=feedback_list.csv"
        }
    )

@login_required
@main.route('/download-feedbacks-pdf')
def download_feedbacks_pdf():

    check = staffs_only()
    if check:
        return check

    # Query feedback data
    feedbacks = get_all_feedbacks()

    # PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=0.3 * inch,
        rightMargin=0.3 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="Feedback List",
        author="Skillytics System"
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading_style = styles['Heading1']

    # Column widths (must total < ~11.7 inches for landscape A4)
    col_widths = [
        1.5 * inch,  # Date
        1.2 * inch,  # Time
        2.2 * inch,  # Sender Email
        1.2 * inch,  # Category
        4.6 * inch   # Message
    ]

    # Table data with wrapped Paragraphs - matching CSV columns
    data = [[
        'Date', 'Time', 'Sender Email', 'Category', 'Message'
    ]]

    for feedback in feedbacks:
        # Determine sender email (student or staff) - same logic as CSV
        sender_email = feedback['student_email'] if feedback['student_email'] else feedback['staff_email']
        
        # Truncate long messages for better display
        message = feedback['message']
        if message and len(message) > 200:
            message = message[:200] + "..."
        
        data.append([
            Paragraph(feedback['date_sent'] or 'N/A', normal_style),
            Paragraph(feedback['time_sent'] or 'N/A', normal_style),
            Paragraph(sender_email or 'N/A', normal_style),
            Paragraph(feedback['category'] or 'N/A', normal_style),
            Paragraph(message or 'N/A', normal_style),
        ])

    # Create table
    table = Table(data, colWidths=col_widths)

    # Table styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
    ]))

    # Build document
    elements = [
        Paragraph("Feedback List", heading_style),
        Spacer(1, 12),
        table
    ]

    doc.build(elements)

    # Get PDF content
    pdf_value = buffer.getvalue()
    buffer.close()

    # Send PDF as response
    return Response(
        pdf_value,
        mimetype='application/pdf',
        headers={
            "Content-Disposition": "attachment; filename=feedback_list.pdf"
        }
    )


@login_required
@main.route("/api/academic-cluster-interpretations", methods=["GET"])
def api_academic_cluster_interpretations():
    check = staffs_only()
    if check:
        return check
    part_id = int(request.args.get('part_id', 2))
    from skillytics.CRUD import get_academic_cluster_interpretations
    interpretations = get_academic_cluster_interpretations(part_id)
    return jsonify(interpretations)

@login_required
@main.route("/api/technical-cluster-interpretations", methods=["GET"])
def api_technical_cluster_interpretations():
    check = staffs_only()
    if check:
        return check
    part_id = int(request.args.get('part_id', 2))
    from skillytics.CRUD import get_technical_cluster_interpretations
    interpretations = get_technical_cluster_interpretations(part_id)
    return jsonify(interpretations)
