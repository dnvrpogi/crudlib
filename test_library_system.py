import os
import sqlite3
import tempfile
import unittest

from library_system import (
    add_book,
    add_penalty_rule,
    add_student,
    borrow_book,
    init_db,
    return_book,
)


class LibrarySystemTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_db(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_book_and_penalty_rule(self):
        self.assertTrue(add_book("978-1-2345-6789-0", "ACC-1001", "Fiction", self.db_path))
        add_penalty_rule("Fiction", 7, 5.0, self.db_path)

        conn = sqlite3.connect(self.db_path)
        book_row = conn.execute("SELECT isbn, accession_number, book_type FROM Books WHERE accession_number = ?", ("ACC-1001",)).fetchone()
        penalty_row = conn.execute("SELECT book_type, days_allowed, daily_penalty FROM Penalty WHERE book_type = ?", ("Fiction",)).fetchone()
        conn.close()

        self.assertEqual(book_row, ("978-1-2345-6789-0", "ACC-1001", "Fiction"))
        self.assertEqual(penalty_row, ("Fiction", 7, 5.0))

    def test_borrow_and_return_penalty(self):
        add_book("978-1-2345-6789-1", "ACC-1002", "Science", self.db_path)
        add_penalty_rule("Science", 3, 10.0, self.db_path)

        transaction_id, due_date = borrow_book("S-001", "ACC-1002", "2026-09-01", self.db_path)
        self.assertEqual(transaction_id, 1)
        self.assertEqual(due_date, "2026-09-04")

        penalty, overdue_days = return_book(transaction_id, "2026-09-10", self.db_path)
        self.assertEqual(overdue_days, 6)
        self.assertEqual(penalty, 60.0)

    def test_add_student(self):
        self.assertTrue(add_student("Juan Dela Cruz", "A", "2nd Year", "S-001", self.db_path))

        conn = sqlite3.connect(self.db_path)
        student_row = conn.execute(
            "SELECT student_name, section, year_level, student_id FROM Student WHERE student_id = ?",
            ("S-001",),
        ).fetchone()
        conn.close()

        self.assertEqual(student_row, ("Juan Dela Cruz", "A", "2nd Year", "S-001"))


if __name__ == "__main__":
    unittest.main()
