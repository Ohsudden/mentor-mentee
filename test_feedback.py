
from database import Database
db = Database()

def test_feedback():
    change_matching_status = db.change_matching_status(1, "finished")
    print(change_matching_status)


test_feedback()