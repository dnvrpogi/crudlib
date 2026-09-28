import argparse
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).with_name("library.db")


def get_connection(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT NOT NULL,
            accession_number TEXT NOT NULL UNIQUE,
            book_type TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Penalty (
            book_type TEXT PRIMARY KEY,
            days_allowed INTEGER NOT NULL,
            daily_penalty REAL NOT NULL DEFAULT 10.0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Student (
            student_id TEXT PRIMARY KEY,
            student_name TEXT NOT NULL,
            section TEXT NOT NULL,
            year_level TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS BookTransaction (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            student_id TEXT NOT NULL,
            due_date TEXT NOT NULL,
            borrow_date TEXT NOT NULL,
            return_date TEXT,
            penalty REAL NOT NULL DEFAULT 0.0,
            accession_number TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Student(student_id),
            FOREIGN KEY (accession_number) REFERENCES Books(accession_number)
        )
        """
    )
    conn.commit()
    conn.close()


def add_book(isbn: str, accession_number: str, book_type: str, db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO Books (isbn, accession_number, book_type) VALUES (?, ?, ?)",
            (isbn, accession_number, book_type),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def add_penalty_rule(book_type: str, days_allowed: int, daily_penalty: float = 10.0, db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO Penalty (book_type, days_allowed, daily_penalty) VALUES (?, ?, ?) "
        "ON CONFLICT(book_type) DO UPDATE SET days_allowed=excluded.days_allowed, daily_penalty=excluded.daily_penalty",
        (book_type, days_allowed, daily_penalty),
    )
    conn.commit()
    conn.close()


def add_student(student_name: str, section: str, year_level: str, student_id: str, db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO Student (student_name, section, year_level, student_id) VALUES (?, ?, ?, ?)",
            (student_name, section, year_level, student_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_book_by_accession(accession_number: str, db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM Books WHERE accession_number = ?",
        (accession_number,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_penalty_rule(book_type: str, db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM Penalty WHERE book_type = ?",
        (book_type,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def borrow_book(student_id: str, accession_number: str, borrow_date: str, db_path: Path = DB_PATH):
    book = get_book_by_accession(accession_number, db_path)
    if not book:
        raise ValueError(f"Book with accession number {accession_number} does not exist.")

    penalty_rule = get_penalty_rule(book["book_type"], db_path)
    if not penalty_rule:
        raise ValueError(f"No penalty rule is set for book type: {book['book_type']}")

    borrow_dt = datetime.strptime(borrow_date, "%Y-%m-%d").date()
    due_date = (borrow_dt + __import__("datetime").timedelta(days=penalty_rule["days_allowed"])).isoformat()

    conn = get_connection(db_path)
    cursor = conn.execute(
        """
        INSERT INTO BookTransaction (transaction_date, student_id, due_date, borrow_date, return_date, penalty, accession_number)
        VALUES (?, ?, ?, ?, NULL, 0.0, ?)
        """,
        (borrow_date, student_id, due_date, borrow_date, accession_number),
    )
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    return transaction_id, due_date


def return_book(transaction_id: int, return_date: str, db_path: Path = DB_PATH):
    conn = get_connection(db_path)

    row = conn.execute(
        "SELECT bt.*, b.book_type FROM BookTransaction bt JOIN Books b ON b.accession_number = bt.accession_number WHERE bt.transaction_id = ?",
        (transaction_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Transaction {transaction_id} does not exist.")

    if row["return_date"] is not None:
        conn.close()
        raise ValueError(f"Book from transaction {transaction_id} has already been returned.")

    penalty_rule = get_penalty_rule(row["book_type"], db_path)
    if not penalty_rule:
        conn.close()
        raise ValueError(f"No penalty rule is set for book type: {row['book_type']}")

    due_dt = datetime.strptime(row["due_date"], "%Y-%m-%d").date()
    return_dt = datetime.strptime(return_date, "%Y-%m-%d").date()
    overdue_days = max(0, (return_dt - due_dt).days)
    computed_penalty = overdue_days * penalty_rule["daily_penalty"]

    conn.execute(
        "UPDATE BookTransaction SET return_date = ?, penalty = ? WHERE transaction_id = ?",
        (return_date, computed_penalty, transaction_id),
    )
    conn.commit()
    conn.close()
    return computed_penalty, overdue_days


def list_books(db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM Books ORDER BY book_id").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_transactions(db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT bt.transaction_id, bt.transaction_date, bt.student_id, bt.due_date, bt.borrow_date, bt.return_date, bt.penalty, bt.accession_number
        FROM BookTransaction bt
        ORDER BY bt.transaction_id
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_penalties(db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM Penalty ORDER BY book_type").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_students(db_path: Path = DB_PATH):
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM Student ORDER BY student_name").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Library system")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create database tables")

    add_book_parser = subparsers.add_parser("add-book", help="Add a book")
    add_book_parser.add_argument("isbn")
    add_book_parser.add_argument("accession_number")
    add_book_parser.add_argument("book_type")

    penalty_parser = subparsers.add_parser("add-penalty", help="Add or update a book-type penalty rule")
    penalty_parser.add_argument("book_type")
    penalty_parser.add_argument("days_allowed", type=int)
    penalty_parser.add_argument("daily_penalty", type=float, nargs="?", default=10.0)

    borrow_parser = subparsers.add_parser("borrow", help="Borrow a book")
    borrow_parser.add_argument("student_id")
    borrow_parser.add_argument("accession_number")
    borrow_parser.add_argument("borrow_date")

    return_parser = subparsers.add_parser("return", help="Return a borrowed book")
    return_parser.add_argument("transaction_id", type=int)
    return_parser.add_argument("return_date")

    add_student_parser = subparsers.add_parser("add-student", help="Add a student")
    add_student_parser.add_argument("student_name")
    add_student_parser.add_argument("section")
    add_student_parser.add_argument("year_level")
    add_student_parser.add_argument("student_id")

    list_parser = subparsers.add_parser("list", help="List entries")
    list_parser.add_argument("table", choices=["books", "transactions", "penalties", "students"])

    return parser


def run_command(args):
    if args.command == "init":
        init_db()
        print("Database initialized successfully.")
    elif args.command == "add-book":
        success = add_book(args.isbn, args.accession_number, args.book_type)
        if success:
            print(f"Book added: {args.accession_number}")
        else:
            print(f"Book with accession number {args.accession_number} already exists.")
    elif args.command == "add-penalty":
        add_penalty_rule(args.book_type, args.days_allowed, args.daily_penalty)
        print(f"Penalty rule saved for {args.book_type}.")
    elif args.command == "add-student":
        success = add_student(args.student_name, args.section, args.year_level, args.student_id)
        if success:
            print(f"Student added: {args.student_id}")
        else:
            print(f"Student with ID {args.student_id} already exists.")
    elif args.command == "borrow":
        transaction_id, due_date = borrow_book(args.student_id, args.accession_number, args.borrow_date)
        print(f"Borrowed successfully. Transaction ID: {transaction_id}, Due date: {due_date}")
    elif args.command == "return":
        penalty, overdue_days = return_book(args.transaction_id, args.return_date)
        print(f"Returned successfully. Penalty: {penalty:.2f}, overdue days: {overdue_days}")
    elif args.command == "list":
        if args.table == "books":
            rows = list_books()
            for row in rows:
                print(row)
        elif args.table == "transactions":
            rows = list_transactions()
            for row in rows:
                print(row)
        elif args.table == "penalties":
            rows = list_penalties()
            for row in rows:
                print(row)
        elif args.table == "students":
            rows = list_students()
            for row in rows:
                print(row)


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    run_command(args)
