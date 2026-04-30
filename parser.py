import pandas as pd
import pdfplumber

def parse_csv(file_path):
    df = pd.read_csv(file_path)
    # Assume columns: date, description, amount
    transactions = []
    for _, row in df.iterrows():
        transactions.append({
            'date': str(row['date']),
            'description': str(row['description']),
            'amount': float(row['amount'])
        })
    return transactions

def parse_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    # Simple parsing: assume lines with date, desc, amount
    transactions = []
    lines = text.split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            try:
                date = parts[0]
                amount = float(parts[-1])
                desc = ' '.join(parts[1:-1])
                transactions.append({
                    'date': date,
                    'description': desc,
                    'amount': amount
                })
            except:
                pass
    return transactions