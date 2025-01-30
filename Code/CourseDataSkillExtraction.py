import os
import psycopg2
from pymongo import MongoClient
from gpt4all import GPT4All
import re
import json
import psycopg2.extras
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
# Initialize MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['udemy_courses_db']
collection = mongo_db['courseswithcategory']

# Load GPT4All model for skill extraction (GPU if possible)
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Clean and preprocess text
def clean_text(text):
    """
    Cleans the input text by removing HTML tags, special characters, and extra spaces.
    """
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    return text.lower().strip()

# Function to extract skills from the course text using GPT4All
def extract_skills_from_text(text):
    """
    Extract skills using the GPT4All model.
    """
    cleaned_text = clean_text(text)

    # Start a chat session with the model
    with model.chat_session():
        # Generate response for skill extraction
        response = model.generate(f"Extract the relevant technical skills from the following course description: '{cleaned_text}'", max_tokens=1024)
    
    # Assuming the response is a list of skills, we can directly use it (adjust as needed)
    skills = response.split(',')  # Split skills if returned in a comma-separated format
    skills = [skill.strip() for skill in skills]  # Clean up the list of skills

    return skills

# Function to extract skills enclosed in '** **' from a list of skills
def extract_skills_from_asterisks(skills):
    """
    Extract skills that are enclosed in ** ** from the list of skills.
    """
    # Regular expression to capture text between ** **
    skill_pattern = r"\*\*(.*?)\*\*"
    extracted_skills = []

    for skill in skills:
        matches = re.findall(skill_pattern, skill)
        extracted_skills.extend(matches)  # Add matched skills to the list

    return extracted_skills

# PostgreSQL connection setup
def get_postgres_connection():
    return psycopg2.connect(
        dbname="CourseDashboard_final",  # Update with your actual database name
        user="postgres",   # Update with your actual username
        password="****",  # Update with your actual password
        host="localhost", 
        port="5432"
    )

# Function to create PostgreSQL table (if it doesn't exist)
def create_table_if_not_exists():
    conn = get_postgres_connection()
    cur = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS course_data1 (
        _id TEXT PRIMARY KEY,  -- Changed from SERIAL to TEXT
        title TEXT,
        headline TEXT,
        description TEXT,
        rating FLOAT,
        num_reviews INT,
        price TEXT,
        num_subscribers INT,
        content_length_video INT,
        primary_category TEXT,
        extracted_skills TEXT[]
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()

# Check if a course exists in PostgreSQL
# Check if a course exists in PostgreSQL
def course_exists_in_postgres(course_id):
    conn = get_postgres_connection()
    cur = conn.cursor()
    query = "SELECT 1 FROM course_data1 WHERE _id = %s;"
    cur.execute(query, (str(course_id),))  # Convert ObjectId to string
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


# Function to sanitize fields before inserting into PostgreSQL
def sanitize_field(value):
    """
    Sanitize a field to ensure compatibility with PostgreSQL.
    - Convert `dict` to JSON string
    - Convert `list` to a semicolon-separated string
    - Handle `None` gracefully
    """
    if isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list):
        return ";".join(map(str, value))
    elif value is None:
        return None
    return value

# Function to insert data into PostgreSQL
def insert_course_data(course_data, extracted_skills):
    conn = get_postgres_connection()
    cur = conn.cursor()

    # Convert extracted_skills list to a semicolon-separated string
    sanitized_skills = [sanitize_field(skill) for skill in extracted_skills]

    # Debug: Print data being inserted
    print("Inserting Course Data:")
    for key, value in course_data.items():
        print(f"{key}: {value} (Type: {type(value)})")
    print("Sanitized Skills:", sanitized_skills)

    # Insert course data
    insert_query = """
    INSERT INTO course_data1 (_id, title, headline, description, rating, num_reviews, price, num_subscribers, content_length_video, primary_category, extracted_skills)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    cur.execute(insert_query, (
        str(course_data.get('_id')),  # Convert ObjectId to string
        sanitize_field(course_data.get('title')),
        sanitize_field(course_data.get('headline')),
        sanitize_field(course_data.get('description')),
        sanitize_field(course_data.get('rating')),
        sanitize_field(course_data.get('num_reviews')),
        sanitize_field(course_data.get('price')),
        sanitize_field(course_data.get('num_subscribers')),
        sanitize_field(course_data.get('content_length_video')),
        sanitize_field(course_data.get('primary_category')),
        sanitized_skills  # Pass as sanitized list
    ))

    conn.commit()
    cur.close()
    conn.close()


# Process documents from MongoDB and insert into PostgreSQL
def process_courses():
    # Set up PostgreSQL table if not exists
    create_table_if_not_exists()

    # Fetch courses from MongoDB one by one
    for course in collection.find():
        course_id = course['_id']

        # Check if course exists in PostgreSQL
        if course_exists_in_postgres(course_id):
            print(f"Skipping course with _id: {course_id} (already exists in PostgreSQL)")
            continue

        print(f"Processing course with _id: {course_id}")  # Debug: show current course being processed

        all_skills = []  # Initialize list to store extracted skills

        for field in ['title', 'headline', 'description']:
            if field in course and course[field]:  # Check if the field exists and is not empty
                print(f"Processing field '{field}'")  # Debug: Show field being processed

                # Extract skills from the current text field using GPT4All
                skills = extract_skills_from_text(course[field])
                all_skills.extend(skills)  # Collect all extracted skills

        # Remove duplicates from the skills list
        unique_skills = list(set(all_skills))

        # Extract skills enclosed in '** **' from the unique skills
        final_skills = extract_skills_from_asterisks(unique_skills)

        # Print the extracted skills for debugging
        print(f"Extracted Skills: {final_skills}")

        # Extract additional course details from the document
        course_data = {key: sanitize_field(course.get(key)) for key in [
            '_id', 'title', 'headline', 'description', 'rating', 'num_reviews', 
            'price', 'num_subscribers', 'content_length_video', 'primary_category']}

        # Insert the course data and extracted skills into PostgreSQL
        insert_course_data(course_data, final_skills)

# Run the process
process_courses()
