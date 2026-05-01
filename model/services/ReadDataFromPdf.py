import pymupdf as pdf
import re

class ReadDataFromPdf:

    FilePath: str
    Doc: pdf.Document
    out: str

    def __init__(self, file_path) -> None:
        self.FilePath = file_path
        self.Doc = pdf.open(self.FilePath)
        self.out = self.Doc[0].get_text("text")

    def extractIban(self) -> str | None:

        match = re.search("IBAN: " + r"[A-Z]{2}\d{2}[A-Z0-9 ]{11,30}", self.out)

        if match:
            iban = match.group()
            return iban.replace("IBAN:", "").strip()
        else:
            return None
        
    def extractContractNumber(self) -> str | None:

        match = re.search(r"Vertrag\s+(\d{4,})", self.out)
        if match:
            return match.group(1).strip()
        else:
            return None
        
    def extractAccountHolder(self) -> str | None:
        match = re.search(r"Kontoauszug\s*\n+([^\n]+)", self.out, re.IGNORECASE)

        if match:
            return match.group(1).strip("\\/| ")

        return None
    
    import re

    def extractAccountType(self) -> str | None:
        search_area = self.out[:500]

        ignored_words = {
            "kontonummer",
            "kontoauszug",
            "kontoinhaber",
            "kontostand",
        }

        matches = re.finditer(
            r"\b[\wäöüÄÖÜß-]*konto[\wäöüÄÖÜß-]*\b",
            search_area,
            re.IGNORECASE
        )

        for match in matches:
            account_type = match.group().strip("\\/|.,:;()[]{} ")

            if account_type.lower() in ignored_words:
                continue

            return account_type

        return None