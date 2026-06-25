
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
import json

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
        return response.data[0].embedding

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
                INSERT OR REPLACE INTO Mentee_embeddings
                (mentee_id, combined_profile_emb, domain_of_study_emb)
                VALUES (?, ?, ?)
            """, (
                mentee_id,
                combined_emb,
                domain_emb
            ))

        conn.commit()
        conn.close()

        return True, "Embeddings generated successfully"
    
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
    
    def provide_recommendations(self, n_matches):
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
        pass