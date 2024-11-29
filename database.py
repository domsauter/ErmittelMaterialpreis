import pyodbc
from datetime import datetime, timedelta
from typing import Tuple, List, Optional

class Database:
    CONNECTION_STRING = (
        "DSN=xxxxxx;"
        "SERVER=xxxxxx;"
        "DATABASE=xxxxxx;"
        "SERVERTYPE=INGRES;"
        "DATEALIAS=ansidate;"
        "BLANKDATE=NULL;"
        "DATE1582=NULL;"
        "SELECTLOOPS=N;"
        "NUMERIC_OVERFLOW=IGNORE"
    )

    @staticmethod
    def berechne_kg_preis(werkstoff: str, start: Optional[str] = None, ende: Optional[str] = None, 
                          durchmesser: Optional[str] = None, lieferant: Optional[str] = None) -> Tuple[Optional[float], int, List[str]]:
        if start is None:
            start = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if ende is None:
            ende = datetime.today().strftime('%Y-%m-%d')
        if lieferant is None:
            lieferant = '%'
        if durchmesser is None:
            durchmesser = '%'

        werkstoff_like = f"%{werkstoff}%"
        durchmesser_like = f"%{durchmesser}x%"
        lieferant_like = f"%{lieferant}%"

        conn = None
        try:
            conn = pyodbc.connect(Database.CONNECTION_STRING, timeout=900)
            query = """
            SELECT TOP 5000
                (tabelle1.preis / tabelle2.gewicht) AS kg_preis,
                tabelle1.artnr
            FROM datenbank.tabelle1 tabelle1
            JOIN datenbank.tabelle2 tabelle2 ON tabelle1.artnr = tabelle2.artnr
            JOIN datenbank.tabelle3 tabelle3 ON tabelle1.besnr = tabelle3.besnr
            WHERE tabelle3.datum BETWEEN ? AND ?
                AND tabelle2.matgruppe BETWEEN '50' AND '54'
                AND LOWER(tabelle2.benennung) LIKE LOWER(?)
                AND tabelle2.benennung NOT LIKE '%TLB%'
                AND tabelle2.gewicht <> 0
                AND tabelle1.menge <> 0
                AND tabelle2.klass LIKE ?
                AND tabelle3.lieferant LIKE ?
            """
            cursor = conn.cursor()
            cursor.execute(query, start, ende, werkstoff_like, durchmesser_like, lieferant_like)

            total_kg_preis = 0
            i = 0
            artikelnummern = []
            for row in cursor:
                kg_preis, artnr = row
                if kg_preis is not None:
                    total_kg_preis += kg_preis
                    artikelnummern.append(artnr)
                    i += 1

            if i > 0:
                durchschnitt_kg_preis = total_kg_preis / i
                return durchschnitt_kg_preis, i, artikelnummern
            else:
                return None, 0, []

        except pyodbc.Error as db_err:
            print(f"Datenbankfehler: {db_err}")
            return None, 0, []
        except Exception as e:
            print(f"Fehler: {e}")
            return None, 0, []
        finally:
            if conn:
                conn.close()
