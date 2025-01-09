import pyodbc
from datetime import datetime, timedelta
from typing import Tuple, List, Optional

class Database:
    CONNECTION_STRING = (
        "DSN=xxxxx;"
        "SERVER=xxxxx;"
        "DATABASE=xxxxx;"
        "SERVERTYPE=INGRES;"
        "DATEALIAS=ansidate;"
        "BLANKDATE=NULL;"
        "DATE1582=NULL;"
        "SELECTLOOPS=N;"
        "NUMERIC_OVERFLOW=IGNORE"
    )

    BASE_QUERY = """
        SELECT
            (tabelle1.preis / tabelle2.gewicht) AS kg_preis,
            tabelle1.artnr,
            tabelle2.klass
        FROM schema.tabelle1 tabelle1
        JOIN schema.tabelle2 tabelle2 ON tabelle1.artnr = tabelle2.artnr
        JOIN schema.tabelle3 tabelle3 ON tabelle1.besnr = tabelle3.besnr
        WHERE tabelle3.datum BETWEEN ? AND ?
            AND tabelle2.matgruppe BETWEEN '50' AND '54'
            AND LOWER(tabelle2.benennung) LIKE LOWER(?)
            AND tabelle2.benennung NOT LIKE '%TLB%'
            AND tabelle2.benennung NOT LIKE '%blank%'
            AND tabelle2.benennung NOT LIKE '%US%'
            AND tabelle2.benennung NOT LIKE '%hartverchromt%'
            AND tabelle2.benennung NOT LIKE '%HH%'
            AND tabelle2.benennung NOT LIKE '%QT%'
            AND tabelle2.gewicht <> 0
            AND tabelle1.menge <> 0
            AND tabelle2.klass LIKE 'D%x%'
    """

    @staticmethod
    def berechne_kg_preis(
        werkstoff: str,
        start: Optional[str] = None,
        ende: Optional[str] = None,
        durchmesser: Optional[str] = None,
        laenge: Optional[str] = None,
        lieferant: Optional[str] = None,
    ) -> Tuple[Optional[float], int, List[str], List[str]]:
        # Standardwerte
        start = start or (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        ende = ende or datetime.today().strftime('%Y-%m-%d')
        lieferant_like = f"%{lieferant or ''}%"
        werkstoff_like = f"%{werkstoff}%"

        # Umwandlung von durchmesser und laenge in Integer
        if durchmesser is None or durchmesser == '':
            durchmesser_int = 0
        else:
            try:
                if durchmesser.startswith("D") and len(durchmesser) > 1:
                    durchmesser_int = int(durchmesser[1:])  # Entfernt "D" und wandelt den Rest in int um
                else:
                    durchmesser_int = int(durchmesser)
            except ValueError:
                print(f"Ungültiger Durchmesserwert: {durchmesser}")
                durchmesser_int = 0

        if laenge is None or laenge == '':
            laenge_int = 0
        else:
            try:
                laenge_int = int(laenge)
            except ValueError:
                print(f"Ungültiger Längenwert: {laenge}")
                laenge_int = 0

        # Dynamische Bedingungen für durchmesser und laenge
        conditions = []
        if durchmesser_int < 330 or durchmesser_int == 0:
            conditions.append("CAST(TRIM(SUBSTR(tabelle2.klass, 2, 3)) AS INTEGER) < 330")
        else:
            conditions.append("CAST(TRIM(SUBSTR(tabelle2.klass, 2, 3)) AS INTEGER) >= 330")
        
        if laenge_int >= 50 or laenge_int == 0:
            conditions.append("CAST(TRIM(SUBSTR(tabelle2.klass, POSITION('x' IN tabelle2.klass) + 1, 4)) AS INTEGER) >= 50")
        else:
            conditions.append("CAST(TRIM(SUBSTR(tabelle2.klass, POSITION('x' IN tabelle2.klass) + 1, 4)) AS INTEGER) < 50")

        conditions.append("tabelle3.liefnr LIKE ?")

        # Finalisierung der Query
        final_query = Database.BASE_QUERY + " AND " + " AND ".join(conditions)

        # Datenbankabfrage
        conn = None
        try:
            conn = pyodbc.connect(Database.CONNECTION_STRING, timeout=900)
            cursor = conn.cursor()
            cursor.execute(final_query, start, ende, werkstoff_like, lieferant_like)

            results = cursor.fetchall()
            if not results:
                return None, 0, [], []

            kg_preise = [row[0] for row in results if row[0] is not None]
            artikelnummern = [row[1] for row in results]
            abmessungen = [row[2] for row in results]

            durchschnitt_kg_preis = sum(kg_preise) / len(kg_preise)
            return durchschnitt_kg_preis, len(kg_preise), artikelnummern, abmessungen

        except pyodbc.Error as db_err:
            print(f"Datenbankfehler: {db_err}")
            return None, 0, [], []
        except Exception as e:
            print(f"Fehler: {e}")
            return None, 0, [], []
        finally:
            if conn:
                conn.close()
