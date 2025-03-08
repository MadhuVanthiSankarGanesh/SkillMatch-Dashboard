import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import io
import requests
import re
from rapidfuzz import process, fuzz
from bs4 import BeautifulSoup

# Set Seaborn style for better visuals
sns.set_style("whitegrid")
sns.set_context("talk")

# GitHub file URLs
courses_data_file = "https://raw.githubusercontent.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/main/DataforDashboard/course_data_final.csv"
jobs_data_file = "https://raw.githubusercontent.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/main/DataforDashboard/cleaned_jobs_data_final.csv"

def fetch_data_from_github(url):
    """Fetches data from GitHub raw CSV URL."""
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))

# Fuzzy Matching for Skill Consolidation
def consolidate_skills(skills_list, threshold=80):
    consolidated = {}
    for skill in skills_list:
        matched = False
        for key in list(consolidated.keys()):
            if fuzz.token_set_ratio(skill.lower(), key.lower()) >= threshold:
                consolidated[key] += 1
                matched = True
                break
        if not matched:
            consolidated[skill] = 1
    return consolidated

# Clean and Extract Skills
def clean_and_extract_skills(input_text):
    if not isinstance(input_text, str):
        return []
    input_text = re.sub(r'^[{}]+|[{}]+$', '', input_text)
    input_text = re.sub(r'\b(bold,?\s*)', '', input_text, flags=re.IGNORECASE)
    input_text = input_text.replace('"', '')
    skills = [skill.strip() for skill in input_text.split(',') if skill.strip()]
    return list(set(skills))

# Clean HTML Tags from Description
def clean_and_format_description(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n+', '\n', text).strip()
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    text = text.replace("\u2022", "- ")
    return text

# Display Course Details
def display_course_details(course):
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
    try:
        jobs_data = fetch_data_from_github(jobs_data_file)
        courses_data = fetch_data_from_github(courses_data_file)

        # Clean and Extract Skills
        if 'extracted_skills' in jobs_data.columns:
            jobs_data['extracted_skills'] = jobs_data['extracted_skills'].apply(lambda x: clean_and_extract_skills(x))
        
        if 'extracted_skills' in courses_data.columns:
            courses_data['extracted_skills'] = courses_data['extracted_skills'].apply(lambda x: clean_and_extract_skills(x))

        return jobs_data, courses_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

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

    consolidated_skills = consolidate_skills(cleaned_jobs['extracted_skills'].explode().dropna().tolist())
    sorted_skills = sorted(consolidated_skills.items(), key=lambda x: x[1], reverse=True)
    skill_names, skill_counts = zip(*sorted_skills[:5])

    plt.figure(figsize=(12, 6))
    sns.barplot(x=skill_counts, y=skill_names, palette='viridis')
    plt.title("Top 5 Skills in Job Postings", fontsize=20)
    plt.xlabel("Count", fontsize=16)
    plt.ylabel("Skill", fontsize=16)
    st.pyplot(plt)

elif page == "Courses Data":
    st.header("Courses Data")
    relevant_columns = ['title', 'rating', 'num_reviews', 'price', 'extracted_skills']
    displayed_columns = [col for col in relevant_columns if col in course_data.columns]
    st.dataframe(course_data[displayed_columns])  
    generate_wordcloud(course_data, 'extracted_skills', "Word Cloud of Course Skills")
    
elif page == "Insights & Visualizations":
    st.header("Insights & Visualizations")

    # Job Skills Distribution
    st.subheader("Distribution of Job Skills")
    job_skills = consolidate_skills(cleaned_jobs['extracted_skills'].explode().dropna().tolist())
    sorted_job_skills = sorted(job_skills.items(), key=lambda x: x[1], reverse=True)[:10]
    skill_names, skill_counts = zip(*sorted_job_skills)

    plt.figure(figsize=(12, 6))
    sns.barplot(x=skill_counts, y=skill_names, palette='viridis')
    plt.title("Top 10 Skills in Job Postings", fontsize=20)
    plt.xlabel("Count", fontsize=16)
    plt.ylabel("Skill", fontsize=16)
    st.pyplot(plt)

    # Skill Comparison between Jobs and Courses
    st.subheader("Skill Comparison: Jobs vs Courses")
    job_skill_set = set(job_skills.keys())
    course_skills = consolidate_skills(course_data['extracted_skills'].explode().dropna().tolist())
    course_skill_set = set(course_skills.keys())

    matched_skills = job_skill_set & course_skill_set
    unmatched_job_skills = job_skill_set - course_skill_set
    unmatched_course_skills = course_skill_set - job_skill_set

    labels = ['Matched Skills', 'Job-Only Skills', 'Course-Only Skills']
    sizes = [len(matched_skills), len(unmatched_job_skills), len(unmatched_course_skills)]
    colors = ['#66b3ff', '#99ff99', '#ffcc99']
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title("Skill Overlap between Jobs and Courses", fontsize=20)
    st.pyplot(plt)

    # Course Ratings vs Reviews
    st.subheader("Course Ratings vs Number of Reviews")
    if 'rating' in course_data.columns and 'num_reviews' in course_data.columns:
        plt.figure(figsize=(12, 6))
        sns.scatterplot(data=course_data, x='num_reviews', y='rating', s=100)
        plt.title("Ratings vs Number of Reviews", fontsize=20)
        st.pyplot(plt)

    # Salary Distribution
    st.subheader("Salary Distribution")
    if 'med_salary' in cleaned_jobs.columns:
        plt.figure(figsize=(12, 6))
        sns.histplot(cleaned_jobs['med_salary'].dropna(), bins=20, kde=True, color='blue')
        plt.title("Distribution of Median Salaries", fontsize=20)
        st.pyplot(plt)

    # Work Type Distribution
    st.subheader("Distribution of Work Types")
    if 'work_type' in cleaned_jobs.columns:
        plt.figure(figsize=(12, 6))
        sns.countplot(y=cleaned_jobs['work_type'], palette='coolwarm')
        plt.title("Distribution of Work Types", fontsize=20)
        st.pyplot(plt)

elif page == "Course Recommendation System":
    st.header("Course Recommendation System")
    st.write("### Find Courses Based on Skills")

    all_skills = list(consolidate_skills(course_data['extracted_skills'].explode().dropna().tolist()).keys())
    selected_skills = st.multiselect("Select skills:", sorted(all_skills))

    if selected_skills:
        recommended_courses = course_data[course_data['extracted_skills'].apply(
            lambda skills: all(any(fuzz.token_set_ratio(skill, s) >= 80 for s in skills) for skill in selected_skills)
        )]

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
        job_skills = list(consolidate_skills(
            cleaned_jobs[cleaned_jobs['title'] == selected_job]['extracted_skills'].explode().dropna().tolist()
        ).keys())
        
        st.write(f"### Skills Required for {selected_job}")
        st.write(job_skills)

        st.write("### Matching Courses")
        matching_courses = course_data[course_data['extracted_skills'].apply(
            lambda skills: any(any(fuzz.token_set_ratio(skill, s) >= 80 for s in skills) for skill in job_skills)
        )]

        if not matching_courses.empty:
            for _, course in matching_courses.iterrows():
                display_course_details(course)
        else:
            st.write("No matching courses found.")

