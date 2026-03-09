from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import pandas as pd
from skillytics import db
from skillytics.models import Student, Enrollment, Course, StudentSemesterCluster, TechnicalSkillScore


def find_optimal_clusters(data, max_clusters=10, min_clusters=2):
    n_samples = data.shape[0]
    max_clusters = min(max_clusters, n_samples - 1)
    
    if max_clusters < min_clusters:
        return min_clusters, {}
    
    silhouette_scores = {}
    
    for n_clusters in range(min_clusters, max_clusters + 1):
        model = AgglomerativeClustering(n_clusters=n_clusters, metric='euclidean', linkage='ward')
        cluster_labels = model.fit_predict(data)
        score = silhouette_score(data, cluster_labels)
        silhouette_scores[n_clusters] = score
    
    # Find optimal number of clusters (highest silhouette score)
    optimal_clusters = max(silhouette_scores.keys(), key=lambda k: silhouette_scores[k])
    
    return optimal_clusters, silhouette_scores


def _get_grade_map():
    """Helper function to return grade mapping"""
    return {
        'A+': 4.00, 'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00, 'C-': 1.67,
        'D+': 1.33, 'D': 1.00, 'E': 0.67,
        'F': 0.00
    }


def _update_student_cluster_record(student_id, part_id, cluster_type, cluster_label):
    """Helper function to update or create StudentSemesterCluster record"""
    record = StudentSemesterCluster.query.filter_by(student_id=student_id, part_id=part_id).first()
    if not record:
        record = StudentSemesterCluster(student_id=student_id, part_id=part_id)
        db.session.add(record)
    
    setattr(record, cluster_type, cluster_label)
    return record


################        ACADEMIC PERFORMANCE        ################

def perform_academic_clustering_by_part(part_id, max_clusters=8):
    """Cluster students based on academic performance from previous part"""
    previous_part = part_id - 1
    if previous_part < 1:
        print(f"❌ Cannot cluster part {part_id}: no previous courses taken.")
        return None

    # Step 1: Get enrollments for courses from the previous part
    enrollments = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            Enrollment.course_grade,
            Student.part_id
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .filter(Course.part_id == previous_part)
        .filter(Student.part_id == part_id)
        .all()
    )

    if not enrollments:
        print(f"⚠ No enrollment data found for part {part_id} (using part {previous_part} courses).")
        return None

    # Step 2: Grade conversion
    grade_map = _get_grade_map()

    df = pd.DataFrame(enrollments, columns=['student_id', 'course_code', 'course_grade', 'current_part'])
    df['grade_point'] = df['course_grade'].map(grade_map).fillna(0)

    # Step 3: Pivot data
    df_pivot = df.pivot_table(index='student_id', columns='course_code', values='grade_point', fill_value=0)

    if df_pivot.shape[0] < 2:
        print(f"⚠ Not enough students in part {part_id} for clustering.")
        return None

    # Step 4: Scale data
    scaled = StandardScaler().fit_transform(df_pivot)

    # Step 5: Find optimal number of clusters
    optimal_clusters, scores = find_optimal_clusters(scaled, max_clusters=max_clusters)

    # Step 6: Perform clustering
    model = AgglomerativeClustering(n_clusters=optimal_clusters, metric='euclidean', linkage='ward')
    cluster_labels = model.fit_predict(scaled)

    # Step 7: Calculate final silhouette score
    final_score = silhouette_score(scaled, cluster_labels)
    print(f"🧠 Final Silhouette Score for part {part_id} using part {previous_part} courses: {final_score:.4f}")
    print(f"📈 Used {optimal_clusters} clusters for {df_pivot.shape[0]} students")

    # Step 8: Save to database
    for idx, student_id in enumerate(df_pivot.index):
        _update_student_cluster_record(student_id, part_id, 'cluster_academic', int(cluster_labels[idx]))

    db.session.commit()

    return optimal_clusters, final_score


#################       TECHNICAL SKILLS        ################

def perform_technical_clustering_by_part(part_id, max_clusters=8):
    """Cluster students based on technical skills from previous part"""
    previous_part = part_id - 1
    if previous_part < 1:
        print(f"❌ Cannot cluster part {part_id}: no previous technical skills taken.")
        return None
    
    # Get technical skill scores
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
        .filter(Student.part_id == part_id)
        .filter(TechnicalSkillScore.part_id == previous_part)
        .all()
    )

    if not scores:
        print(f"⚠ No technical skill data found for part {part_id} (using part {previous_part} scores).")
        return None

    # Process data
    df = pd.DataFrame(scores, columns=['student_id', 'category_id', 'q1', 'q2', 'q3', 'q4', 'q5'])
    
    # Filter out students with no valid scores
    df['valid_score_count'] = df[['q1', 'q2', 'q3', 'q4', 'q5']].notnull().sum(axis=1)
    fully_null_students = df.groupby('student_id')['valid_score_count'].sum()
    fully_null_students = fully_null_students[fully_null_students == 0].index.tolist()
    df = df[~df['student_id'].isin(fully_null_students)]

    # Pivot data
    df['skill_label'] = df['category_id'].astype(str) + '_'
    wide_df = df.pivot_table(
        index='student_id',
        columns='skill_label',
        values=['q1', 'q2', 'q3', 'q4', 'q5']
    )
    wide_df.columns = [f"{prefix}{q}" for q, prefix in wide_df.columns]

    # Only cluster students with complete data
    clusterable_df = wide_df.dropna()
    clusterable_df.index = clusterable_df.index.astype(str)
    clusterable_students = clusterable_df.index.tolist()

    # Get all students who should have records
    all_students = list(set(df['student_id'].astype(str).tolist()) | set(map(str, fully_null_students)))

    if clusterable_df.shape[0] < 2:
        print(f"⚠ Not enough students with complete scores for clustering.")
        return None

    # Scale and cluster
    scaled = StandardScaler().fit_transform(clusterable_df)
    optimal_clusters, scores = find_optimal_clusters(scaled, max_clusters=max_clusters)

    model = AgglomerativeClustering(n_clusters=optimal_clusters, metric='euclidean', linkage='ward')
    cluster_labels = model.fit_predict(scaled)

    final_score = silhouette_score(scaled, cluster_labels)
    print(f"🧠 Final Silhouette Score for TECHNICAL (part {part_id}): {final_score:.4f}")
    print(f"📈 Used {optimal_clusters} clusters for {clusterable_df.shape[0]} students")

    # Save to database
    for student_id in all_students:
        if student_id in clusterable_students:
            cluster_idx = clusterable_students.index(student_id)
            cluster_label = int(cluster_labels[cluster_idx])
        else:
            cluster_label = None  # Students without complete data get None
        
        _update_student_cluster_record(student_id, part_id, 'cluster_technical_skills', cluster_label)

    db.session.commit()

    return optimal_clusters, final_score


############        BOTH AREAS      ####################

def perform_both_clustering_by_part(part_id, max_clusters=8):
    """Cluster students based on both academic and technical performance"""
    previous_part = part_id - 1
    if previous_part < 1:
        print(f"⚠ Cannot cluster part {part_id}: no previous part.")
        return None

    # 1️⃣ Get academic scores
    grades = (
        db.session.query(
            Enrollment.student_id,
            Course.course_code,
            Enrollment.course_grade
        )
        .join(Course, Enrollment.course_code == Course.course_code)
        .join(Student, Enrollment.student_id == Student.student_id)
        .filter(Course.part_id == previous_part)
        .filter(Student.part_id == part_id)
        .all()
    )

    if not grades:
        print(f"⚠ No academic data found for part {part_id}.")
        return None

    grade_map = _get_grade_map()

    df_grades = pd.DataFrame(grades, columns=['student_id', 'course_code', 'course_grade'])
    df_grades['grade_point'] = df_grades['course_grade'].map(grade_map).fillna(0)
    df_academic = df_grades.pivot_table(index='student_id', columns='course_code', values='grade_point', fill_value=0)

    # 2️⃣ Get technical skills
    tech = (
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
        .filter(Student.part_id == part_id)
        .filter(TechnicalSkillScore.part_id == previous_part)
        .all()
    )

    if not tech:
        print(f"⚠ No technical skill data found for part {part_id}.")
        return None

    df_tech = pd.DataFrame(tech, columns=[
        'student_id', 'category_id', 'q1', 'q2', 'q3', 'q4', 'q5'
    ])

    # Exclude students with no valid technical scores
    df_tech['valid_score_count'] = df_tech[['q1', 'q2', 'q3', 'q4', 'q5']].notnull().sum(axis=1)
    fully_null_students = df_tech.groupby('student_id')['valid_score_count'].sum()
    fully_null_students = fully_null_students[fully_null_students == 0].index.tolist()
    df_tech = df_tech[~df_tech['student_id'].isin(fully_null_students)]

    # Pivot technical data
    df_tech['label'] = df_tech['category_id'].astype(str) + '_'
    df_tech_wide = df_tech.pivot_table(index='student_id', columns='label', values=['q1', 'q2', 'q3', 'q4', 'q5'])
    df_tech_wide.columns = [f"{prefix}{q}" for q, prefix in df_tech_wide.columns]

    # 3️⃣ Combine academic and technical data
    df_combined = df_academic.join(df_tech_wide, how='inner')

    # Only cluster students with complete data
    df_clusterable = df_combined.dropna()
    df_clusterable.index = df_clusterable.index.astype(str)
    clusterable_students = df_clusterable.index.tolist()

    # Get all students who should have records
    all_students = list(set(df_academic.index.astype(str).tolist()) | set(df_tech_wide.index.astype(str).tolist()))

    if df_clusterable.shape[0] < 2:
        print(f"⚠ Not enough complete students in part {part_id} for clustering.")
        return None

    # 4️⃣ Scale and cluster
    scaled = StandardScaler().fit_transform(df_clusterable)
    optimal_clusters, scores = find_optimal_clusters(scaled, max_clusters=max_clusters)

    model = AgglomerativeClustering(n_clusters=optimal_clusters, metric='euclidean', linkage='ward')
    cluster_labels = model.fit_predict(scaled)

    final_score = silhouette_score(scaled, cluster_labels)
    print(f"🧠 Final Silhouette Score for COMBINED (part {part_id}): {final_score:.4f}")
    print(f"📈 Used {optimal_clusters} clusters for {df_clusterable.shape[0]} students")

    # 5️⃣ Save to database
    for student_id in all_students:
        student_id_str = str(student_id)
        
        if student_id_str in clusterable_students:
            cluster_idx = clusterable_students.index(student_id_str)
            cluster_label = int(cluster_labels[cluster_idx])
        else:
            cluster_label = None  # Students without complete data get None
        
        _update_student_cluster_record(student_id, part_id, 'cluster_both', cluster_label)

    db.session.commit()

    return optimal_clusters, final_score