import os
import psycopg2
import psycopg2.extras
from gpt4all import GPT4All
import re
import json
from datetime import datetime

# GPU configuration
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU

# Load GPT4All model
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")


def extract_skills_from_text(text):
    """
    Extract skills using the GPT4All model.
    """
    with model.chat_session():
        response = model.generate(
             f"Identify the key skills from the following job description. "
            f"Only list the main technical skills in bold (e.g., **skill**) with no additional formatting, titles, bullet points, or explanations."
            f"'{text}'",
            max_tokens=1024,
        )
    return response


def extract_skills_from_response(job_description):
    """
    Extract skills enclosed in ** ** from the GPT4All response.
    """
    response = extract_skills_from_text(job_description)
    skill_pattern = r"\*\*(.*?)\*\*"
    matches = re.findall(skill_pattern, response)
    return [match.strip() for match in matches]


def get_postgres_connection():
    """
    Establish a connection to PostgreSQL.
    """
    return psycopg2.connect(
        dbname="CourseDashboard_final",
        user="postgres",
        password="HelloWorld_1",
        host="localhost",
        port="5432",
    )

def sanitize_field_extracted_skills(value):
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

def create_table_if_not_exists():
    """
    Create the cleaned_jobs_with_skills table if it does not exist.
    """
    query = """
    CREATE TABLE IF NOT EXISTS cleaned_jobs_with_skills_final2 (
        job_id TEXT PRIMARY KEY,
        company_name TEXT,
        title TEXT,
        description TEXT,
        max_salary FLOAT,
        pay_period TEXT,
        location TEXT,
        company_id TEXT,
        views INT,
        med_salary FLOAT,
        min_salary FLOAT,
        formatted_work_type TEXT,
        applies INT,
        original_listed_time TIMESTAMP,
        remote_allowed BOOLEAN,
        job_posting_url TEXT,
        application_url TEXT,
        application_type TEXT,
        expiry TIMESTAMP,
        closed_time TIMESTAMP,
        formatted_experience_level TEXT,
        skills_desc TEXT,
        listed_time TIMESTAMP,
        posting_domain TEXT,
        sponsored BOOLEAN,
        work_type TEXT,
        currency TEXT,
        compensation_type TEXT,
        normalized_salary FLOAT,
        zip_code TEXT,
        fips TEXT,
        extracted_skills TEXT[]
    );
    """
    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()


def job_exists_in_postgres(job_id):
    """
    Check if a job ID already exists in the cleaned_jobs_with_skills table.
    """
    query = "SELECT 1 FROM cleaned_jobs_with_skills_final2 WHERE job_id = %s;"
    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (job_id,))
            return cur.fetchone() is not None

import json
from datetime import datetime


def sanitize_field(value, is_extracted_skills=False):
    """
    Sanitize a field for PostgreSQL compatibility.
    Convert Unix timestamps to PostgreSQL timestamp and other data as needed.
    
    :param value: The value to be sanitized.
    :param is_extracted_skills: Flag indicating if the field is `extracted_skills` (list of skills).
    :return: Sanitized value for insertion into PostgreSQL.
    """
    if isinstance(value, dict):
        # If it's a dictionary, convert it to a JSON string
        return json.dumps(value)
    
    elif isinstance(value, list):
        # If it's a list, convert it to a JSON string
        return json.dumps(value)
    
    elif value is None:
        # Return None for missing or null values
        return None
    
    elif isinstance(value, str):
        # Check if it's a number stored as string and convert to float or int as required
        if value.replace('.', '', 1).isdigit() or (value.startswith('-') and value[1:].replace('.', '', 1).isdigit()):
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                return value  # If conversion fails, return the original string
        return value  # Return string as-is
    
    elif isinstance(value, float):
        # If it's a float, convert to int if it has no decimal part
        return int(value) if value.is_integer() else value
    
    elif isinstance(value, (int, float)) and (value > 1000000000 and value < 9999999999): 
        # Range check for Unix timestamps (valid timestamps)
        # Convert Unix timestamp (numeric) to PostgreSQL timestamp
        return datetime.utcfromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    
    elif is_extracted_skills and isinstance(value, list):
        # If it's the `extracted_skills` field and it's a list, sanitize each skill (string or dict)
        sanitized_skills = [sanitize_field(skill) for skill in value]
        return sanitized_skills
    
    return value  # Return the value if no special sanitization is needed




def insert_job_data(job_data, extracted_skills):
    """
    Insert job data into the cleaned_jobs_with_skills table.
    """
    query = """
        INSERT INTO cleaned_jobs_with_skills_final2 (
    job_id, company_name, title, description, max_salary, pay_period, location, company_id,
    views, med_salary, min_salary, formatted_work_type, applies, original_listed_time,
    remote_allowed, job_posting_url, application_url, application_type, expiry, closed_time,
    formatted_experience_level, skills_desc, listed_time, posting_domain, sponsored, work_type,
    currency, compensation_type, normalized_salary, zip_code, fips, extracted_skills
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TO_TIMESTAMP(%s),  CASE WHEN %s = 0 THEN FALSE ELSE TRUE END, %s, %s, %s, TO_TIMESTAMP(%s), TO_TIMESTAMP(%s), %s, %s, TO_TIMESTAMP(%s), %s, CASE WHEN %s = 0 THEN FALSE ELSE TRUE END, %s, %s, %s, %s, %s, %s ,%s
)
    """  
    
    # Create the values list by sanitizing fields
    values = [
        sanitize_field(job_data.get(field), is_extracted_skills=(field == 'extracted_skills'))
        for field in [
            "job_id", "company_name", "title", "description", "max_salary", "pay_period", "location",
            "company_id", "views", "med_salary", "min_salary", "formatted_work_type", "applies",
            "original_listed_time", "remote_allowed", "job_posting_url", "application_url",
            "application_type", "expiry", "closed_time", "formatted_experience_level", "skills_desc",
            "listed_time", "posting_domain", "sponsored", "work_type", "currency", "compensation_type",
            "normalized_salary", "zip_code", "fips"
        ]
    ]
    sanitized_skills = [sanitize_field_extracted_skills(skill) for skill in extracted_skills]
    # Add extracted_skills as an array
    print('Sanitised Skills', sanitized_skills)
    values.append(sanitized_skills)  # Add extracted skills as the last value
    
    # Debugging: Check length of placeholders and values
    print(f"Number of placeholders: {query.count('%s')}")
    print(f"Number of values: {len(values)}")
    
    # Print both to compare
    print(f"Query (length of %s placeholders): {query}")
    print(f"Values (length): {values}")
    
    if query.count('%s') != len(values):
        print("Mismatch in number of placeholders and values!")
        return  # Exit if there is a mismatch
    
    try:
        # Open the connection and use the cursor to execute the query
        with get_postgres_connection() as conn:
            with conn.cursor() as cur:  # Ensure cursor is properly opened
                cur.execute(query, values)  # Execute the query
                conn.commit()  # Commit the transaction
                print(f"Inserted job with ID: {job_data.get('job_id')}")
    except Exception as e:
        print(f"Error executing query: {e}")

def process_jobs():
    """
    Process all jobs, extract skills, and insert into the database.
    """
    create_table_if_not_exists()

    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM cleaned_jobs;")
            jobs = cur.fetchall()

            for job in jobs:
                job_id = job["job_id"]
                if job_exists_in_postgres(job_id):
                    print(f"Skipping job with ID: {job_id} (already exists)")
                    continue

                print(f"Processing job with ID: {job_id}")
                extracted_skills = extract_skills_from_response(job["description"] or "")
                print("Extracted skills:", extracted_skills)
                insert_job_data(job, extracted_skills)


# Run the processing function
if __name__ == "__main__":
    process_jobs()
