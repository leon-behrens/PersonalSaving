# Personal Finance Tracker

A Python CLI application to read bank statements, store transactions in a database, and view expenses by category.

## Setup

1. Install dependencies: `pip install -r requirements.txt`

2. Run commands using: `python main.py <command>`

## Usage

### Import transactions from a file
`python main.py import path/to/file.csv` or `python main.py import path/to/file.pdf`

### View all transactions
`python main.py view`

### View expenses by category
`python main.py expenses`

### View total savings
`python main.py savings`

For CSV files, ensure columns are named 'date', 'description', 'amount'. PDF parsing is basic text extraction - you may need to adjust the parser for specific statement formats.