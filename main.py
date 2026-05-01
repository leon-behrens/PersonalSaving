import pymupdf as pdf
import re
from model.services.ReadDataFromPdf import ReadDataFromPdf
from model.databases.CreateDatabases import CreateDatabases


myPdfReader = ReadDataFromPdf("resources/sample.pdf")
myDatabase = CreateDatabases("resources/Accounts.db")

iban = myPdfReader.extractIban()
print(iban)
contract_number = myPdfReader.extractContractNumber()
print(contract_number)
account_holder = myPdfReader.extractAccountHolder()
print(account_holder)
account_type = myPdfReader.extractAccountType()
print(account_type)

myDatabase.addBankAccount(iban, account_holder, account_type, contract_number, "BLKB")