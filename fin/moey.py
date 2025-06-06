import re
from datetime import datetime
from typing import BinaryIO

import pdfplumber

from fin.models import Transaction


def parse_pdf(pdf_file: BinaryIO):
    with pdfplumber.open(pdf_file) as pdf:
        text = [page.extract_text() for page in pdf.pages]
        lines = [line for page in text for line in page.split("\n")]
        transactions = []
        for line in lines:
            if _is_transaction(line):
                account_date = line.split(" / ")[0]
                remaining_line = line.split(" / ")[1].split(" ")[1:]
                amount_cents = int(remaining_line[-3].replace(",", "").replace(".", ""))
                if remaining_line[-2] == "-":
                    amount_cents = -amount_cents
                description = " ".join(remaining_line[:-3])

                transactions.append(Transaction(
                    created_at=datetime.strptime(account_date, "%d-%m-%Y"),
                    description=description,
                    amount_cents=amount_cents,
                ))
        return transactions

def _is_transaction(line):
    # good line starts with "01-04-2024 / 31-03-2024 "
    return re.match(r"^\d{2}-\d{2}-\d{4} / \d{2}-\d{2}-\d{4} ", line)