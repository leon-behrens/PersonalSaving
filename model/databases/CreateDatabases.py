import sqlite3

class CreateDatabases:

    cursor: sqlite3.Cursor

    def __init__(self, PathToDb) -> None:
        self.cursor = sqlite3.connect(PathToDb).cursor()
        

    def createAccountDatabase(self) -> None:
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS BankAccounts (
                                id INTEGER PRIMARY KEY,
                                iban TEXT NOT NULL UNIQUE,
                                owner_name TEXT,
                                account_type TEXT,
                                contract_number TEXT UNIQUE,
                                bank_name TEXT
                            )''')
        
    def addBankAccount(self, iban: str, owner_name: str, account_type: str, contract_number: str, bank_name: str) -> None:
        self.createAccountDatabase()

        self.cursor.execute('''INSERT INTO BankAccounts (iban, owner_name, account_type, contract_number, bank_name)
                            VALUES (?, ?, ?, ?, ?)''', (iban, owner_name, account_type, contract_number, bank_name))
        self.cursor.connection.commit()
