import streamlit as st
import sqlite3
import re
import ollama
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="PitchMate", page_icon="🪟", layout="wide")

# --- CSS Styling ---
st.markdown("""<style>
body { background-color: #121212; }
[data-testid="stSidebar"] { background-color: #1e1e1e; color: white; }
.sidebar-title { font-size: 24px; font-weight: bold; padding-bottom: 10px; color: #00ffb3; }
.st-emotion-cache-1c7y2kd, .st-emotion-cache-br351g, .st-emotion-cache-16tyu1, .st-emotion-cache-1xulwhk { color: white; }
.faq { padding: 10px 0; font-size: 15px; border-bottom: 1px solid #333; }
.chat-box { background-color: #1f1f1f; padding: 30px; border-radius: 10px; color: white; }
.stApp { background-color: #1c1c1e; color: #f2f2f2; }
html, body, [class*="css"] { color: #7e5a9b !important; }
.st-emotion-cache-1y34ygi, .st-emotion-cache-6qob1r { background: #27272f; color: #ffffff; }
header, .css-18ni7ap { background-color: #121212 !important; color: #e0e0e0 !important; }
.stTextInput input { background-color: #2b2b2b; color: white; border-radius: 8px; }
.stButton > button { background-color: #00ffb3; color: black; border-radius: 8px; padding: 8px 20px; }
h1, h2, h3, h4, h5 { color: white; }
</style>""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("Logo.png", use_container_width=True)
st.sidebar.markdown("<div class='sidebar-title'>PitchMate</div>", unsafe_allow_html=True)
function = st.sidebar.selectbox("Choose a function", [
    "Trainer Details",
    "Placement Stats",
    "Company Info",
    "DSCC Activities",
    "Project Showcase"
])

st.sidebar.markdown("Frequently Asked Prompts")
faq_prompts = [
    "1. Who are all the trainers available", 
    "2. Who are trainers from Hyderabad",
    "3. List trainers who are all data science coaches",
    "4. What are all the companies that visited for hiring",
    "5. How many people were placed in May 2025?",
    "6. Which companies visited for placement?",
    "7. How many students were placed in 2025",
]
for q in faq_prompts:
    st.sidebar.markdown(f"<div class='faq'>{q}</div>", unsafe_allow_html=True)

# --- Database Setup ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect('news.db', check_same_thread=False)
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS trainers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            profile TEXT,
            description TEXT,
            skillset TEXT,
            experience INTEGER,
            location TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY,
            month_year TEXT,
            placement_count INTEGER,
            avg_ctc REAL,
            success_rate REAL,
            location TEXT,
            batch TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            role TEXT,
            ctc_range TEXT,
            hiring_frequency TEXT,
            requirements TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dscc_activities (
            id INTEGER PRIMARY KEY,
            activity_name TEXT,
            description TEXT,
            cadence TEXT,
            winners TEXT,
            last_conducted TEXT,
            participation_count INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            project_title TEXT,
            topic TEXT,
            domain TEXT,
            difficulty_level TEXT
        )
    ''')

    # Insert sample trainer data if not present
    c.execute('SELECT COUNT(*) FROM trainers')
    if c.fetchone()[0] == 0:
        trainers = [
            ('Dhananjay Daharia', 'Data Science Coach', 'Skilled Data Science Coach with hands-on experience in healthcare. He helps teams and individuals navigate the full data lifecycle, from extraction to predictive modeling. With expertise in Machine Learning, Python, and dashboarding, he delivers insights that drive smarter decisions and real-world impact in the healthcare industry.', 'Python, Django, Flask', 6, 'Hyderabad'),
            ('Nikita Tandel', 'Data Science Coach', 'An analytics professional specializing in Machine Learning and Data Science trainings. She is experienced in training over 4500+ entry-level to highly experienced candidates. Well-versed with numerous analytical tools including Python, ML, Statistics, SAS, SQL, Tableau, Power BI. Strong background in management and customer relationship management.', 'Data Science, Python, ML', 11, 'Mumbai'),
            ('Raghaverndra BM', 'Cloud and Web Devlopment SME', 'Seasoned Data Science Coach and Senior Analyst. Skillful mentor and an aspiring data scientist, adept at simplifying intricate concepts for practical ', 'AWS, DevOps, Kubernetes', 9, 'Chennai'),
            ('Jeevan Raj', 'Data Science Coach', 'An accomplished Data Science Coach at Imarticus Learning. His spearheaded diverse responsibilities includes content creation, developing organizational dashboards, pioneering interview preparation sessions, and conducting webinars for learners nationwide.', 'JavaScript, React, Node.js', 4, 'Bangalore'),
            ('Karthik C', 'Head of DS&AI', 'Passionate AI professional with 13 years of expertise in Artificial Intelligence & Data Science. Key areas of expertise includes: Pricing Analytics, Problem Solving, Machine Learning (ML), Deep Learning (DL), Text-mining, Natural Language Processing (NLP), GenerativeAI (GenAI), Data Science Consulting, Technology training and establishing AI Centers of Excellence (CoE).', 'Deep Learning, NLP, Python', 12, 'Mumbai'),
            ('Amaan Adeen', 'Data Science Coach', 'Computer Science Engineer with a passion for data. Skilled in Python and machine learning, he applies EDA to improve Kaggle datasets and tune models for accuracy. With a background in Android development, he’s transitioning into data science, driven by curiosity and a passion for continuous learning.', 'Data Science, Python, ML', 6, 'Hyderabad'),
            ('Jagruti Pawashe', 'Machine Learning Coach', 'Proficient in Python and machine learning, he uses EDA to refine Kaggle datasets and optimize models. With experience in Android development, he’s making his move into data science, fueled by a love for learning and exploring new insights.', 'Python, Machine Learning, RAG automation', 8, 'Mumbai')
        ]
        c.executemany('INSERT INTO trainers (name, profile, description, skillset, experience, location) VALUES (?, ?, ?, ?, ?, ?)', trainers)

    # Sample data for other tables
    c.execute('SELECT COUNT(*) FROM placements')
    if c.fetchone()[0] == 0:
        placements = [
            ('2024-11', 24, 12.5, 89.5, 'Hyderabad', 'PGA-43'),
            ('2024-12', 20, 11.8, 92.3, 'Mumbai', 'PGA-38'),
            ('2025-01', 23, 10.2, 85.7, 'Bangalore', 'CIBOP-118'),
            ('2025-02', 19, 11.8, 91.0, 'Hyderabad', 'PGA-39'),
            ('2024-10', 25, 13.0, 87.6, 'Mumbai', 'PGA-44'),
            ('2025-03', 21, 12.2, 89.8, 'Bangalore', 'CIBOP-121'),
            ('2024-09', 26, 10.5, 84.3, 'Hyderabad', 'PGA-42')
        ]
        c.executemany('''
            INSERT INTO placements (month_year, placement_count, avg_ctc, success_rate, location, batch)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', placements)

    c.execute('SELECT COUNT(*) FROM companies')
    if c.fetchone()[0] == 0:
        companies = [
            ('Axion Ray', 'Developer', '4-8 LPA', 'Monthly', 'Java, Python'),
            ('Amazon', 'SDE-1', '15-25 LPA', 'Quarterly', 'DSA, Python'),
            ('Latent View', 'Data Analyst', '5-9 LPA', 'Monthly', 'SQL, Statistics'),
            ('Axion Ray', 'Data Science', '4-8 LPA', 'Monthly', 'ML, Python'),
            ('Axion Ray', 'Data Analyst', '5-9 LPA', 'Monthly', 'SQL, Tableau, Python'),
            ('Sagility Health', 'Data Analyst', '6-12 LPA', 'Quarterly', 'ML, Spring Boot'),
            ('Amazon', 'Data Scientist', '18-30 LPA', 'Quarterly', 'Python, NLP, ML'),
            ('Tech Mahindra', 'System Engineer', '4-7 LPA', 'Monthly', 'Linux, Networking, Scripting'),
            ('Axion Ray', 'Cloud Engineer', '8-14 LPA', 'Bi-monthly', 'AWS, Docker, CI/CD')
        ]
        c.executemany('INSERT INTO companies (company_name, role, ctc_range, hiring_frequency, requirements) VALUES (?, ?, ?, ?, ?)', companies)

    c.execute('SELECT COUNT(*) FROM dscc_activities')
    if c.fetchone()[0] == 0:
        activities = [
            ('Blogathon', 'Blog Presentation challenge', 'Monthly', 'Sivashini', '2024-01-10', 220),
            ('Hackathon Level-1', '48hr coding marathon', 'Bi Weekly', 'Team Alpha', '2024-01-20', 154),
            ('Data Science Project Competition', 'Data science project challenge', 'Quarterly', 'Shyam', '2025-02-12', 121),
            ('Hackathon Level-2', 'A 48 Hr coding competition', 'Bi Weekly', 'Sravanthi', '2025-04-11', 142),
            ('Internship', 'A Code competition between participants, whoever wins gets the internship', 'Half-Yearly', 'Alan, Vignes, Raj', '2025-01-20', 231)
        ]
        c.executemany('INSERT INTO dscc_activities (activity_name, description, cadence, winners, last_conducted, participation_count) VALUES (?, ?, ?, ?, ?, ?)', activities)

    c.execute('SELECT COUNT(*) FROM projects')
    if c.fetchone()[0] == 0:
        projects = [
            ('Crypto price prediction', 'Machine Learning', 'Data Analytics', 'Intermediate'),
            ('Sentiment Analysis on Twitter Data', 'NLP', 'Social Media', 'Intermediate'),
            ('EDA using Tablue and Power BI', 'Tablue and Power BI', 'Visualization', 'Beginner'),
            ('Resume Parser using NLP', 'NLP', 'Data Science', 'Advanced'),
            ('Financial Fraud Detection', 'Machine Learning', 'Data Science', 'Advanced'),
            ('GenAi project', 'LLM', 'Data Science', 'Advanced')
        ]
        c.executemany('INSERT INTO projects (project_title, topic, domain, difficulty_level) VALUES (?, ?, ?, ?)', projects)

    conn.commit()
    return conn

# --- Query & Format Functions ---
def extract_filters(query):
    query = query.lower()
    skill_pattern = r"(skilled|skilled in|expertise in|know|with)\s+([\w\s,]+)"
    location_pattern = r"(in|from)\s+([\w\s]+)"
    profile_pattern = r"(profile|position|role|as a)\s+([\w\s]+)"
    experience_pattern = r"(experience|years of experience)\s+(\d+)"
    year_pattern = r"\b(202[0-5])\b"
    month_pattern = r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b"
    frequency_pattern = r"\b(monthly|bimonthly|bi weekly|quarterly|half-yearly)\b"
    domain_pattern = r"\b(data science|machine learning|nlp|visualization|social media|data analytics)\b"
    ctc_pattern = r"\b(highest ctc|highest package)\b"

    skill = re.search(skill_pattern, query, re.IGNORECASE)
    location = re.search(location_pattern, query, re.IGNORECASE)
    profile = re.search(profile_pattern, query, re.IGNORECASE)
    experience = re.search(experience_pattern, query, re.IGNORECASE)
    year = re.search(year_pattern, query, re.IGNORECASE)
    month = re.search(month_pattern, query, re.IGNORECASE)
    frequency = re.search(frequency_pattern, query, re.IGNORECASE)
    domain = re.search(domain_pattern, query, re.IGNORECASE)
    ctc = re.search(ctc_pattern, query, re.IGNORECASE)

    return {
        'skill': skill.group(2).strip() if skill else None,
        'location': location.group(2).strip() if location else None,
        'profile': profile.group(2).strip() if profile else None,
        'experience': int(experience.group(2)) if experience else None,
        'year': year.group(1) if year else None,
        'month': month.group(1) if month else None,
        'frequency': frequency.group(1) if frequency else None,
        'domain': domain.group(1) if domain else None,
        'highest_ctc': bool(ctc)
    }

def query_trainers(conn, filters):
    c = conn.cursor()
    query = "SELECT name, profile, description, skillset, experience, location FROM trainers WHERE 1=1"
    params = []
    if filters['skill']:
        query += " AND skillset LIKE ?"
        params.append(f"%{filters['skill']}%")
    if filters['location']:
        query += " AND location LIKE ?"
        params.append(f"%{filters['location']}%")
    if filters['profile']:
        query += " AND profile LIKE ?"
        params.append(f"%{filters['profile']}%")
    if filters['experience']:
        query += " AND experience >= ?"
        params.append(filters['experience'])
    c.execute(query, params)
    return c.fetchall()

def query_placements(conn, filters):
    c = conn.cursor()
    query = "SELECT month_year, placement_count, avg_ctc, success_rate, location, batch FROM placements WHERE 1=1"
    params = []
    if filters['year']:
        query += " AND month_year LIKE ?"
        params.append(f"%{filters['year']}%")
    if filters['month']:
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        if filters['month'].lower() in month_map:
            query += " AND month_year LIKE ?"
            params.append(f"%{month_map[filters['month'].lower()]}%")
    c.execute(query, params)
    return c.fetchall()

def query_companies(conn, filters):
    c = conn.cursor()
    query = "SELECT company_name, role, ctc_range, hiring_frequency, requirements FROM companies WHERE 1=1"
    params = []
    if filters['frequency']:
        frequency_map = {'bimonthly': 'Bi-monthly', 'bi weekly': 'Bi Weekly'}
        freq = frequency_map.get(filters['frequency'].lower(), filters['frequency'].title())
        query += " AND hiring_frequency = ?"
        params.append(freq)
    if filters['highest_ctc']:
        query = "SELECT company_name, role, ctc_range, hiring_frequency, requirements FROM companies ORDER BY CAST(SUBSTR(ctc_range, INSTR(ctc_range, '-') + 1, INSTR(ctc_range, ' LPA') - INSTR(ctc_range, '-') - 1) AS INTEGER) DESC"
    c.execute(query, params)
    return c.fetchall()

def query_activities(conn, filters):
    c = conn.cursor()
    query = "SELECT activity_name, description, cadence, winners, last_conducted, participation_count FROM dscc_activities WHERE 1=1"
    params = []
    if filters['frequency']:
        frequency_map = {'bimonthly': 'Bi Weekly', 'bi weekly': 'Bi Weekly', 'monthly': 'Monthly', 'quarterly': 'Quarterly', 'half-yearly': 'Half-Yearly'}
        freq = frequency_map.get(filters['frequency'].lower(), filters['frequency'].title())
        query += " AND cadence = ?"
        params.append(freq)
    c.execute(query, params)
    return c.fetchall()

def query_projects(conn, filters):
    c = conn.cursor()
    query = "SELECT project_title, topic, domain, difficulty_level FROM projects WHERE 1=1"
    params = []
    if filters['domain']:
        query += " AND domain LIKE ?"
        params.append(f"%{filters['domain']}%")
    c.execute(query, params)
    return c.fetchall()

def get_top_experienced_trainers(conn, limit=5):
    query = """
        SELECT name, profile, description, skillset, experience, location 
        FROM trainers 
        ORDER BY experience DESC 
        LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()

def format_trainers_with_ollama(data, original_question):
    if not data:
        return "No trainer data found for your query."
    
    trainer_info = []
    for name, profile, description, skillset, experience, location in data:
        trainer_info.append(f"Name: {name}, Profile: {profile}, Description: {description}, Skills: {skillset}, Experience: {experience} years, Location: {location}")
    
    prompt_data = "\n".join(trainer_info)
    
    prompt = f"""You are a professional trainer profile formatter. Format the trainer data below into clean, professional markdown.

IMPORTANT RULES:
- Create ONE profile section per trainer only
- Do NOT repeat or duplicate any trainer information
- Each trainer gets exactly ONE formatted section
- Start each trainer with "## 👨‍🏫 [Trainer Name]" as header
- Use this exact table format for each trainer
- Keep the response clean and professional

Required format for each trainer:
## 👨‍🏫 [Name from data]

| Field | Details |
|-------|---------|
| **Role** | [Role from data] |
| **Location** | [Location from data] |
| **Experience** | [Experience from data] |
| **Skill Set** | [Skills from data] |
| **Strengths** | [Strengths from data] |
| **LinkedIn Profile** | [Connect Here]([LinkedIn URL]) |

---

USER QUERY: {query}
TRAINER DATA TO FORMAT:
{trainer_info}
"""

    try:
        response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Error from Ollama: {e}"

def format_placements_with_ollama(data, original_question):
    if not data:
        return "No placement data found for your query."
    
    placement_info = []
    for month_year, placement_count, avg_ctc, success_rate, location, batch in data:
        placement_info.append(f"Month: {month_year}, Placements: {placement_count}, Avg CTC: {avg_ctc} LPA, Success Rate: {success_rate}%, Location: {location}, Batch: {batch}")
    
    prompt_data = "\n".join(placement_info)
    
    prompt = f"""
The user asked: '{original_question}'

Based on the following placement data, create a response with this EXACT format:

🎯 Top CTC recorded: [Highest CTC] LPA

Name           | Education Background | Company      | Role                    | CTC      | Location
---------------|---------------------|--------------|-------------------------|----------|----------
[Student Name] | [Degree]            | [Company]    | [Job Role]             | ₹[X] LPA | [City]
[Student Name] | [Degree]            | [Company]    | [Job Role]             | ₹[X] LPA | [City]

Know their stories below

[Add a brief story for top performer]

Here's the placement data:
{prompt_data}

IMPORTANT:
- Use the exact table format with | separators
- Start with 🎯 emoji and highest CTC
- Create realistic student profiles based on the data provided
- Use ₹ symbol for CTC amounts
- Include "Know their stories below" section
- Generate realistic names and education backgrounds
"""

    try:
        response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Error from Ollama: {e}"

def format_companies_with_ollama(data, original_question):
    if not data:
        return "No company data found for your query."
    
    company_info = []
    for company_name, role, ctc_range, hiring_frequency, requirements in data:
        company_info.append(f"Company: {company_name}, Role: {role}, CTC: {ctc_range}, Frequency: {hiring_frequency}, Requirements: {requirements}")
    
    prompt_data = "\n".join(company_info)
    
    prompt = f"""
The user asked: '{original_question}'

Based on the following company data, create a response with this EXACT format:

🏢 Companies Hiring Our Graduates

Company Name   | Roles Available        | CTC Range    | Hiring Frequency | Key Requirements
---------------|------------------------|--------------|------------------|------------------
[Company]      | [Role]                | [X-Y LPA]    | [Monthly/Quarterly] | [Skills needed]
[Company]      | [Role]                | [X-Y LPA]    | [Monthly/Quarterly] | [Skills needed]

Here's the company data:
{prompt_data}

IMPORTANT:
- Use the exact table format with | separators
- Start with 🏢 emoji and "Companies Hiring Our Graduates"
- Keep the CTC format as shown
- Use the exact column headers provided
- List all companies from the data
"""

    try:
        response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Error from Ollama: {e}"

def format_activities_with_ollama(data, original_question):
    if not data:
        return "No DSCC activities data found for your query."
    
    activity_info = []
    for activity_name, description, cadence, winners, last_conducted, participation_count in data:
        activity_info.append(f"Activity: {activity_name}, Description: {description}, Cadence: {cadence}, Winners: {winners}, Last Conducted: {last_conducted}, Participants: {participation_count}")
    
    prompt_data = "\n".join(activity_info)
    
    prompt = f"""
The user asked: '{original_question}'

Based on the following DSCC activities data, create a response with this format:

🧠 DSCC Activities: Transforming Learners into Industry-Ready Professionals

Here's a summary of all key DSCC activities:

🔹 **Blogathon**
- **Description:** Blog Presentation challenge
- **Timeline:** Monthly
- **Last Conducted:** 2024-01-10
- **Participants:** 220
- **Recent Winners:** Sivashini

🔹 **Hackathon Level-1**
- **Description:** 48hr coding marathon
- **Timeline:** Bi Weekly
- **Last Conducted:** 2024-01-20
- **Participants:** 154
- **Recent Winners:** Team Alpha

Create similar sections for each activity using the data provided.

Here's the DSCC activities data:
{prompt_data}

IMPORTANT:
- Use 🔹 for each activity
- Use bullet points with **bold** labels
- Keep it clean and readable
- Don't use complex tables
"""

    try:
        response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Error from Ollama: {e}"

def format_projects_with_ollama(data, original_question):
    if not data:
        return "No project data found for your query."
    
    project_info = []
    for project_title, topic, domain, difficulty_level in data:
        project_info.append(f"Project: {project_title}, Topic: {topic}, Domain: {domain}, Level: {difficulty_level}")
    
    prompt_data = "\n".join(project_info)
    
    prompt = f"""
The user asked: '{original_question}'

Based on the following project data, create a response with this EXACT format:

🚀 Projects During the 6-Month Course

During the 6-month course, you'll work on [X] industry-focused projects that cover the most in-demand skills across Data Science, NLP, Machine Learning, Visualization, and GenAI.

Here's a snapshot of the projects you'll build:

Project Topic                                    | Domain          | Technologies Used              | Skills Developed
------------------------------------------------|-----------------|--------------------------------|------------------
[Project Title]                                 | [Domain]        | [Tech Stack]                  | [Skills Gained]
[Project Title]                                 | [Domain]        | [Tech Stack]                  | [Skills Gained]

Here's the project data:
{prompt_data}

IMPORTANT:
- Use 🚀 emoji in header
- Include the introductory paragraph mentioning industry-focused projects
- Use the exact table format with | separators
- Generate realistic technology stacks based on the project topics
- Create appropriate skills developed for each project
- Keep the professional tone
"""

    try:
        response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Error from Ollama: {e}"

def format_with_specialized_prompts(data, original_question, function):
    if function == "Trainer Details":
        return format_trainers_with_ollama(data, original_question)
    elif function == "Placement Stats":
        return format_placements_with_ollama(data, original_question)
    elif function == "Company Info":
        return format_companies_with_ollama(data, original_question)
    elif function == "DSCC Activities":
        return format_activities_with_ollama(data, original_question)
    elif function == "Project Showcase":
        return format_projects_with_ollama(data, original_question)
    else:
        return "Unknown function type"

def detect_table_intent(query: str) -> str:
    query = query.lower()
    if any(word in query for word in ["trainer", "trainers", "skills", "coach"]):
        return "Trainer Details"
    elif any(word in query for word in ["placement", "placed", "ctc", "package"]):
        return "Placement Stats"
    elif any(word in query for word in ["company", "companies", "hiring"]):
        return "Company Info"
    elif any(word in query for word in ["dscc", "activity", "activities", "competition"]):
        return "DSCC Activities"
    elif any(word in query for word in ["project", "showcase", "demo"]):
        return "Project Showcase"
    else:
        return "Unknown"

def handle_user_query(query, conn):
    filters = extract_filters(query)
    function = detect_table_intent(query)
    
    if function == "Trainer Details":
        if "highest experience" in query.lower():
            data = get_top_experienced_trainers(conn)
            return format_with_specialized_prompts(data, query, function)
        data = query_trainers(conn, filters)
        return format_with_specialized_prompts(data, query, function)
    
    elif function == "Placement Stats":
        data = query_placements(conn, filters)
        return format_with_specialized_prompts(data, query, function)
    
    elif function == "Company Info":
        data = query_companies(conn, filters)
        return format_with_specialized_prompts(data, query, function)
    
    elif function == "DSCC Activities":
        data = query_activities(conn, filters)
        return format_with_specialized_prompts(data, query, function)
    
    elif function == "Project Showcase":
        data = query_projects(conn, filters)
        return format_with_specialized_prompts(data, query, function)
    
    else:
        return "Sorry, I didn't understand the query."

# --- Main UI ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Add a button to clear chat history
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.success("Chat history cleared!")

tab1, tab2 = st.tabs(["Main", "Chat History"])

with tab1:
    st.markdown("## PitchMate")
    query = st.text_input("How can I help you?", key="user_input")

    if st.button("Ask"):
        conn = init_db()
        function = detect_table_intent(query)
        filters = extract_filters(query)

        # Fetch data based on intent
        if function == "Trainer Details":
            data = query_trainers(conn, filters)
            columns = ["Name", "Profile", "Description", "Skillset", "Experience", "Location"]
        elif function == "Placement Stats":
            data = query_placements(conn, filters)
            columns = ["Month-Year", "Placement Count", "Avg CTC", "Success Rate", "Location", "Batch"]
        elif function == "Company Info":
            data = query_companies(conn, filters)
            columns = ["Company Name", "Role", "CTC Range", "Hiring Frequency", "Requirements"]
        elif function == "DSCC Activities":
            data = query_activities(conn, filters)
            columns = ["Activity Name", "Description", "Cadence", "Winners", "Last Conducted", "Participants"]
        elif function == "Project Showcase":
            data = query_projects(conn, filters)
            columns = ["Project Title", "Topic", "Domain", "Difficulty Level"]
        else:
            data = []
            columns = []

        # Display table if data exists
        if data:
            df = pd.DataFrame(data, columns=columns)
            with st.expander("🔍 View All Matches"):
                st.dataframe(df, use_container_width=True)

        # Generate and show response
        st.markdown(f"🔍 Detected Intent: **{function}**")
        response = handle_user_query(query, conn)
        st.markdown("### Response")
        st.write(response)

        # Save to session history
        st.session_state.chat_history.append({"query": query, "response": response})

with tab2:
    st.markdown("### Chat History")
    if st.session_state.chat_history:
        for i, entry in enumerate(reversed(st.session_state.chat_history), 1):
            try:
                query = entry.get('query', 'Unknown Query')
                response = entry.get('response', 'No Response Available')
                with st.expander(f"Q{i}: {query}"):
                    st.markdown(f"**Answer:** {response}")
            except (KeyError, AttributeError):
                st.warning(f"Chat entry {i} is malformed and cannot be displayed.")
    else:
        st.info("No chat history yet. Ask something in the 'Main' tab.")