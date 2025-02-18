import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
from bs4 import BeautifulSoup

# Set Seaborn style for better visuals
sns.set_style("whitegrid")
sns.set_context("talk")  # Increase font sizes

# GitHub URLs for your files (replace with actual URLs)
COURSES_URL = "https://github.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/raw/main/data/courses.xlsx"
CLEANEDJOBS_URL = "https://github.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/blob/main/data/cleaned_jobs.xls"

# Function to fetch Excel files from GitHub
def load_excel_data(file_path):
    try:
        data = pd.read_excel(file_path)
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Function to clean and extract skills
def clean_and_extract_skills(input_text):
    if not isinstance(input_text, str):
        return []
    input_text = re.sub(r'^[{}]+|[{}]+$', '', input_text)
    input_text = re.sub(r'\b(bold,?\s*)', '', input_text, flags=re.IGNORECASE)
    input_text = input_text.replace('"', '')
    return [skill.strip() for skill in input_text.split(',') if skill.strip()]

# Function to clean and format course descriptions
def clean_and_format_description(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n+', '\n', text).strip()
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    text = text.replace("•", "- ")
    return text

# Function to generate a word cloud
def generate_wordcloud(data, column, title):
    if column not in data.columns:
        st.error(f"Column '{column}' does not exist in the data.")
        return
    text = ' '.join([word for words in data[column].dropna() for word in words])
    wordcloud = WordCloud(background_color='white', colormap='viridis', width=1000, height=500).generate(text)
    plt.figure(figsize=(12, 7))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title, fontsize=20)
    st.pyplot(plt)

# Load data from GitHub
courses_data = load_excel_data(COURSES_URL)
cleaned_jobs_data = load_excel_data(CLEANEDJOBS_URL)

# Debugging: Print available columns
st.write("Columns in cleaned_jobs_data:", cleaned_jobs_data.columns.tolist())
st.write("Preview of cleaned_jobs_data:", cleaned_jobs_data.head())  # Show first few rows


# Check if data is loaded correctly
if not courses_data.empty:
    last_column_name_courses = courses_data.columns[-1]
    if 'description' in courses_data.columns:
        courses_data['cleaned_description'] = courses_data['description'].apply(clean_and_format_description)

if not cleaned_jobs_data.empty:
    last_column_name_jobs = cleaned_jobs_data.columns[-1]
    if 'extracted_skills_text' in cleaned_jobs_data.columns:
        cleaned_jobs_data['extracted_skills'] = cleaned_jobs_data['extracted_skills_text'].apply(clean_and_extract_skills)
    else:
        st.error("Column 'extracted_skills_text' not found in cleaned jobs dataset.")

# Streamlit app layout
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
    st.dataframe(cleaned_jobs_data)
    st.write("### Skills Analysis")
    if 'extracted_skills' in cleaned_jobs_data.columns:
        generate_wordcloud(cleaned_jobs_data, 'extracted_skills', "Word Cloud of Job Skills")
        skills = cleaned_jobs_data['extracted_skills'].explode()
        skill_counts = skills.value_counts().head(5)
        plt.figure(figsize=(12, 6))
        sns.barplot(x=skill_counts.values, y=skill_counts.index, palette='viridis')
        plt.title("Top 5 Skills in Job Postings", fontsize=20)
        plt.xlabel("Count", fontsize=16)
        plt.ylabel("Skill", fontsize=16)
        st.pyplot(plt)
    else:
        st.error("No extracted skills available in the dataset.")

elif page == "Courses Data":
    st.header("Courses Data")
    st.dataframe(courses_data)
    if 'title' in courses_data.columns:
        generate_wordcloud(courses_data, last_column_name_courses, "Word Cloud of Course Skills")

elif page == "Insights & Visualizations":
    st.header("Insights & Visualizations")
    if 'rating' in courses_data.columns and 'num_reviews' in courses_data.columns:
        plt.figure(figsize=(12, 6))
        sns.scatterplot(data=courses_data, x='num_reviews', y='rating', s=100)
        plt.title("Ratings vs Number of Reviews", fontsize=20)
        st.pyplot(plt)

elif page == "Course Recommendation System":
    st.header("Course Recommendation System")
    if last_column_name_courses in courses_data.columns:
        all_skills = courses_data[last_column_name_courses].explode().dropna().unique()
        selected_skills = st.multiselect("Select skills:", sorted(all_skills))
        if selected_skills:
            recommended_courses = courses_data[courses_data[last_column_name_courses].apply(lambda skills: all(skill in skills for skill in selected_skills))]
            if not recommended_courses.empty:
                for _, course in recommended_courses.iterrows():
                    st.write(course['title'])
            else:
                st.write("No matching courses found.")

elif page == "Skill Gap Analysis":
    st.header("Skill Gap Analysis")
    if 'title' in cleaned_jobs_data.columns and 'extracted_skills' in cleaned_jobs_data.columns:
        selected_job = st.selectbox("Select a Job:", cleaned_jobs_data['title'].unique())
        if selected_job:
            job_skills = cleaned_jobs_data[cleaned_jobs_data['title'] == selected_job]['extracted_skills'].explode().dropna().unique()
            st.write(f"### Skills Required for {selected_job}")
            st.write(job_skills)
            selected_skill = st.selectbox("Select a Skill from the Job:", job_skills)
            if selected_skill and last_column_name_courses in courses_data.columns:
                matching_courses = courses_data[courses_data[last_column_name_courses].apply(lambda skills: selected_skill in skills)]
                if not matching_courses.empty:
                    for _, course in matching_courses.iterrows():
                        st.write(course['title'])
                else:
                    st.write("No matching courses found.")
    else:
        st.error("Jobs dataset does not have necessary columns.")
