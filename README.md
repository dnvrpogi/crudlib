# Library System

A simple SQL-based library management system using SQLite for storing books, tracking borrow/return transactions, and managing penalty rules by book type.

## Features

- Books table with `book_id`, `isbn`, `accession_number`, and `book_type`
- BookTransaction table with `transaction_id`, `transaction_date`, `student_id`, `due_date`, `borrow_date`, `return_date`, `penalty`, and `accession_number`
- Penalty table with `book_type`, `days_allowed`, and `daily_penalty`

## Web app usage

Start the SQL web app:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5001
```

## CLI usage

Initialize the database:

```bash
python library_system.py init
```

Add a book:

```bash
python library_system.py add-book 978-1-2345-6789-0 ACC-1001 Fiction
```

Add a penalty rule:

```bash
python library_system.py add-penalty Fiction 7 5.0
```

Borrow a book:

```bash
python library_system.py borrow S-001 ACC-1001 2026-09-25
```

Return a book:

```bash
python library_system.py return 1 2026-09-30
```

List records:

```bash
python library_system.py list books
python library_system.py list transactions
python library_system.py list penalties
```

## Notes

- The database file is created as `library.db` in the project folder.
- Penalty calculation is based on overdue days multiplied by the daily penalty for that book type.
