import pandas as pd
import random
import re
from collections import defaultdict


def load_and_preprocess_data(file_path):
    """Load CSV data and preprocess column names."""
    print("Loading and preprocessing data...")
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.replace('\xa0', ' ', regex=False)
    return df

def rename_columns_to_schema(df):
    """Rename columns to match database schema."""
    print("Renaming columns to match database schema...")
    column_mapping = {
        # Personal Details
        'What is your gender?': 'gender',
        'What is your current semester?': 'part',

        # Academic scores - Part 1
        'CSC402 - PROGRAMMING I': 'CSC402',
        'CSC413 - INTRODUCTION TO INTERACTIVE MULTIMEDIA': 'CSC413',
        'CSC429 - COMPUTER ORGANIZATION AND ARCHITECTURE': 'CSC429',
        'CTU552 - PHILOSOPHY AND CURRENT ISSUES': 'CTU552',
        'CO-CURRICULAR (E.G., HBU111, ETC)': 'C1',
        'ICT450 - DATABASE DESIGN AND DEVELOPMENT': 'ICT450',
        'MAT406 - FOUNDATION MATHEMATICS': 'MAT406',

        # Academic scores - Part 2
        'CSC404 - PROGRAMMING II': 'CSC404',
        'CTU554 - VALUES AND CIVILIZATION II': 'CTU554',
        'CO-CURRICULAR (E.G., HBU121, ETC)': 'C2',
        'ICT502 - DATABASE ENGINEERING': 'ICT502',
        'ITT400 - INTRODUCTION TO DATA COMMUNICATION AND NETWORKING': 'ITT400',
        'MAT421 - CALCULUS I': 'MAT421',
        'STA416 - APPLIED PROBABILITY AND STATISTICS': 'STA416',

        # Academic scores - Part 3
        'CSC435 - OBJECT ORIENTED PROGRAMMING': 'CSC435',
        'CSC510 - DISCRETE STRUCTURES': 'CSC510',
        'CSC520 - PRINCIPLES OF OPERATING SYSTEMS': 'CSC520',
        'CSC583 - ARTIFICIAL INTELLIGENCE ALGORITHMS': 'CSC583',
        'ELC501 - ENGLISH FOR CRITICAL ACADEMIC READING': 'ELC501',
        'CO-CURRICULAR (E.G., HBU131, ETC)': 'C3',
        'MAT423 - LINEAR ALGEBRA I': 'MAT423',
        'FOREIGN LANGUAGE (E.G., TMC401, ETC)': 'FL1',

        # Academic scores - Part 4
        'CSC508 - DATA STRUCTURES': 'CSC508',
        'CSC569 - PRINCIPLES OF COMPILERS': 'CSC569',
        'CSC577 - SOFTWARE ENGINEERING - THEORIES AND PRINCIPLES': 'CSC577',
        'CSC584 - ENTERPRISE PROGRAMMING': 'CSC584',
        'ELC650 - ENGLISH FOR PROFESSIONAL INTERACTION': 'ELC650',
        'ELECTIVE (ISP565 - DATA MINING, CSC566 - IMAGE PROCESSING)': 'E1',
        'FOREIGN LANGUAGE (E.G., TMC451, ETC)': 'FL2',

        # Academic scores - Part 5
        'CSC580 - PARALLEL PROCESSING': 'CSC580',
        'CSC645 - ALGORITHM ANALYSIS AND DESIGN': 'CSC645',
        'CSC649 - SPECIAL TOPICS IN COMPUTER SCIENCE': 'CSC649',
        'CSP600 - PROJECT FORMULATION': 'CSP600',
        'ENT600 - TECHNOLOGY ENTREPRENEURSHIP': 'ENT600',
        'ELECTIVE (STA404 - STATISTICS FOR BUSINESS AND SOCIAL SCIENCES, CSC557 - MOBILE PROGRAMMING)': 'E2',
        'FOREIGN LANGAUGE (E.G., TMC501, ETC)': 'FL3',

        # Academic scores - Part 6
        'ELECTIVE (DSC651 - DATA REPRESENTATION AND REPORTING TECHNIQUES, CSC683 - GAME DEVELOPMENT)': 'E3',
        'CSC662 - COMPUTER SECURITY': 'CSC662',
        'ELECTIVE (ISP610 - BUSINESS DATA ANALYTICS, CSC574 - DYNAMIC WEB APPLICATION DEVELOPMENT)': 'E4',
        'CSC650 - PROJECT': 'CSC650',
        'EET699 - ENGLISH EXIT TEST': 'EET699',
        'ICT652 - ETHICAL, SOCIAL, AND PROFESSIONAL ISSUES IN ICT': 'ICT652',

        # Digital Literacy Skills (Part 1)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 1)': 'dl_1_p1',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 1)': 'dl_2_p1',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 1)': 'dl_3_p1',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 1)': 'dl_4_p1',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 1)': 'dl_5_p1',
        
        # Programming Skills (Part 1)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 1)': 'prog_1_p1',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 1)': 'prog_2_p1',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 1)': 'prog_3_p1',
        'How well can you analyze and optimize the performance of a program? (Part 1)': 'prog_4_p1',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 1)': 'prog_5_p1',
        
        # Data Science Skills (Part 1)
        'I am confident in using SQL and Python for data analysis and database queries (Part 1)': 'ds_1_p1',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 1)': 'ds_2_p1',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 1)': 'ds_3_p1',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 1)': 'ds_4_p1',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 1)': 'ds_5_p1',

        # Digital Literacy Skills (Part 2)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 2)': 'dl_1_p2',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 2)': 'dl_2_p2',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 2)': 'dl_3_p2',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 2)': 'dl_4_p2',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 2)': 'dl_5_p2',
        
        # Programming Skills (Part 2)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 2)': 'prog_1_p2',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 2)': 'prog_2_p2',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 2)': 'prog_3_p2',
        'How well can you analyze and optimize the performance of a program? (Part 2)': 'prog_4_p2',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 2)': 'prog_5_p2',
        
        # Data Science Skills (Part 2)
        'I am confident in using SQL and Python for data analysis and database queries (Part 2)': 'ds_1_p2',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 2)': 'ds_2_p2',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 2)': 'ds_3_p2',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 2)': 'ds_4_p2',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 2)': 'ds_5_p2',

        # Digital Literacy Skills (Part 3)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 3)': 'dl_1_p3',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 3)': 'dl_2_p3',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 3)': 'dl_3_p3',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 3)': 'dl_4_p3',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 3)': 'dl_5_p3',
        
        # Programming Skills (Part 3)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 3)': 'prog_1_p3',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 3)': 'prog_2_p3',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 3)': 'prog_3_p3',
        'How well can you analyze and optimize the performance of a program? (Part 3)': 'prog_4_p3',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 3)': 'prog_5_p3',
        
        # Data Science Skills (Part 3)
        'I am confident in using SQL and Python for data analysis and database queries (Part 3)': 'ds_1_p3',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 3)': 'ds_2_p3',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 3)': 'ds_3_p3',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 3)': 'ds_4_p3',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 3)': 'ds_5_p3',

        # Digital Literacy Skills (Part 4)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 4)': 'dl_1_p4',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 4)': 'dl_2_p4',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 4)': 'dl_3_p4',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 4)': 'dl_4_p4',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 4)': 'dl_5_p4',
        
        # Programming Skills (Part 4)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 4)': 'prog_1_p4',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 4)': 'prog_2_p4',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 4)': 'prog_3_p4',
        'How well can you analyze and optimize the performance of a program? (Part 4)': 'prog_4_p4',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 4)': 'prog_5_p4',
        
        # Data Science Skills (Part 4)
        'I am confident in using SQL and Python for data analysis and database queries (Part 4)': 'ds_1_p4',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 4)': 'ds_2_p4',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 4)': 'ds_3_p4',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 4)': 'ds_4_p4',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 4)': 'ds_5_p4',

        # Digital Literacy Skills (Part 5)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 5)': 'dl_1_p5',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 5)': 'dl_2_p5',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 5)': 'dl_3_p5',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 5)': 'dl_4_p5',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 5)': 'dl_5_p5',
        
        # Programming Skills (Part 5)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 5)': 'prog_1_p5',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 5)': 'prog_2_p5',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 5)': 'prog_3_p5',
        'How well can you analyze and optimize the performance of a program? (Part 5)': 'prog_4_p5',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 5)': 'prog_5_p5',
        
        # Data Science Skills (Part 5)
        'I am confident in using SQL and Python for data analysis and database queries (Part 5)': 'ds_1_p5',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 5)': 'ds_2_p5',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 5)': 'ds_3_p5',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 5)': 'ds_4_p5',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 5)': 'ds_5_p5',

        # Digital Literacy Skills (Part 6)
        'How confident are you in evaluating the credibility of online sources and citing information ethically for academic projects? (Part 6)': 'dl_1_p6',
        'How well do you practice safe, legal, and responsible use of technology, including respecting copyright and maintaining online privacy? (Part 6)': 'dl_2_p6',
        'How effectively can you use digital tools to analyze problems, manage projects, and make informed decisions? (Part 6)': 'dl_3_p6',
        'How comfortable are you with learning new technologies, troubleshooting technical issues, and adapting to emerging software platforms? (Part 6)': 'dl_4_p6',
        'How proficient are you at creating digital content and communicating technical information to different audiences using various digital media? (Part 6)': 'dl_5_p6',
        
        # Programming Skills (Part 6)
        'How confident are you in your ability to design and implement algorithms to solve complex problems? (Part 6)': 'prog_1_p6',
        'How comfortable are you with version control systems like Git for managing and collaborating on code projects? (Part 6)': 'prog_2_p6',
        'How proficient are you at writing unit tests and ensuring code reliability through test-driven development (TDD)? (Part 6)': 'prog_3_p6',
        'How well can you analyze and optimize the performance of a program? (Part 6)': 'prog_4_p6',
        'How comfortable are you with integrating external libraries, APIs, or frameworks into your programming projects? (Part 6)': 'prog_5_p6',
        
        # Data Science Skills (Part 6)
        'I am confident in using SQL and Python for data analysis and database queries (Part 6)': 'ds_1_p6',
        'I can effectively process and analyze large datasets using big data tools like Hadoop, Spark, and Hive (Part 6)': 'ds_2_p6',
        'I am comfortable applying machine learning techniques and algorithms like logistic regression and supervised learning to solve data-driven problems (Part 6)': 'ds_3_p6',
        'I can manage and maintain databases using tools such as MySQL, R, and data administration techniques (Part 6)': 'ds_4_p6',
        'I can prepare and present data-driven insights using data visualization and reporting tools like Excel, PPT, and dashboards (Part 6)': 'ds_5_p6'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    return df


def clean_unnecessary_columns(df):
    """Remove unnecessary columns from the dataset."""
    print("Removing unnecessary columns...")
    columns_to_drop = ["Timestamp", "Do you agree with the statement above?"]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')
    return df


def generate_student_identifiers(df):
    """Generate unique student IDs and anonymized emails."""
    print("Generating student identifiers...")
    
    # Generate anonymized unique emails
    df['email'] = [f'student{i+1}@gmail.com' for i in range(len(df))]
    
    # Generate unique student IDs
    student_ids = set()
    while len(student_ids) < len(df):
        id_str = '202' + str(random.randint(2, 5)) + ''.join([str(random.randint(0, 9)) for _ in range(6)])
        student_ids.add(id_str)
    
    df['student_id'] = list(student_ids)
    return df


def generate_student_names(df):
    """Generate random Malaysian names based on gender."""
    print("Generating student names...")
    
    male_first_names = ['Ahmad', 'Aqil', 'Danial', 'Faiz', 'Hakim', 'Irfan', 'Kamal', 'Rizwan']
    female_first_names = ['Aisyah', 'Nurul', 'Siti', 'Zulaikha', 'Farah', 'Hannah', 'Amira', 'Liyana']
    last_names = ['Ismail', 'Rahman', 'Hassan', 'Yusof', 'Abdullah', 'Khalid', 'Latif']
    
    def generate_first_last_name(gender):
        gender = str(gender).strip().lower()
        if gender == 'male':
            first = random.choice(male_first_names)
        else:
            first = random.choice(female_first_names)
        
        last = random.choice(last_names)
        return first, last
    
    first_names = []
    last_names_list = []
    
    for gender in df['gender']:
        first, last = generate_first_last_name(gender)
        first_names.append(first)
        last_names_list.append(last)
    
    df['first_name'] = first_names
    df['last_name'] = last_names_list
    
    return df


def generate_malaysia_phone():
    """Generate random Malaysian phone numbers."""
    prefixes = ['010', '011', '012', '013', '014', '016', '017', '018', '019']
    prefix = random.choice(prefixes)
    if prefix == '011':
        number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    else:
        number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}-{number}"



def add_common_fields(df):
    """Add common fields for all students."""
    print("Adding common institutional fields...")
    
    df['password'] = '123'
    df['institution_name'] = 'UiTM Kampus Jasin'
    df['faculty_name'] = 'FSKM'
    df['program_code'] = 'CDCS230'
    df['status'] = 'Incomplete'
    df['address'] = 'UiTM Kampus Jasin'
    df['phone_number'] = [generate_malaysia_phone() for _ in range(len(df))]

    
    return df


def reorder_dataframe_columns(df):
    """Reorder columns to match expected database structure."""
    print("Reordering columns...")
    
    basic_columns = ['student_id', 'password', 'email', 'first_name', 'last_name', 'gender', 'phone_number', 
                    'institution_name', 'faculty_name', 'program_code', 'part', 'status', 'address']
    
    # Get all other columns (academic and skill scores)
    other_columns = [col for col in df.columns if col not in basic_columns]
    
    # Reorder DataFrame
    df = df[basic_columns + other_columns]
    return df


def validate_data_quality(df):
    """Validate data quality and check for duplications."""
    print("Validating data quality...")
    
    student_id_duplicated = df['student_id'].duplicated().any()
    email_duplicated = df['email'].duplicated().any()
    
    print(f"Student ID duplicated: {student_id_duplicated}")
    print(f"Student Email duplicated: {email_duplicated}")
    print(f"DataFrame shape: {df.shape}")
    print(f"Total columns: {len(df.columns)}")
    
    return df


def save_cleaned_data(df, output_path):
    """Save the cleaned dataset to CSV."""
    print(f"Saving cleaned data to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Data has been successfully cleaned and saved.")


def main():
    """Main function to orchestrate the data cleaning process."""
    # Configuration
    input_file = "C:/Users/aqima/OneDrive/Desktop/PROJECT/skillytics/data/original-data.csv"
    output_file = "C:/Users/aqima/OneDrive/Desktop/PROJECT/skillytics/data/clean-data.csv"
    
    print("Starting data cleaning process...")
    print("=" * 50)
    
    # Step 1: Load and preprocess data
    df = load_and_preprocess_data(input_file)
    
    # Step 2: Rename columns to match schema
    df = rename_columns_to_schema(df)
    
    # Step 3: Clean unnecessary columns
    df = clean_unnecessary_columns(df)
    
    # Step 4: Generate student identifiers
    df = generate_student_identifiers(df)
    
    # Step 5: Generate student names
    df = generate_student_names(df)
    
    # Step 6: Add common fields
    df = add_common_fields(df)
    
    # Step 7: Reorder columns
    df = reorder_dataframe_columns(df)
    
    # Step 8: Sort by index for consistency
    df = df.sort_index()
    
    # Step 9: Validate data quality
    df = validate_data_quality(df)
    
    # Step 10: Save cleaned data
    save_cleaned_data(df, output_file)
    
    print("=" * 50)
    print("Data cleaning process completed successfully!")


if __name__ == "__main__":
    main()