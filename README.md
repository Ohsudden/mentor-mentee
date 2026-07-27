# Mentor-Mentee Matching Platform

An AI-powered web application built with **FastAPI**, **SQLite** (leveraging **`sqlite-vec`** for high-dimensional vector search), **OpenAI Embeddings**, and **Google Gemini**. The platform facilitates intelligent matching between mentees (students) and mentors into structured research/mentorship groups managed by curators.

---

## 🚀 About the Project

The **Mentor-Mentee Matching Platform** connects students and research mentors by evaluating profile compatibility across three core dimensions:
1. **Semantic Vector Similarity**: Uses OpenAI's `text-embedding-3-small` (1536-dimensional embeddings) and `sqlite-vec` to measure alignment between mentee research/career goals and mentorship group descriptions.
2. **AI Experience Evaluation**: Leverages Google Gemini 2.5 Flash (`langchain-google-genai`) to evaluate mentee work experience and assign experience levels (`beginner`, `intermediate`, `advanced`).
3. **Availability & Timezone Alignment**: Calculates schedule overlaps (converted to GMT) to ensure mentors and mentees can commit to regular meeting times.

---

## 👥 User Roles & Features

### 🎓 Mentee (Student)
- **Profile & Questionnaire**: Complete skills, domain of study, research goals (short/long-term), and expectations.
- **AI Experience Profiling**: Automatic evaluation of submitted work experience by Google Gemini.
- **Availability Schedule**: Set weekly time slots and timezone.
- **Matching & Match History**: View matched mentorship groups and past completed groups.
- **Feedback System**: Rate completed group experiences on compatibility, responsiveness, relationship quality, and overall satisfaction.

### 👨‍🏫 Mentor
- **Profile Setup**: Define field of expertise, years of research/industry experience, university affiliation, and max group capacity.
- **Availability Management**: Maintain available mentoring time slots.

### 🏛️ Curator
- **Group Formation**: Create and manage mentorship groups (program type, target experience level, max capacity).
- **Mentor Assignment**: Assign available mentors to created groups.
- **AI Recommendation Engine**: Trigger automated matching to generate top mentee recommendations for each group using vector search and schedule alignment.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.13 / FastAPI, Uvicorn, Starlette (Session Middleware), Jinja2 Templates
- **Database & Storage**: SQLite (`mentor_mentee.db`) with `sqlite-vec` extension
- **Security**: Password hashing using `pwdlib[argon2]`
- **AI / Machine Learning**:
  - `langchain-google-genai` (Gemini 2.5 Flash) for experience assessment
  - `openai` (`text-embedding-3-small`) for generating 1536d profile & group embeddings
  - `sqlite-vec` for fast vector similarity querying
- **Observability**: `arize-phoenix` for LLM tracing and evaluation

---

## 📋 Prerequisites

- **Python 3.10+** (Tested on Python 3.13.5)
- **API Keys**:
  - `OPENAI_API_KEY` (For vector embeddings generation)
  - `GOOGLE_API_KEY` (For Gemini AI experience level evaluation)

Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY="your_google_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
```

---

## ⚙️ Setup & Installation

1. **Activate Virtual Environment** (PowerShell):
   ```powershell
   (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .venv\Scripts\Activate.ps1)
   ```

2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Initialize & Seed Database** (Optional, for demo/testing data):
   ```powershell
   python test_database.py
   ```

---

## 🏃 Running the Application

Start the FastAPI application with Uvicorn:

```powershell
uvicorn main:app --reload
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🧪 Testing & Verification

Run individual feature test scripts to verify database, vector embeddings, and feedback functionality:

- **Database & Seeding Test**:
  ```powershell
  python test_database.py
  ```
- **Embedding Generation & Vector Search Test**:
  ```powershell
  python test_embeddings.py
  ```
- **Feedback API Test**:
  ```powershell
  python test_feedback.py
  ```
- **General Functions Test**:
  ```powershell
  python test_functions.py
  ```

---

## 📁 Project Structure

```
mentor-mentee/
├── database.py           # SQLite connection, schema initialization, and query functions
├── llm_integration.py    # OpenAI embeddings, Gemini AI integration, and matching algorithm
├── main.py               # FastAPI routes, authentication sessions, and API endpoints
├── mentor_mentee.db      # SQLite database file with sqlite-vec extension
├── requirements.txt      # Python dependencies
├── static/               # Frontend HTML templates and static assets
│   ├── index.html
│   ├── login.html
│   ├── registration.html
│   ├── profile.html
│   ├── group_formation.html
│   ├── current_groups.html
│   ├── current_matched_groups.html
│   ├── previous_matches.html
│   └── feedback_base_form.html
├── test_database.py      # Database seeding & user management tests
├── test_embeddings.py    # OpenAI embedding & vector search tests
├── test_feedback.py      # Mentee feedback submission tests
└── test_functions.py     # General platform unit tests
```
