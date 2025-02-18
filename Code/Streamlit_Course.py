import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import psycopg2
import re
from rapidfuzz import process, fuzz
from bs4 import BeautifulSoup

# Set Seaborn style for better visuals
sns.set_style("whitegrid")
sns.set_context("talk")  # Increase font sizes

db_config = {
    "dbname": st.secrets["postgres"]["dbname"],
    "user": st.secrets["postgres"]["user"],
    "password": st.secrets["postgres"]["password"],
    "host": st.secrets["postgres"]["host"],
    "port": st.secrets["postgres"]["port"]
}
def create_connection(db_config):
    try:
        connection = psycopg2.connect(**db_config)
        print("Database connection successful.")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def fetch_cleaned_jobs_data(connection):
    try:
        query = """
        SELECT 
            job_id, 
            title, 
            company_name,
            company_id,
            description,
            max_salary,
            pay_period,
            location, 
            med_salary,
            min_salary,
            formatted_work_type,
            remote_allowed,
            work_type, 
            extracted_skills::TEXT AS extracted_skills_text 
        FROM cleaned_jobs_with_skills_final1;
        """
        return pd.read_sql_query(query, connection)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def fetch_course_data(connection):
    try:
        query = "SELECT * FROM course_data;"
        return pd.read_sql_query(query, connection)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def clean_and_extract_skills(input_text):
    if not isinstance(input_text, str):
        return []
    input_text = re.sub(r'^[{}]+|[{}]+$', '', input_text)
    input_text = re.sub(r'\b(bold,?\s*)', '', input_text, flags=re.IGNORECASE)
    input_text = input_text.replace('"', '')
    return [skill.strip() for skill in input_text.split(',') if skill.strip()]

# Change the clean_and_format_description function to handle the HTML formatting more effectively
def clean_and_format_description(html_text):
    """Cleans HTML tags and formats a course description for better readability."""
    
    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")

    # Extract text while keeping bullet points and formatting
    text = soup.get_text(separator="\n")  

    # Remove excessive blank lines
    text = re.sub(r'\n+', '\n', text).strip()

    # Add spacing after punctuation if missing
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)  

    # Format bullet points
    text = text.replace("•", "- ")  

    return text


def display_course_details(course):
    """Displays course details in a formatted card in Streamlit."""
    st.markdown(f"""
    <div style="border: 2px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
        <h4 style="color: #2C3E50;">{course['title']}</h4>
        <p><strong>Rating:</strong> {course['rating']} ⭐ | <strong>Reviews:</strong> {course['num_reviews']}</p>
        <p><strong>Price:</strong> {course['price']}</p>
        <p><strong>Headline:</strong> {course['headline']}</p>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    connection = create_connection(DB_CONFIG)
    if not connection:
        st.error("Unable to connect to the database.")
        return pd.DataFrame(), pd.DataFrame()
    try:
        cleaned_jobs_data = fetch_cleaned_jobs_data(connection)
        course_data = fetch_course_data(connection)
        if 'extracted_skills_text' in cleaned_jobs_data.columns:
            cleaned_jobs_data['extracted_skills'] = cleaned_jobs_data['extracted_skills_text'].apply(clean_and_extract_skills)
        if 'extracted_skills' in course_data.columns:
            course_data['extracted_skills'] = course_data['extracted_skills'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        return cleaned_jobs_data, course_data
    finally:
        connection.close()

def generate_wordcloud(data, column, title):
    text = ' '.join([word for words in data[column].dropna() for word in words])
    wordcloud = WordCloud(background_color='white', colormap='viridis', width=1000, height=500).generate(text)
    plt.figure(figsize=(12, 7))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title, fontsize=20)
    st.pyplot(plt)

cleaned_jobs, course_data = load_data()

st.title("Interactive Data Dashboard")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page:", [
    "Jobs Data",
    "Courses Data",
    "Insights & Visualizations",
    "Course Recommendation System",
    "Skill Gap Analysis"
])

if page == "Jobs Data":
    st.header("Cleaned Jobs Data")
    st.dataframe(cleaned_jobs)
    st.write("### Skills Analysis")
    generate_wordcloud(cleaned_jobs, 'extracted_skills', "Word Cloud of Job Skills")
    
    skills = cleaned_jobs['extracted_skills'].explode()
    skill_counts = skills.value_counts().head(5)
    plt.figure(figsize=(12, 6))
    sns.barplot(x=skill_counts.values, y=skill_counts.index, palette='viridis')
    plt.title("Top 5 Skills in Job Postings", fontsize=20)
    plt.xlabel("Count", fontsize=16)
    plt.ylabel("Skill", fontsize=16)
    st.pyplot(plt)

elif page == "Courses Data":
    st.header("Courses Data")

    # Select only relevant columns to display
    relevant_columns = ['title', 'rating', 'num_reviews', 'price', 'extracted_skills']
    displayed_columns = [col for col in relevant_columns if col in course_data.columns]

    st.dataframe(course_data[displayed_columns])  # Display only relevant columns

    generate_wordcloud(course_data, 'extracted_skills', "Word Cloud of Course Skills")


elif page == "Insights & Visualizations":
    st.header("Insights & Visualizations")
    
    if 'rating' in course_data.columns and 'num_reviews' in course_data.columns:
        plt.figure(figsize=(12, 6))
        sns.scatterplot(data=course_data, x='num_reviews', y='rating', s=100)
        plt.title("Ratings vs Number of Reviews", fontsize=20)
        st.pyplot(plt)

    if 'med_salary' in cleaned_jobs.columns:
        plt.figure(figsize=(12, 6))
        sns.histplot(cleaned_jobs['med_salary'].dropna(), bins=20, kde=True, color='blue')
        plt.title("Distribution of Median Salaries", fontsize=20)
        plt.xlabel("Median Salary", fontsize=16)
        plt.ylabel("Frequency", fontsize=16)
        st.pyplot(plt)

    if 'work_type' in cleaned_jobs.columns:
        plt.figure(figsize=(12, 6))
        sns.countplot(y=cleaned_jobs['work_type'], palette='coolwarm')
        plt.title("Distribution of Work Types", fontsize=20)
        st.pyplot(plt)

    if 'max_salary' in cleaned_jobs.columns and 'min_salary' in cleaned_jobs.columns:
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=cleaned_jobs[['min_salary', 'max_salary']])
        plt.title("Salary Range Distribution", fontsize=20)
        st.pyplot(plt)

    if 'num_reviews' in course_data.columns:
        plt.figure(figsize=(12, 6))
        sns.histplot(course_data['num_reviews'], bins=20, kde=True, color='green')
        plt.title("Distribution of Course Reviews", fontsize=20)
        st.pyplot(plt)
elif page == "Course Recommendation System":
    st.header("Course Recommendation System")
    st.write("### Find Courses Based on Skills")

    all_skills = course_data['extracted_skills'].explode().dropna().unique()
    selected_skills = st.multiselect("Select skills:", sorted(all_skills))

    if selected_skills:
        recommended_courses = course_data[course_data['extracted_skills'].apply(lambda skills: all(skill in skills for skill in selected_skills))]
        
        if not recommended_courses.empty:
            st.write("### Recommended Courses")
            for _, course in recommended_courses.iterrows():
                display_course_details(course)
        else:
            st.write("No matching courses found.")

elif page == "Skill Gap Analysis":
    st.header("Skill Gap Analysis")
    st.write("### Analyze Skill Gaps for a Job")

    selected_job = st.selectbox("Select a Job:", cleaned_jobs['title'].unique())

    if selected_job:
        job_skills = cleaned_jobs[cleaned_jobs['title'] == selected_job]['extracted_skills'].explode().dropna().unique()
        st.write(f"### Skills Required for {selected_job}")
        st.write(job_skills)

        selected_skill = st.selectbox("Select a Skill from the Job:", job_skills)

        if selected_skill:
            st.write(f"### Courses Covering Related Skills to: {selected_skill}")

            all_course_skills = course_data['extracted_skills'].explode().dropna().unique()
            similar_skills = [match for match, score, _ in process.extract(selected_skill, all_course_skills, scorer=fuzz.ratio) if score >= 70]

            if similar_skills:
                st.write(f"Matched Skills: {similar_skills}")

                matching_courses = course_data[course_data['extracted_skills'].apply(lambda skills: any(skill in skills for skill in similar_skills))]

                if not matching_courses.empty:
                    for _, course in matching_courses.iterrows():
                        display_course_details(course)
                else:
                    st.write("No matching courses found.")
            else:
                st.write("No similar skills found.")
