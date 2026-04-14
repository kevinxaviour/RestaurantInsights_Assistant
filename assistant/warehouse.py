import csv
import sqlite3
import threading
from datetime import datetime
from typing import Any

from .config import AssistantConfig


class CSVSQLiteWarehouse:
    def __init__(self, config: AssistantConfig):
        self.config = config
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(":memory:", check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._boot_table()

    def _boot_table(self) -> None:
        cur = self._connection.cursor()
        cur.execute(
            f"""
            CREATE TABLE {self.config.sqlite_table} (
                Order_ID INTEGER,
                Date TEXT,
                Product TEXT,
                Price REAL,
                Quantity REAL,
                Purchase_Type TEXT,
                Payment_Method TEXT,
                Manager TEXT,
                City TEXT
            )
            """
        )

        with self.config.csv_path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            rows = []
            for row in reader:
                date_value = datetime.strptime(
                    row["Date"].strip(), "%d-%m-%Y"
                ).strftime("%Y-%m-%d")
                rows.append(
                    (
                        int(row["Order_ID"]),
                        date_value,
                        row["Product"].strip(),
                        float(row["Price"]),
                        float(row["Quantity"]),
                        row["Purchase_Type"].strip(),
                        row["Payment_Method"].strip(),
                        " ".join(row["Manager"].split()),
                        row["City"].strip(),
                    )
                )

        cur.executemany(
            f"""
            INSERT INTO {self.config.sqlite_table}(
                Order_ID, Date, Product, Price, Quantity,
                Purchase_Type, Payment_Method, Manager, City
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self._connection.commit()

    def run(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        with self._lock:
            cur = self._connection.cursor()
            result = cur.execute(sql)
            columns = (
                [item[0] for item in result.description] if result.description else []
            )
            rows = [list(row) for row in result.fetchall()]
        return columns, rows

    def get_date_bounds(self) -> tuple[str, str]:
        with self._lock:
            cur = self._connection.cursor()
            result = cur.execute(
                f"SELECT MIN(Date) AS min_date, MAX(Date) AS max_date FROM {self.config.sqlite_table}"
            ).fetchone()
        return str(result[0]), str(result[1])

    def get_distinct_values(self, column_name: str) -> list[str]:
        with self._lock:
            cur = self._connection.cursor()
            rows = cur.execute(
                f"SELECT DISTINCT TRIM({column_name}) AS value FROM {self.config.sqlite_table} ORDER BY value"
            ).fetchall()
        return [str(item[0]) for item in rows if item[0] is not None]
