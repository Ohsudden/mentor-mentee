import sqlite3
from datetime import datetime
from pwdlib import PasswordHash

class Database:
    def __init__(self, db_name='mentor_mentee.db'):
        self.db_name = db_name
    
    def connect(self):
        """Establish database connection"""
        return sqlite3.connect(self.db_name)
    
    def create_tables(self):
        """Create all database tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS User (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                    name VARCHAR NOT NULL,
                    email VARCHAR UNIQUE NOT NULL,
                    role TEXT CHECK(role IN ('mentor', 'mentee', 'curator', 'administrator')) NOT NULL,
                    gender TEXT CHECK(gender IN ('male', 'female', 'non-binary')),
                    password_hash VARCHAR NOT NULL,
                    age INTEGER,
                    education_level TEXT CHECK(education_level IN ('high school', 'undergrad', 'postgrad', 'phd', 'postdoc')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Mentor_profile (
                    mentor_id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    field_of_expertise VARCHAR,
                    experience VARCHAR,
                    max_groups INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Mentee_profile (
                    mentee_id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    skills VARCHAR,
                    domain_of_study VARCHAR,
                    favourable_program_type VARCHAR,
                    experience_level VARCHAR,
                    research_goals VARCHAR,
                    short_term_goals VARCHAR,
                    long_term_goals VARCHAR,
                    mentor_expectations VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Questionnaire (
                    questionnaire_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mentee_id INTEGER NOT NULL,
                    papers_read_plan VARCHAR,
                    lit_review_confidence INTEGER,
                    meeting_frequency VARCHAR,
                    communication_abilities VARCHAR,
                    research_tool_skill VARCHAR,
                    deadline_management VARCHAR,
                    domain_knowledge VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mentee_id) REFERENCES Mentee_profile(mentee_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Availability (
                    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    day_of_the_week TEXT NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Matching (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mentor_id INTEGER NOT NULL,
                    name VARCHAR,
                    description VARCHAR,
                    program_type TEXT,
                    max_size INTEGER,
                    experience_level VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mentor_id) REFERENCES Mentor_profile(mentor_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Matching_mentee (
                    mentee_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    owned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (mentee_id, group_id),
                    FOREIGN KEY (mentee_id) REFERENCES Mentee_profile(mentee_id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES Matching(group_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Matching_algorithm_score (
                    matching_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    dnf_similarity_00 REAL,
                    size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES Matching(group_id) ON DELETE CASCADE
                )
            ''')
            
            # Create Feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    mentor_id INTEGER NOT NULL,
                    mentee_id INTEGER NOT NULL,
                    compatibility REAL,
                    responsiveness REAL,
                    relationship_quality REAL,
                    rating_overall REAL,
                    comments VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES Matching(group_id) ON DELETE CASCADE,
                    FOREIGN KEY (mentor_id) REFERENCES Mentor_profile(mentor_id) ON DELETE CASCADE,
                    FOREIGN KEY (mentee_id) REFERENCES Mentee_profile(mentee_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            print("Database tables created successfully!")
            
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize the database"""
        self.create_tables()

    def get_user_by_id(self, user_id):
        """Fetch user by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            return user
        except sqlite3.Error as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()

    def login_user(self, email, password):
        """Authenticate user by email and password"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, email, password_hash FROM User WHERE email = ?", (email,))
            user = cursor.fetchone()
            if not user:
                return False, "Invalid email or password"
            if not PasswordHash.recommended().verify(password, user[2]):
                return False, "Incorrect password."
            return True, {"id": user[0], "email": user[1]}
        except sqlite3.Error as e:
            print(f"Error during login: {e}")
            return False, "Database error"
        finally:
            conn.close()
            cursor.close()
    def create_user(self, name, email, password, confirm_password, role, gender=None, age=None, education_level=None):
        """Create a new user"""
        if password != confirm_password:
            return False, "Passwords do not match"
        
        password_hash = PasswordHash.recommended().hash(password)
        
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO User (name, email, password_hash, role, gender, age, education_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password_hash, role, gender, age, education_level))
            conn.commit()
            return True, "User created successfully"
        except sqlite3.Error as e:
            print(f"Error creating user: {e}")
            conn.rollback()
            return False, "Error creating user"
        finally:
            conn.close()