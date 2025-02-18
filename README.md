# Interactive Data Dashboard with Skill Gap Analysis and Course Recommendations

## Overview
This project is an interactive data dashboard built with **Streamlit**, designed to analyze job market trends, skill gaps, and recommend relevant courses based on job descriptions. It integrates data from various sources and presents key insights using **data visualization, word clouds, and skill-matching algorithms**.
**Dashboard Link :** https://skillmatch-dashboard-mb9vylrejen9rn9yms8awf.streamlit.app/

## Data Sources
- **Udemy API**: Used to collect online course data, including ratings, reviews, pricing, and skill coverage.
- **LinkedIn Job Dataset (Kaggle)**: A dataset containing job postings, salaries, required skills, and work types.
- **MongoDB Storage**: Initially, the raw data from Udemy and LinkedIn was stored in MongoDB for easy retrieval and preprocessing.
- **PostgreSQL Database**: After extracting relevant skills from job descriptions and course descriptions using **GPTforALL**, the cleaned data was stored in PostgreSQL.

## Features
### 1. **Jobs Data Visualization**
- Displays a **cleaned dataset** of job postings.
- Generates **word clouds** of job skills.
- Visualizes the **top 5 in-demand skills** using bar charts.

### 2. **Courses Data Visualization**
- Displays **relevant course information**.
- Generates a **word cloud of course skills**.

### 3. **Insights & Visualizations**
- **Salary distribution** analysis.
- **Job work type** distribution.
- **Course ratings vs. reviews** scatter plot.
- **Salary range distribution** via boxplots.

### 4. **Course Recommendation System**
- Users can **select skills** they want to learn.
- Recommends courses that **match the selected skills**.

### 5. **Skill Gap Analysis**
- Users can select a **job title** to view required skills.
- Matches **missing skills** with courses.
- Uses **fuzzy matching (RapidFuzz)** to suggest courses based on similar skills.

## Technologies Used
- **Python** (Streamlit, Pandas, Seaborn, Matplotlib, RapidFuzz, WordCloud, BeautifulSoup, Psycopg2)
- **MongoDB** (Initial storage of raw datasets)
- **PostgreSQL** (Final structured storage of cleaned data)
- **GPTforALL** (Extracted skills from job and course descriptions)
- **Udemy API** (Fetched course data)
- **LinkedIn Job Dataset (Kaggle)** (Job postings dataset)

