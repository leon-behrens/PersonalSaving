import argparse
import os
from database import create_db, insert_transaction, get_transactions, get_expenses_by_category, get_savings
from parser import parse_csv, parse_pdf

def main():
    create_db()  # Ensure DB exists

    parser = argparse.ArgumentParser(description='Personal Finance Tracker CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import transactions from a file')
    import_parser.add_argument('file', help='Path to CSV or PDF file')

    # View command
    subparsers.add_parser('view', help='View all transactions')

    # Expenses command
    subparsers.add_parser('expenses', help='View expenses by category')

    # Savings command
    subparsers.add_parser('savings', help='View total savings')

    args = parser.parse_args()

    if args.command == 'import':
        file_path = args.file
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        if file_path.endswith('.csv'):
            transactions = parse_csv(file_path)
        elif file_path.endswith('.pdf'):
            transactions = parse_pdf(file_path)
        else:
            print("Unsupported file type. Use CSV or PDF.")
            return

        if transactions:
            for t in transactions:
                insert_transaction(t['date'], t['description'], t['amount'], 'Other')
            print(f"Imported {len(transactions)} transactions.")
        else:
            print("No transactions found in the file.")

    elif args.command == 'view':
        trans = get_transactions()
        if trans:
            print("Date\t\tDescription\t\tAmount\t\tCategory")
            print("-" * 80)
            for row in trans:
                print(f"{row[0]}\t{row[1]}\t\t{row[2]}\t\t{row[3]}")
        else:
            print("No transactions yet.")

    elif args.command == 'expenses':
        expenses = get_expenses_by_category()
        if expenses:
            print("Category\t\tTotal Expense")
            print("-" * 40)
            for cat, total in expenses:
                print(f"{cat}\t\t{-total:.2f}")  # Negative for expenses
        else:
            print("No expenses recorded.")

    elif args.command == 'savings':
        savings = get_savings()
        print(f"Total Savings: ${savings:.2f}")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()