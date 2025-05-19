from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flash messages


def init_db():
    """Initialize SQLite database and create transactions table."""
    try:
        with sqlite3.connect('database.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")


@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    """Handle adding a new transaction."""
    if request.method == 'POST':
        try:
            type_ = request.form['type']
            category = request.form['category'].strip()
            amount = request.form['amount']
            description = request.form['description'].strip()
            date = request.form['date'].strip() or datetime.now().strftime('%Y-%m-%d')

            # Validate inputs
            if type_ not in ['income', 'expense']:
                flash("Type must be 'income' or 'expense'.", "error")
                return redirect(url_for('add_transaction'))
            if not category:
                flash("Category is required.", "error")
                return redirect(url_for('add_transaction'))
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError("Amount must be positive.")
            except ValueError:
                flash("Amount must be a positive number.", "error")
                return redirect(url_for('add_transaction'))

            with sqlite3.connect('database.db') as conn:
                conn.execute('''
                    INSERT INTO transactions (type, category, amount, description, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (type_, category, amount, description, date))
                conn.commit()
            flash("Transaction added successfully!", "success")
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            flash(f"Database error: {e}", "error")
            return redirect(url_for('add_transaction'))
    return render_template('add_transaction.html')


@app.route('/view', methods=['GET', 'POST'])
def view_transactions():
    """Display transactions, optionally filtered by category."""
    category = None
    if request.method == 'POST':
        category = request.form['category'].strip()

    try:
        with sqlite3.connect('database.db') as conn:
            if category:
                cur = conn.execute('SELECT * FROM transactions WHERE category = ?', (category,))
            else:
                cur = conn.execute('SELECT * FROM transactions')
            transactions = cur.fetchall()
        return render_template('view_transactions.html', transactions=transactions, category=category)
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "error")
        return render_template('view_transactions.html', transactions=[], category=category)


@app.route('/summary')
def summary():
    """Display total income, expenses, and balance."""
    try:
        with sqlite3.connect('database.db') as conn:
            cur = conn.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
            total_income = cur.fetchone()[0] or 0
            cur = conn.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
            total_expenses = cur.fetchone()[0] or 0
        balance = total_income - total_expenses
        return render_template('summary.html', total_income=total_income, total_expenses=total_expenses,
                               balance=balance)
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "error")
        return render_template('summary.html', total_income=0, total_expenses=0, balance=0)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)