import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import requests
from io import BytesIO
import re
from bs4 import BeautifulSoup

# Set Seaborn style for better visuals
sns.set_style("whitegrid")
sns.set_context("talk")  # Increase font sizes

# GitHub URLs for your files (replace with your actual URLs)
COURSES_URL = "https://github.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/raw/main/data/courses.xlsx"
CLEANEDJOBS_URL = "https://github.com/MadhuVanthiSankarGanesh/SkillMatch-Dashboard/raw/main/data/cleaned_jobs.xlsx"

# Function to fetch Excel files from GitHub
def load_excel_data():
    try:
        # Load the cleaned jobs data from the .xls file
        cleaned_jobs_data = pd.read_excel('path_to_cleanedjobs.xls', sheet_name='your_sheet_name')
        # Load the course data from the .xls file
        course_data = pd.read_excel('path_to_courses.xls', sheet_name='your_sheet_name')
        
        # Ensure the 'extracted_skills' column exists in both datasets, if applicable
        if 'extracted_skills_text' in cleaned_jobs_data.columns:
            cleaned_jobs_data['extracted_skills'] = cleaned_jobs_data['extracted_skills_text'].apply(clean_and_extract_skills)
        if 'extracted_skills' in course_data.columns:
            course_data['extracted_skills'] = course_data['extracted_skills'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        
        return cleaned_jobs_data, course_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()
# Function to clean and extract skills
def clean_and_extract_skills(input_text):
    if not isinstance(input_text, str):
        return []
    input_text = re.sub(r'^[{}]+|[{}]+$', '', input_text)  # Remove curly braces if any
    input_text = re.sub(r'\b(bold,?\s*)', '', input_text, flags=re.IGNORECASE)  # Remove unwanted word
    input_text = input_text.replace('"', '')  # Clean any quotes
    return [skill.strip() for skill in input_text.split(',') if skill.strip()]

# Function to clean and format course descriptions
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

# Function to generate a wordcloud
def generate_wordcloud(data, column, title):
    if column not in data.columns:
        st.error(f"Column '{column}' does not exist in the data.")
        return  # Skip the function if the column doesn't exist
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

# Process the data
if not courses_data.empty:
    if 'extracted_skills' in courses_data.columns:
        courses_data['extracted_skills'] = courses_data['extracted_skills'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    if 'description' in courses_data.columns:
        courses_data['cleaned_description'] = courses_data['description'].apply(clean_and_format_description)

if not cleaned_jobs_data.empty:
    if 'extracted_skills_text' in cleaned_jobs_data.columns:
        cleaned_jobs_data['extracted_skills'] = cleaned_jobs_data['extracted_skills_text'].apply(clean_and_extract_skills)

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

# Display cleaned jobs data and visualizations
if page == "Jobs Data":
    st.header("Cleaned Jobs Data")
    st.dataframe(cleaned_jobs_data)
    st.write("### Skills Analysis")
    generate_wordcloud(cleaned_jobs_data, 'extracted_skills', "Word Cloud of Job Skills")

    skills = cleaned_jobs_data['extracted_skills'].explode()
    skill_counts = skills.value_counts().head(5)
    plt.figure(figsize=(12, 6))
    sns.barplot(x=skill_counts.values, y=skill_counts.index, palette='viridis')
    plt.title("Top 5 Skills in Job Postings", fontsize=20)
    plt.xlabel("Count", fontsize=16)
    plt.ylabel("Skill", fontsize=16)
    st.pyplot(plt)

# Display courses data and visualizations
elif page == "Courses Data":
    st.header("Courses Data")
    relevant_columns = ['title', 'rating', 'num_reviews', 'price', 'extracted_skills']
    displayed_columns = [col for col in relevant_columns if col in courses_data.columns]
    st.dataframe(courses_data[displayed_columns])  # Display only relevant columns

    generate_wordcloud(courses_data, 'extracted_skills', "Word Cloud of Course Skills")

elif page == "Insights & Visualizations":
    st.header("Insights & Visualizations")
    
    if 'rating' in courses_data.columns and 'num_reviews' in courses_data.columns:
        plt.figure(figsize=(12, 6))
        sns.scatterplot(data=courses_data, x='num_reviews', y='rating', s=100)
        plt.title("Ratings vs Number of Reviews", fontsize=20)
        st.pyplot(plt)

    if 'med_salary' in cleaned_jobs_data.columns:
        plt.figure(figsize=(12, 6))
        sns.histplot(cleaned_jobs_data['med_salary'].dropna(), bins=20, kde=True, color='blue')
        plt.title("Distribution of Median Salaries", fontsize=20)
        plt.xlabel("Median Salary", fontsize=16)
        plt.ylabel("Frequency", fontsize=16)
        st.pyplot(plt)

    if 'work_type' in cleaned_jobs_data.columns:
        plt.figure(figsize=(12, 6))
        sns.countplot(y=cleaned_jobs_data['work_type'], palette='coolwarm')
        plt.title("Distribution of Work Types", fontsize=20)
        st.pyplot(plt)

elif page == "Course Recommendation System":
    st.header("Course Recommendation System")
    st.write("### Find Courses Based on Skills")

    all_skills = courses_data['extracted_skills'].explode().dropna().unique()
    selected_skills = st.multiselect("Select skills:", sorted(all_skills))

    if selected_skills:
        recommended_courses = courses_data[courses_data['extracted_skills'].apply(lambda skills: all(skill in skills for skill in selected_skills))]
        
        if not recommended_courses.empty:
            st.write("### Recommended Courses")
            for _, course in recommended_courses.iterrows():
                st.write(course['title'])

        else:
            st.write("No matching courses found.")

elif page == "Skill Gap Analysis":
    st.header("Skill Gap Analysis")
    st.write("### Analyze Skill Gaps for a Job")

    selected_job = st.selectbox("Select a Job:", cleaned_jobs_data['title'].unique())

    if selected_job:
        job_skills = cleaned_jobs_data[cleaned_jobs_data['title'] == selected_job]['extracted_skills'].explode().dropna().unique()
        st.write(f"### Skills Required for {selected_job}")
        st.write(job_skills)

        selected_skill = st.selectbox("Select a Skill from the Job:", job_skills)

        if selected_skill:
            st.write(f"### Courses Covering Related Skills to: {selected_skill}")

            all_course_skills = courses_data['extracted_skills'].explode().dropna().unique()
            matching_courses = courses_data[courses_data['extracted_skills'].apply(lambda skills: selected_skill in skills)]

            if not matching_courses.empty:
                for _, course in matching_courses.iterrows():
                    st.write(course['title'])
            else:
                st.write("No matching courses found.")
