import sqlite3
import os

DB_PATH = 'finance.db'

def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    description TEXT,
                    amount REAL,
                    category_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )''')
    # Insert default categories
    default_categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Savings', 'Other']
    for cat in default_categories:
        c.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
    conn.commit()
    conn.close()

def insert_transaction(date, description, amount, category_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
    cat_id = c.fetchone()
    if cat_id:
        c.execute('INSERT INTO transactions (date, description, amount, category_id) VALUES (?, ?, ?, ?)',
                  (date, description, amount, cat_id[0]))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT t.date, t.description, t.amount, c.name
                 FROM transactions t
                 JOIN categories c ON t.category_id = c.id
                 ORDER BY t.date''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_expenses_by_category():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT c.name, SUM(t.amount) as total
                 FROM transactions t
                 JOIN categories c ON t.category_id = c.id
                 WHERE t.amount < 0
                 GROUP BY c.name''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_savings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT SUM(amount) FROM transactions WHERE amount > 0''')
    savings = c.fetchone()[0] or 0
    conn.close()
    return savings