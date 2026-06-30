import os
from dotenv import load_dotenv

load_dotenv()

from database import Database
from llm_integration import LLMIntegration

api_key = os.getenv("OPENAI_API_KEY")
print("API KEY:", api_key)

def seed_database():

    db = Database()


    if os.path.exists(db.db_path):
        os.remove(db.db_path)

    db.init_db()

    print("Creating users...")

    users = [
        (10, "Alice Curator", "alice@test.com", "curator"),
        (11, "Dr. Smith", "smith@test.com", "mentor"),
        (12, "Dr. Johnson", "johnson@test.com", "mentor"),
    ]

    for user_id, name, email, role in users:
        db.create_user_controlled(
            user_id,
            name,
            email,
            "password",
            "password",
            role
        )

    for user_id in range(13, 23):

        db.create_user_controlled(
            user_id,
            f"Mentee {user_id-12}",
            f"mentee{user_id-12}@test.com",
            "password",
            "password",
            "mentee"
        )


    print("Creating profiles...")

    db.fill_curator_profile(
        user_id=10,
        department="Computer Science",
        university="Test University"
    )

    db.fill_mentor_profile(
        user_id=11,
        field_of_expertise="Artificial Intelligence",
        experience="8 years of ML research",
        max_groups=5,
        university="Test University"
    )

    db.fill_mentor_profile(
        user_id=12,
        field_of_expertise="Cybersecurity",
        experience="12 years industry experience",
        max_groups=5,
        university="Test University"
    )

    domains = [
        "Machine Learning",
        "Computer Vision",
        "Natural Language Processing",
        "Data Science",
        "Cybersecurity",
    ]

    skills = [
        "Python, TensorFlow",
        "Python, OpenCV",
        "Python, PyTorch",
        "SQL, Pandas",
        "Linux, Networking",
    ]

    research = [
        "Machine learning",
        "Computer vision",
        "LLMs",
        "Data mining",
        "Security",
    ]

    levels = [
        "beginner",
        "intermediate",
        "advanced",
    ]

    for i, user_id in enumerate(range(13, 23)):

        db.fill_mentee_profile(
            user_id=user_id,
            skills=skills[i % 5],
            domain_of_study=domains[i % 5],
            favourable_program_type="Research",
            experience_level=levels[i % 3],
            experience_text="Completed several research projects.",
            research_goals=research[i % 5],
            short_term_goals="Improve research skills",
            long_term_goals="Pursue graduate studies",
            mentor_expectations="Weekly meetings",
            university="Test University"      
        )


    print("Creating availability...")

    db.change_availability(
        11,
        "Monday",
        "09:00:00",
        "12:00:00",
        "UTC"
    )

    db.change_availability(
        12,
        "Tuesday",
        "09:00:00",
        "12:00:00",
        "UTC"
    )

    for user_id in range(13, 23):

        db.change_availability(
            user_id,
            "Monday",
            "10:00:00",
            "13:00:00",
            "UTC"
        )


    conn = db.connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT curator_id
        FROM Curator_profile
        WHERE user_id = ?
    """, (10,))

    curator_id = cursor.fetchone()["curator_id"]

    cursor.execute("""
        SELECT mentor_id
        FROM Mentor_profile
        WHERE user_id = ?
    """, (11,))

    mentor_id = cursor.fetchone()["mentor_id"]

    cursor.execute("""
        SELECT mentee_id
        FROM Mentee_profile
        ORDER BY mentee_id
    """)

    mentee_ids = [row["mentee_id"] for row in cursor.fetchall()]

    conn.close()

    ##########################################################
    # Questionnaire
    ##########################################################

    print("Creating questionnaires...")

    for i, mentee_id in enumerate(mentee_ids):

        db.questionnaire_submission(
            mentee_id=mentee_id,
            papers_read_plan=f"{i+2} papers/week",
            lit_review_confidence=(i % 5) + 1,
            meeting_frequency="Weekly",
            communication_abilities="Good",
            research_tool_skill="Intermediate",
            deadline_management="Good",
            domain_knowledge="Intermediate"
        )

    ##########################################################
    # Matching group
    ##########################################################

    print("Creating group...")

    db.create_group(
        curator_id=curator_id,
        mentor_id=mentor_id,
        name="AI Research Group",
        description="""
Looking for motivated students interested in
Machine Learning,
Deep Learning,
Computer Vision,
Large Language Models,
and academic research.
""",
        program_type="Research",
        max_size=5,
        experience_level="intermediate"
    )

    ##########################################################
    # Embeddings
    ##########################################################

    print("Generating embeddings...")

    llm = LLMIntegration()

    llm.generate_embeddings_from_db(db)
    llm.generate_matching_embeddings(db)

    print()
    print("=====================================")
    print("Database seeded successfully.")
    print("=====================================")


if __name__ == "__main__":
    seed_database()