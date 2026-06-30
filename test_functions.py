import os
from dotenv import load_dotenv

load_dotenv()
from database import Database
from llm_integration import LLMIntegration


def main():
    print("====================================")
    print("STARTING LLM INTEGRATION TEST")
    print("====================================\n")

    # 1. Init DB + LLM
    db = Database()
    llm = LLMIntegration()

    print("[1] Checking database connection...")
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM User")
    print("Users in DB:", cursor.fetchone()[0])
    conn.close()

    # 2. Generate embeddings
    print("\n[2] Generating mentee embeddings...")
    ok, msg = llm.generate_embeddings_from_db(db)
    print(msg)

    print("\n[3] Generating matching embeddings...")
    ok, msg = llm.generate_matching_embeddings(db)
    print(msg)

    # 3. Pick a group to test
    print("\n[4] Fetching a test group...")
    conn = db.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT group_id FROM Matching LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("No groups found. Create a group first.")
        return

    group_id = row["group_id"]
    print("Testing group_id:", group_id)

    # 4. Test filtering step
    print("\n[5] Testing candidate filtering...")
    candidates = llm.filter_candidates(db, group_id)
    print("Filtered candidates:", candidates)

    if not candidates:
        print("No candidates passed filtering.")
        return

    # 5. Test embedding retrieval
    print("\n[6] Testing embedding retrieval...")
    embedded = llm.retrieve_embedding_candidates(
        db=db,
        group_id=group_id,
        candidate_ids=candidates,
        limit=5
    )
    print("Embedding-ranked candidates:", embedded)

    # 6. Test diversification
    print("\n[7] Testing diversification...")
    diversified = llm.diversify_candidates(
        db=db,
        candidates=embedded,
        limit=3
    )
    print("Diversified candidates:", diversified)

    # 7. Test final ranking
    print("\n[8] Testing final ranking...")
    final = llm.rank_by_profile_similarity(
        db=db,
        candidate_ids=diversified,
        limit=3
    )
    print("Final ranked matches:", final)

    # 8. Full pipeline test
    print("\n[9] Testing full recommendation pipeline...")
    results = llm.provide_recommendations(
        n_matches=3,
        db=db,
        group_id=group_id
    )
    print("FINAL RECOMMENDATIONS:", results)

    print("\n====================================")
    print("TEST COMPLETE")
    print("====================================")


if __name__ == "__main__":
    main()