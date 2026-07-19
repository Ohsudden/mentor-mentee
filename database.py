import sqlite3
from datetime import datetime
from pwdlib import PasswordHash
import sqlite_vec

class Database:
    def __init__(self, db_name='mentor_mentee.db'):
        self.db_name = db_name
        self.db_path = 'E:\mentor-mentee\mentor_mentee.db'

    def _add_column_if_missing(self, cursor, table_name, column_name, column_definition):
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
    
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.row_factory = sqlite3.Row
        return conn

    
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
                    university VARCHAR,
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
                    experience_level TEXT CHECK(experience_level IN ('beginner', 'intermediate', 'advanced')),
                    experience_text VARCHAR,
                    research_goals VARCHAR,
                    short_term_goals VARCHAR,
                    long_term_goals VARCHAR,
                    mentor_expectations VARCHAR,
                    university VARCHAR,
                    status TEXT NOT NULL DEFAULT 'unmatched' CHECK(status IN ('matched', 'unmatched')),
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
                    timezone VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Matching (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    curator_id INTEGER NOT NULL,
                    mentor_id INTEGER,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    program_type TEXT,
                    max_size INTEGER,
                    experience_level VARCHAR,
                    status TEXT NOT NULL DEFAULT 'To be assigned' CHECK(status IN ('To be assigned', 'in progress', 'finished')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (curator_id)
                    REFERENCES Curator_profile(curator_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (mentor_id)
                    REFERENCES Mentor_profile(mentor_id)
                    ON DELETE SET NULL
        );
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

            self._add_column_if_missing(
                cursor,
                "Mentee_profile",
                "status",
                "status TEXT NOT NULL DEFAULT 'unmatched' CHECK(status IN ('matched', 'unmatched'))"
            )
            self._add_column_if_missing(
                cursor,
                "Matching",
                "status",
                "status TEXT NOT NULL DEFAULT 'To be assigned' CHECK(status IN ('To be assigned', 'in progress', 'finished'))"
            )

            cursor.execute("UPDATE Mentee_profile SET status = 'unmatched' WHERE status IS NULL OR status = ''")
            cursor.execute("UPDATE Matching SET status = 'To be assigned' WHERE status IS NULL OR status = ''")
            
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Curator_profile (
                    curator_id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    department VARCHAR,
                    university VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                );
            ''')
                
            cursor.execute('''
                CREATE VIRTUAL TABLE Matching_embeddings USING vec0(
                    group_id INTEGER PRIMARY KEY,
                    description_emb FLOAT[1536]
                );
            ''')    
            # combined_profile_emb is based on the mentee's skills, short_term_goals, long_term_goals, and mentor_expectations. 
            # domain_of_study_emb is based on the mentee's domain_of_study.
            cursor.execute('''
                CREATE VIRTUAL TABLE Mentee_embeddings USING vec0(
                mentee_id INTEGER PRIMARY KEY,
                combined_profile_emb FLOAT[1536], 
                domain_of_study_emb FLOAT[1536],
            ); 
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
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, name, email, role, gender, age, education_level "
            "FROM User WHERE user_id = ?",
            (user_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "user_id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[3],
            "gender": row[4],
            "age": row[5],
            "education_level": row[6]
    }

    def login_user(self, email, password):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT user_id, name, email, password_hash, role, gender, age, education_level FROM user WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        connection.close()

        if not row:
            return False, "User not found."

        stored_hash = row[3]
        if not PasswordHash.recommended().verify(password, stored_hash):
            return False, "Incorrect password."

        return True, {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[4],
            "gender": row[5],
            "age": row[6],
            "education_level": row[7]
        }
    

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


    def create_user_controlled(self, user_id, name, email, password, confirm_password, role, gender=None, age=None, education_level=None):
        """Create a new user"""
        if password != confirm_password:
            return False, "Passwords do not match"
        
        password_hash = PasswordHash.recommended().hash(password)
        
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO User (user_id, name, email, password_hash, role, gender, age, education_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, email, password_hash, role, gender, age, education_level))
            conn.commit()
            return True, "User created successfully"
        except sqlite3.Error as e:
            print(f"Error creating user: {e}")
            conn.rollback()
            return False, "Error creating user"
        finally:
            conn.close()

    def fill_mentor_profile(self, user_id, field_of_expertise, experience, max_groups, university):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Mentor_profile (user_id, field_of_expertise, experience, max_groups, university)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, field_of_expertise, experience, max_groups, university))
            conn.commit()
            return True, "Mentor profile created successfully"
        except sqlite3.Error as e:
            print(f"Error creating mentor profile: {e}")
            conn.rollback()
            return False, "Error creating mentor profile"
        finally:
            conn.close()

    def fill_mentee_profile(self, user_id, skills, domain_of_study, favourable_program_type, experience_level, experience_text, research_goals, short_term_goals, long_term_goals, mentor_expectations, university):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Mentee_profile (user_id, skills, domain_of_study, favourable_program_type, experience_level, experience_text, research_goals, short_term_goals, long_term_goals, mentor_expectations, university)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, skills, domain_of_study, favourable_program_type, experience_level, experience_text, research_goals, short_term_goals, long_term_goals, mentor_expectations, university))
            conn.commit()
            return True, "Mentee profile created successfully"
        except sqlite3.Error as e:
            print(f"Error creating mentee profile: {e}")
            conn.rollback()
            return False, "Error creating mentee profile"
        finally:
            conn.close()

    def questionnaire_submission(self, mentee_id, papers_read_plan, lit_review_confidence, meeting_frequency, communication_abilities, research_tool_skill, deadline_management, domain_knowledge):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Questionnaire (mentee_id, papers_read_plan, lit_review_confidence, meeting_frequency, communication_abilities, research_tool_skill, deadline_management, domain_knowledge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (mentee_id, papers_read_plan, lit_review_confidence, meeting_frequency, communication_abilities, research_tool_skill, deadline_management, domain_knowledge))
            conn.commit()
            return True, "Questionnaire submitted successfully"
        except sqlite3.Error as e:
            print(f"Error submitting questionnaire: {e}")
            conn.rollback()
            return False, "Error submitting questionnaire"
        finally:
            conn.close()

    def create_marching(self, mentor_id, name, description, program_type, max_size, experience_level):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Matching (mentor_id, name, description, program_type, max_size, experience_level, status)
                VALUES (?, ?, ?, ?, ?, ?, 'To be assigned')
            ''', (mentor_id, name, description, program_type, max_size, experience_level))
            conn.commit()
            return True, "Matching created successfully"
        except sqlite3.Error as e:
            print(f"Error creating matching: {e}")
            conn.rollback()
            return False, "Error creating matching"
        finally:
            conn.close()

    def assign_mentor_to_matching(self, mentee_id, group_id):
        return self.add_mentee_to_group(group_id, mentee_id)

    def change_availability(self, user_id, day_of_the_week, start_time, end_time, timezone):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Availability (user_id, day_of_the_week, start_time, end_time, timezone)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, day_of_the_week, start_time, end_time, timezone))
            conn.commit()
            return True, "Availability updated successfully"
        except sqlite3.Error as e:
            print(f"Error updating availability: {e}")
            conn.rollback()
            return False, "Error updating availability"
        finally:
            conn.close()

    def get_availability(self, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT day_of_the_week, start_time, end_time, timezone
                FROM Availability
                WHERE user_id = ?
            ''', (user_id,))
            rows = cursor.fetchall()
            availability_list = []
            for row in rows:
                availability_list.append({
                    "day_of_the_week": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "timezone": row[3]
                })
            return availability_list
        except sqlite3.Error as e:
            print(f"Error fetching availability: {e}")
            return []
        finally:
            conn.close()

    def remove_availability(self, user_id, day_of_the_week, start_time, end_time, timezone):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM Availability
                WHERE user_id = ? AND day_of_the_week = ? AND start_time = ? AND end_time = ? AND timezone = ?
            ''', (user_id, day_of_the_week, start_time, end_time, timezone))
            conn.commit()
            return True, "Availability removed successfully"
        except sqlite3.Error as e:
            print(f"Error removing availability: {e}")
            conn.rollback()
            return False, "Error removing availability"
        finally:
            conn.close()

    def fill_curator_profile(self, user_id, department, university):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Curator_profile (user_id, department, university)
                VALUES (?, ?, ?)
            ''', (user_id, department, university))
            conn.commit()
            return True, "Curator profile created successfully"
        except sqlite3.Error as e:
            print(f"Error creating curator profile: {e}")
            conn.rollback()
            return False, "Error creating curator profile"
        finally:
            conn.close()

    def assign_mentee_to_matching(self, mentee_id, group_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT status
                FROM Mentee_profile
                WHERE mentee_id = ?
            ''', (mentee_id,))
            mentee = cursor.fetchone()
            if mentee is None:
                return False, "Mentee not found"
            if mentee["status"] == "matched":
                return False, "Mentee is already matched"

            cursor.execute('''
                INSERT INTO Matching_mentee (mentee_id, group_id)
                VALUES (?, ?)
            ''', (mentee_id, group_id))

            cursor.execute('''
                UPDATE Mentee_profile
                SET status = 'matched'
                WHERE mentee_id = ?
            ''', (mentee_id,))

            cursor.execute('''
                UPDATE Matching
                SET status = CASE
                    WHEN (SELECT COUNT(*) FROM Matching_mentee WHERE group_id = ?) >= max_size THEN 'finished'
                    ELSE 'in progress'
                END
                WHERE group_id = ?
            ''', (group_id, group_id))

            conn.commit()
            return True, "Mentee assigned to matching successfully"
        except sqlite3.Error as e:
            print(f"Error assigning mentee to matching: {e}")
            conn.rollback()
            return False, "Error assigning mentee to matching"
        
    def create_group(
            self,
            curator_id,
            mentor_id,
            name,
            description,
            program_type,
            max_size,
            experience_level):

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO Matching
                (curator_id, mentor_id, name, description,
                program_type, max_size, experience_level, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'To be assigned')
            """, (
                curator_id,
                mentor_id,
                name,
                description,
                program_type,
                max_size,
                experience_level
            ))

            conn.commit()
            return True, "Group created successfully"

        except sqlite3.Error as e:
            conn.rollback()
            return False, str(e)

        finally:
            conn.close()

    def get_mentors(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT m.mentor_id, u.name, u.email, m.field_of_expertise, m.experience, m.max_groups, m.university
                FROM Mentor_profile m
                JOIN User u ON m.user_id = u.user_id
            ''')
            rows = cursor.fetchall()
            mentors = []
            for row in rows:
                mentors.append({
                    "mentor_id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "field_of_expertise": row[3],
                    "experience": row[4],
                    "max_groups": row[5],
                    "university": row[6]
                })
            return mentors
        except sqlite3.Error as e:
            print(f"Error fetching mentors: {e}")
            return []
        finally:
            conn.close()

    def get_current_curator(self, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT curator_id FROM Curator_profile WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error fetching curator: {e}")
            return None
        finally:
            conn.close()

    def get_current_groups(self, curator_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT
                    g.group_id,
                    g.name,
                    g.description,
                    g.program_type,
                    g.max_size,
                    g.experience_level,
                    u.name AS mentor_name,
                    COUNT(DISTINCT mm.mentee_id) AS current_size
                FROM Matching g
                LEFT JOIN Mentor_profile mp
                    ON g.mentor_id = mp.mentor_id
                LEFT JOIN User u
                    ON mp.user_id = u.user_id
                LEFT JOIN Matching_mentee mm
                    ON g.group_id = mm.group_id
                WHERE g.curator_id = ?
                GROUP BY
                    g.group_id,
                    g.name,
                    g.description,
                    g.program_type,
                    g.max_size,
                    g.experience_level,
                    u.name
            ''', (curator_id,))
            rows = cursor.fetchall()
            groups = []
            for row in rows:
                groups.append({
                    "group_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "program_type": row[3],
                    "max_size": row[4],
                    "experience_level": row[5],
                    "mentor_name": row[6],
                    "current_size": row[7]
                })
            return groups
        except sqlite3.Error as e:
            print(f"Error fetching groups: {e}")
            return []
        finally:
            conn.close()
        
    def delete_group(self, group_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE Mentee_profile
                SET status = 'unmatched'
                WHERE mentee_id IN (
                    SELECT mentee_id
                    FROM Matching_mentee
                    WHERE group_id = ?
                )
            ''', (group_id,))

            cursor.execute('DELETE FROM Matching WHERE group_id = ?', (group_id,))
            conn.commit()

            if cursor.rowcount == 0:        
                return False, "Group not found"

            return True, "Group deleted successfully"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Error deleting group: {e}"
        finally:
            conn.close()
        
    def change_group(self, group_id, name, description, program_type, max_size, experience_level):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE Matching
                SET name = ?, description = ?, program_type = ?, max_size = ?, experience_level = ?
                WHERE group_id = ?
            ''', (name, description, program_type, max_size, experience_level, group_id))
            conn.commit()
            return True, "Group updated successfully"
        except sqlite3.Error as e:
            print(f"Error updating group: {e}")
            conn.rollback()
            return False, "Error updating group"
        finally:
            conn.close()

    def add_mentee_to_group(self, group_id, mentee_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT status
                FROM Mentee_profile
                WHERE mentee_id = ?
            ''', (mentee_id,))
            mentee = cursor.fetchone()

            if mentee is None:
                return False, "Mentee not found"

            if mentee["status"] == "matched":
                return False, "Mentee is already matched"

            cursor.execute('''
                SELECT status, max_size
                FROM Matching
                WHERE group_id = ?
            ''', (group_id,))
            group = cursor.fetchone()

            if group is None:
                return False, "Group not found"

            if group["status"] == "finished":
                return False, "Group is already finished"

            cursor.execute('''
                SELECT COUNT(*) AS current_size
                FROM Matching_mentee
                WHERE group_id = ?
            ''', (group_id,))
            current_size = cursor.fetchone()["current_size"]

            if current_size >= group["max_size"]:
                cursor.execute('''
                    UPDATE Matching
                    SET status = 'finished'
                    WHERE group_id = ?
                ''', (group_id,))
                conn.commit()
                return False, "Group is already full"

            cursor.execute('''
                INSERT INTO Matching_mentee (group_id, mentee_id)
                VALUES (?, ?)
            ''', (group_id, mentee_id))

            cursor.execute('''
                UPDATE Mentee_profile
                SET status = 'matched'
                WHERE mentee_id = ?
            ''', (mentee_id,))

            next_size = current_size + 1
            group_status = 'finished' if next_size >= group["max_size"] else 'in progress'

            cursor.execute('''
                UPDATE Matching
                SET status = ?
                WHERE group_id = ?
            ''', (group_status, group_id))

            conn.commit()
            return True, "Mentee added to group successfully"
        except sqlite3.Error as e:
            print(f"Error adding mentee to group: {e}")
            conn.rollback()
            return False, "Error adding mentee to group"
        finally:
            conn.close()

    def get_groups(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT group_id, curator_id, mentor_id, name, description, program_type, max_size, experience_level
                FROM Matching
            ''')
            rows = cursor.fetchall()
            groups = []
            for row in rows:
                groups.append({
                    "group_id": row[0],
                    "curator_id": row[1],
                    "mentor_id": row[2],
                    "name": row[3],
                    "description": row[4],
                    "program_type": row[5],
                    "max_size": row[6],
                    "experience_level": row[7]
                })
            return groups
        except sqlite3.Error as e:
            print(f"Error fetching groups: {e}")
            return []
        finally:
            conn.close()

    def get_mentees_in_group(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT m.mentee_id, u.name, u.email, m.skills, m.domain_of_study, m.favourable_program_type,
                       m.experience_level, m.experience_text, m.research_goals, m.short_term_goals,
                       m.long_term_goals, m.mentor_expectations, m.university
                FROM Matching_mentee mm
                JOIN Mentee_profile m ON mm.mentee_id = m.mentee_id
                JOIN User u ON m.user_id = u.user_id
            ''', )
            rows = cursor.fetchall()
            mentees = []
            for row in rows:
                mentees.append({
                    "mentee_id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "skills": row[3],
                    "domain_of_study": row[4],
                    "favourable_program_type": row[5],
                    "experience_level": row[6],
                    "experience_text": row[7],
                    "research_goals": row[8],
                    "short_term_goals": row[9],
                    "long_term_goals": row[10],
                    "mentor_expectations": row[11],
                    "university": row[12]
                })
            return mentees
        except sqlite3.Error as e:
            print(f"Error fetching mentees in group: {e}")
            return []
        finally:
            conn.close()

    def get_matched_groups(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT DISTINCT
                    mt.group_id,
                    g.name,
                    g.description,
                    g.program_type,
                    g.max_size,
                    g.experience_level,
                    u.name AS mentor_name,
                    mp.field_of_expertise,
                    mp.university AS mentor_university
                FROM Matching_mentee mt
                JOIN Matching g
                    ON mt.group_id = g.group_id
                LEFT JOIN Mentor_profile mp
                    ON g.mentor_id = mp.mentor_id
                LEFT JOIN User u
                    ON mp.user_id = u.user_id
            ''')

            rows = cursor.fetchall()
            groups = []
            for row in rows:
                groups.append({
                    "group_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "program_type": row[3],
                    "max_size": row[4],
                    "experience_level": row[5],
                    "mentor_name": row[6],
                    "field_of_expertise": row[7],
                    "mentor_university": row[8]
                })

            return groups

        except sqlite3.Error as e:
            print(f"Error fetching matched groups: {e}")
            return []

        finally:
            conn.close()


    def get_curator_id(self, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT curator_id FROM Curator_profile WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            print(f"Error fetching curator ID: {e}")
            return None
        finally:
            conn.close()

    def get_mentee_id_by_user_id(self, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT mentee_id
                FROM Mentee_profile
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            print(f"Error fetching mentee ID: {e}")
            return None
        finally:
            conn.close()

    def get_previous_matches(self, mentee_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT g.group_id,
                       g.name,
                       g.description,
                       g.program_type,
                       g.max_size,
                       g.experience_level,
                       g.status,
                       u.name AS mentor_name,
                       mp.field_of_expertise,
                       mp.university AS mentor_university,
                       EXISTS(
                           SELECT 1
                           FROM Feedback f
                           WHERE f.group_id = g.group_id AND f.mentee_id = mm.mentee_id
                       ) AS has_feedback
                FROM Matching_mentee mm
                JOIN Matching g ON mm.group_id = g.group_id
                LEFT JOIN Mentor_profile mp ON g.mentor_id = mp.mentor_id
                LEFT JOIN User u ON mp.user_id = u.user_id
                WHERE mm.mentee_id = ?
                ORDER BY g.created_at DESC
            ''', (mentee_id,))

            rows = cursor.fetchall()
            matches = []
            for row in rows:
                matches.append({
                    "group_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "program_type": row[3],
                    "max_size": row[4],
                    "experience_level": row[5],
                    "status": row[6],
                    "mentor_name": row[7],
                    "field_of_expertise": row[8],
                    "mentor_university": row[9],
                    "has_feedback": bool(row[10])
                })
            return matches
        except sqlite3.Error as e:
            print(f"Error fetching previous matches: {e}")
            return []
        finally:
            conn.close()

    def get_student_group_details(self, mentee_id, group_id):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT g.group_id,
                       g.mentor_id,
                       g.name,
                       g.description,
                       g.program_type,
                       g.max_size,
                       g.experience_level,
                       g.status,
                       u.name AS mentor_name,
                       mp.field_of_expertise,
                       mp.university AS mentor_university,
                       EXISTS(
                           SELECT 1
                           FROM Feedback f
                           WHERE f.group_id = g.group_id AND f.mentee_id = mm.mentee_id
                       ) AS has_feedback
                FROM Matching_mentee mm
                JOIN Matching g ON mm.group_id = g.group_id
                LEFT JOIN Mentor_profile mp ON g.mentor_id = mp.mentor_id
                LEFT JOIN User u ON mp.user_id = u.user_id
                WHERE mm.mentee_id = ? AND g.group_id = ?
            ''', (mentee_id, group_id))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "group_id": row[0],
                "mentor_id": row[1],
                "name": row[2],
                "description": row[3],
                "program_type": row[4],
                "max_size": row[5],
                "experience_level": row[6],
                "status": row[7],
                "mentor_name": row[8],
                "field_of_expertise": row[9],
                "mentor_university": row[10],
                "has_feedback": bool(row[11])
            }
        except sqlite3.Error as e:
            print(f"Error fetching student group details: {e}")
            return None
        finally:
            conn.close()

    def submit_feedback(self, group_id, mentor_id, mentee_id, compatibility, responsiveness, relationship_quality, rating_overall, comments):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT 1
                FROM Feedback
                WHERE group_id = ? AND mentee_id = ?
            ''', (group_id, mentee_id))
            if cursor.fetchone():
                return False, "Feedback has already been submitted for this group"

            cursor.execute('''
                INSERT INTO Feedback (
                    group_id,
                    mentor_id,
                    mentee_id,
                    compatibility,
                    responsiveness,
                    relationship_quality,
                    rating_overall,
                    comments
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                group_id,
                mentor_id,
                mentee_id,
                compatibility,
                responsiveness,
                relationship_quality,
                rating_overall,
                comments,
            ))
            conn.commit()
            return True, "Feedback submitted successfully"
        except sqlite3.Error as e:
            print(f"Error submitting feedback: {e}")
            conn.rollback()
            return False, "Error submitting feedback"
        finally:
            conn.close()
    
    def change_matching_status(self, group_id, new_status):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE Matching
                SET status = ?
                WHERE group_id = ?
            ''', (new_status, group_id))
            conn.commit()
            print(f"Matching status for group_id {group_id} changed to {new_status}")
            return True, "Matching status updated successfully"
        except sqlite3.Error as e:
            print(f"Error updating matching status: {e}")
            conn.rollback()
            return False, "Error updating matching status"
        finally:
            conn.close()