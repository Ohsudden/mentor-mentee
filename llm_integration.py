from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
import json
    
import math

import sqlite_vec

from database import Database

class LLMIntegration:
    def __init__(self, openai_api_key=None):
        self.client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))

    def generate_embedding(self, text: str):
        """
        Generate embedding using OpenAI text-embedding-3-small
        Returns: list[float] size 1536
        """
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return sqlite_vec.serialize_float32(response.data[0].embedding)

    def generate_embeddings_from_db(self, db: "Database"):
        """
        Generate embeddings for mentees and store them in SQLite vec tables.
        """

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                mentee_id,
                skills,
                domain_of_study,
                research_goals,
                short_term_goals,
                long_term_goals,
                mentor_expectations
            FROM Mentee_profile
        """)

        mentees = cursor.fetchall()

        for row in mentees:
            mentee_id = row[0]
            combined_text = f"""
            Short Term Goals: {row[4]}
            Long Term Goals: {row[5]}
            Mentor Expectations: {row[6]}
            """

            domain_text = f"""
            Skills: {row[1]}
            Domain of Study: {row[2]}
            Research Goals: {row[3]}
            """ 


            combined_emb = self.generate_embedding(combined_text)
            domain_emb = self.generate_embedding(domain_text)

            cursor.execute("""
                DELETE FROM Mentee_embeddings WHERE mentee_id = ?
            """, (mentee_id,))

            cursor.execute("""
                INSERT INTO Mentee_embeddings
                (mentee_id, combined_profile_emb, domain_of_study_emb)
                VALUES (?, ?, ?)
            """, (mentee_id, combined_emb, domain_emb))

        conn.commit()
        conn.close()

        return True, "Embeddings generated successfully"
    
    def generate_matching_embeddings(self, db: Database):
        """
        Generate embeddings for all matching descriptions and
        store them in Matching_embeddings.
        """

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                group_id,
                description
            FROM Matching
        """)

        groups = cursor.fetchall()

        for group in groups:

            embedding = self.generate_embedding(group["description"])

            cursor.execute("""
                DELETE FROM Matching_embeddings WHERE group_id = ?
            """, (group["group_id"],))
  
            cursor.execute("""INSERT INTO Matching_embeddings
                (group_id, description_emb)
                VALUES (?, ?)
            """, (group["group_id"], embedding))

        conn.commit()
        conn.close()

        return True, "Matching embeddings generated successfully"    
    def get_working_experience(
        self,
        text,
        model="gemini-2.5-flash",
        temperature=0.5,
        max_tokens=100,
    ):
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set."
            )

        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=None,
            max_retries=2,
        )

        response = llm.invoke(text)

        result = json.loads(response.content)

        return result["level"]
    
    def provide_recommendations(self, n_matches, db, group_id):
        # 1. Sort by the availability mentors and mentees. (Make the datetime to the same GMT timezone and check if the availability is within 1 hour of each other.)
        # 2. Sort by the level of experience.
        # 3. Make embeddings for matching description.
        # 4. Make embeddings out of domain of study + skills + research goals.
        # 5. Make additional embeddings out of long term goals, short term goals, and mentor expectations.
        # 6. Use cosine similarity to find the between the matching and mentees by the description and domain. Look for the first n_matches*4
        # 7. Maximize the maximum distance in the group based on the questionnaire.
        # 8. Take the top n_matches*2.
        # 9. Use cosine similarity to find the between mentees by the long term goals, short term goals, research goals, and mentor expectations. 
        # Look for the first n_matches.
        
        # Step 1-2
        candidates = self.filter_candidates(db, group_id)

        if not candidates:
            return []

        # Step 3-6
        candidates = self.retrieve_embedding_candidates(
            db,
            group_id,
            candidates,
            limit=n_matches * 4
        )

        # Step 7
        diversified = self.diversify_candidates(
            db,
            candidates,
            limit=n_matches * 2
        )

        # Step 8-9
        final = self.rank_by_profile_similarity(
            db,
            diversified,
            limit=n_matches
        )

        return final


    def questionnaire_distance(self, a, b):
        keys = [
            "lit_review_confidence",
            "communication_abilities",
            "research_tool_skill",
            "deadline_management",
            "domain_knowledge"
        ]

        total = 0

        for k in keys:
            total += (a[k] - b[k]) ** 2

        return math.sqrt(total)

    def _availability_overlap(self, mentor_slots, mentee_slots):
        """
        Returns True if the mentor and mentee have at least one
        overlapping availability slot of >= 1 hour.

        mentor_slots and mentee_slots are lists of sqlite rows containing:
            day_of_the_week
            start_time
            end_time
            timezone
        """

        for mentor in mentor_slots:
            for mentee in mentee_slots:

                if mentor["day_of_the_week"] != mentee["day_of_the_week"]:
                    continue

                mentor_tz = ZoneInfo(mentor["timezone"])
                mentee_tz = ZoneInfo(mentee["timezone"])

                mentor_start = datetime.strptime(
                    mentor["start_time"], "%H:%M:%S"
                ).replace(
                    year=2000,
                    month=1,
                    day=3,
                    tzinfo=mentor_tz
                ).astimezone(ZoneInfo("UTC"))

                mentor_end = datetime.strptime(
                    mentor["end_time"], "%H:%M:%S"
                ).replace(
                    year=2000,
                    month=1,
                    day=3,
                    tzinfo=mentor_tz
                ).astimezone(ZoneInfo("UTC"))

                mentee_start = datetime.strptime(
                    mentee["start_time"], "%H:%M:%S"
                ).replace(
                    year=2000,
                    month=1,
                    day=3,
                    tzinfo=mentee_tz
                ).astimezone(ZoneInfo("UTC"))

                mentee_end = datetime.strptime(
                    mentee["end_time"], "%H:%M:%S"
                ).replace(
                    year=2000,
                    month=1,
                    day=3,
                    tzinfo=mentee_tz
                ).astimezone(ZoneInfo("UTC"))

                overlap = (
                    min(mentor_end, mentee_end)
                    - max(mentor_start, mentee_start)
                ).total_seconds()

                if overlap >= 3600:
                    return True

        return False

    def filter_candidates(self, db: Database, group_id: int):
        """
        Filter mentees by

        1. Experience level
        2. Availability overlap (>= 1 hour)
        """

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT mentor_id, experience_level
            FROM Matching
            WHERE group_id = ?
        """, (group_id,))

        group = cursor.fetchone()

        if group is None:
            conn.close()
            return []

        mentor_id = group["mentor_id"]
        required_level = group["experience_level"]

        cursor.execute("""
            SELECT user_id
            FROM Mentor_profile
            WHERE mentor_id = ?
        """, (mentor_id,))

        mentor = cursor.fetchone()

        if mentor is None:
            conn.close()
            return []

        mentor_user_id = mentor["user_id"]

        cursor.execute("""
            SELECT *
            FROM Availability
            WHERE user_id = ?
        """, (mentor_user_id,))

        mentor_slots = cursor.fetchall()

        cursor.execute("""
            SELECT
                mentee_id,
                user_id,
                experience_level
            FROM Mentee_profile
        """)

        mentees = cursor.fetchall()

        filtered = []

        for mentee in mentees:

            if mentee["experience_level"] != required_level:
                continue

            cursor.execute("""
                SELECT *
                FROM Availability
                WHERE user_id = ?
            """, (mentee["user_id"],))

            mentee_slots = cursor.fetchall()

            if self._availability_overlap(mentor_slots, mentee_slots):
                filtered.append(mentee["mentee_id"])

        conn.close()

        return filtered    
    

    
    def retrieve_embedding_candidates(
        self,
        db,
        group_id,
        candidate_ids,
        limit
    ):
        """
        Uses description embedding + domain embedding.
        Automatically generates missing embeddings.
        """

        if not candidate_ids:
            return []

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT description_emb
            FROM Matching_embeddings
            WHERE group_id = ?
        """, (group_id,))

        row = cursor.fetchone()

        if row is None:
            conn.close()

            self.generate_matching_embeddings(db)

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT description_emb
                FROM Matching_embeddings
                WHERE group_id = ?
            """, (group_id,))

            row = cursor.fetchone()

        group_embedding = row["description_emb"]

        placeholders = ",".join("?" * len(candidate_ids))

        cursor.execute(f"""
            SELECT mentee_id
            FROM Mentee_embeddings
            WHERE mentee_id IN ({placeholders})
        """, candidate_ids)

        embedded_ids = {r["mentee_id"] for r in cursor.fetchall()}

        missing_ids = [
            mentee_id
            for mentee_id in candidate_ids
            if mentee_id not in embedded_ids
        ]

        if missing_ids:
            conn.close()

            self.generate_embeddings_from_db(db)

            conn = db.connect()
            cursor = conn.cursor()

        query = f"""
            SELECT
                mentee_id,
                vec_distance_cosine(domain_of_study_emb, ?) AS distance
            FROM Mentee_embeddings
            WHERE mentee_id IN ({placeholders})
            ORDER BY distance
            LIMIT ?
        """

        cursor.execute(
            query,
            (group_embedding, *candidate_ids, limit)
        )

        rows = cursor.fetchall()

        conn.close()

        return [row["mentee_id"] for row in rows]   




    def diversify_candidates(
        self,
        db,
        candidates,
        limit
    ):
        """
        Greedy max-min selection.
        """

        if len(candidates) <= limit:
            return candidates

        conn = db.connect()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(candidates))

        cursor.execute(f"""
            SELECT *
            FROM Questionnaire
            WHERE mentee_id IN ({placeholders})
        """, candidates)

        questionnaires = {
            row["mentee_id"]: row
            for row in cursor.fetchall()
        }

        conn.close()

        selected = [candidates[0]]

        while len(selected) < limit:

            best = None
            best_score = -1

            for candidate in candidates:

                if candidate in selected:
                    continue

                score = max(
                    self.questionnaire_distance(
                        questionnaires[candidate],
                        questionnaires[s]
                    )
                    for s in selected
                )

                if score > best_score:
                    best = candidate
                    best_score = score

            selected.append(best)

        return selected

    def rank_by_profile_similarity(
        self,
        db,
        candidate_ids,
        limit
    ):
        conn = db.connect()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(candidate_ids))

        cursor.execute(f"""
            SELECT
                mentee_id
            FROM Mentee_embeddings
            WHERE mentee_id IN ({placeholders})
            ORDER BY combined_profile_emb
            LIMIT ?
        """, (*candidate_ids, limit))

        rows = cursor.fetchall()

        conn.close()

        return [r["mentee_id"] for r in rows]