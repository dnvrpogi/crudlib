import os

from flask import Flask, flash, redirect, render_template, request, url_for

from library_system import (
    add_book,
    add_penalty_rule,
    add_student,
    borrow_book,
    init_db,
    list_books,
    list_penalties,
    list_students,
    list_transactions,
    return_book,
)

app = Flask(__name__)
app.secret_key = "library-secret-key"

init_db()


@app.route("/")
def index():
    books = list_books()
    penalties = list_penalties()
    students = list_students()
    transactions = list_transactions()
    return render_template("index.html", books=books, penalties=penalties, students=students, transactions=transactions)


@app.route("/students/add", methods=["POST"])
def add_student_route():
    student_name = request.form.get("student_name", "").strip()
    section = request.form.get("section", "").strip()
    year_level = request.form.get("year_level", "").strip()
    student_id = request.form.get("student_id", "").strip()

    if not student_name or not section or not year_level or not student_id:
        flash("Please fill in all student fields.", "error")
        return redirect(url_for("index"))

    if add_student(student_name, section, year_level, student_id):
        flash("Student added successfully.", "success")
    else:
        flash("This student ID already exists.", "error")

    return redirect(url_for("index"))


@app.route("/books/add", methods=["POST"])
def add_book_route():
    isbn = request.form.get("isbn", "").strip()
    accession_number = request.form.get("accession_number", "").strip()
    book_type = request.form.get("book_type", "").strip()

    if not isbn or not accession_number or not book_type:
        flash("Please fill in all book fields.", "error")
        return redirect(url_for("index"))

    if add_book(isbn, accession_number, book_type):
        flash("Book added successfully.", "success")
    else:
        flash("This accession number already exists.", "error")

    return redirect(url_for("index"))


@app.route("/penalties/add", methods=["POST"])
def add_penalty_route():
    book_type = request.form.get("book_type", "").strip()
    days_allowed = request.form.get("days_allowed", "").strip()
    daily_penalty = request.form.get("daily_penalty", "10").strip()

    if not book_type or not days_allowed:
        flash("Book type and days allowed are required.", "error")
        return redirect(url_for("index"))

    try:
        add_penalty_rule(book_type, int(days_allowed), float(daily_penalty))
        flash("Penalty rule saved successfully.", "success")
    except ValueError:
        flash("Please enter valid numeric values for days and penalty.", "error")

    return redirect(url_for("index"))


@app.route("/transactions/borrow", methods=["POST"])
def borrow_route():
    student_id = request.form.get("student_id", "").strip()
    accession_number = request.form.get("accession_number", "").strip()
    borrow_date = request.form.get("borrow_date", "").strip()

    if not student_id or not accession_number or not borrow_date:
        flash("Student ID, accession number, and borrow date are required.", "error")
        return redirect(url_for("index"))

    try:
        transaction_id, due_date = borrow_book(student_id, accession_number, borrow_date)
        flash(f"Book borrowed successfully. Transaction ID: {transaction_id}. Due date: {due_date}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("index"))


@app.route("/transactions/return", methods=["POST"])
def return_route():
    transaction_id = request.form.get("transaction_id", "").strip()
    return_date = request.form.get("return_date", "").strip()

    if not transaction_id or not return_date:
        flash("Transaction ID and return date are required.", "error")
        return redirect(url_for("index"))

    try:
        penalty, overdue_days = return_book(int(transaction_id), return_date)
        flash(f"Book returned successfully. Penalty: {penalty:.2f}. Overdue days: {overdue_days}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    except TypeError:
        flash("Please enter a valid transaction ID.", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=True, host="0.0.0.0", port=port)
