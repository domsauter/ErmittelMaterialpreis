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

    QUERY_STANDARD = """
            SELECT
                (tabelle1.preis / tabelle2.gewicht) AS kg_preis,
                tabelle1.artnr,
                tabelle2.klass
            FROM database.tabelle1 tabelle1
            JOIN database.tabelle2 tabelle2 ON tabelle1.artnr = tabelle2.artnr
            JOIN database.tabelle3 tabelle3 ON tabelle1.besnr = tabelle3.besnr
            WHERE tabelle3.datum BETWEEN ? AND ?
                AND tabelle2.matgruppe BETWEEN '50' AND '54'
                AND LOWER(tabelle2.benennung) LIKE LOWER(?)
                AND tabelle2.benennung NOT LIKE '%TLB%'
                AND tabelle2.benennung NOT LIKE '%blank%'
                AND tabelle2.benennung NOT LIKE '%US%'
                AND tabelle2.gewicht <> 0
                AND tabelle1.menge <> 0
                AND tabelle2.klass LIKE 'D%x%'
                AND CAST(TRIM(SUBSTR(tabelle2.klass, 2, 3)) AS INTEGER) < 330
                AND CAST(TRIM(SUBSTR(tabelle2.klass, POSITION('x' IN tabelle2.klass) + 1, 4)) AS INTEGER) > 50
                AND tabelle3.lieferant LIKE ?
            """
    
    QUERY_D330 = """
            SELECT
                (tabelle1.preis / tabelle2.gewicht) AS kg_preis,
                tabelle1.artnr,
                tabelle2.klass
            FROM database.tabelle1 tabelle1
            JOIN database.tabelle2 tabelle2 ON tabelle1.artnr = tabelle2.artnr
            JOIN database.tabelle3 tabelle3 ON tabelle1.besnr = tabelle3.besnr
            WHERE tabelle3.datum BETWEEN ? AND ?
                AND tabelle2.matgruppe BETWEEN '50' AND '54'
                AND LOWER(tabelle2.benennung) LIKE LOWER(?)
                AND tabelle2.benennung NOT LIKE '%TLB%'
                AND tabelle2.benennung NOT LIKE '%blank%'
                AND tabelle2.benennung NOT LIKE '%US%'
                AND tabelle2.gewicht <> 0
                AND tabelle1.menge <> 0
                AND tabelle2.klass LIKE 'D%x%'
                AND CAST(TRIM(SUBSTR(tabelle2.klass, 2, 3)) AS INTEGER) > 330
                AND tabelle3.lieferant LIKE ?
            """
    
    QUERY_L50 = """
            SELECT
                (tabelle1.preis / tabelle2.gewicht) AS kg_preis,
                tabelle1.artnr,
                tabelle2.klass
            FROM database.tabelle1 tabelle1
            JOIN database.tabelle2 tabelle2 ON tabelle1.artnr = tabelle2.artnr
            JOIN database.tabelle3 tabelle3 ON tabelle1.besnr = tabelle3.besnr
            WHERE tabelle3.datum BETWEEN ? AND ?
                AND tabelle2.matgruppe BETWEEN '50' AND '54'
                AND LOWER(tabelle2.benennung) LIKE LOWER(?)
                AND tabelle2.benennung NOT LIKE '%TLB%'
                AND tabelle2.benennung NOT LIKE '%blank%'
                AND tabelle2.benennung NOT LIKE '%US%'
                AND tabelle2.gewicht <> 0
                AND tabelle1.menge <> 0
                AND tabelle2.klass LIKE 'D%x%'
                AND CAST(TRIM(SUBSTR(tabelle2.klass, POSITION('x' IN tabelle2.klass) + 1, 4)) AS INTEGER) < 50
                AND tabelle3.lieferant LIKE ?
            """

    @staticmethod
    def berechne_kg_preis(werkstoff: str, start: Optional[str] = None, ende: Optional[str] = None, 
                          durchmesser: Optional[str] = None, laenge: Optional[str] = None, lieferant: Optional[str] = None) -> Tuple[Optional[float], int, List[str]]:
        if start is None:
            start = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if ende is None:
            ende = datetime.today().strftime('%Y-%m-%d')
        if lieferant is None:
            lieferant = '%'
        if durchmesser is None or durchmesser == '':
            durchmesser_int = 0
        else:
            try:
                if durchmesser.startswith("D") and len(durchmesser) > 1:
                    durchmesser_int = int(durchmesser[1:])  # Entfernt "D" und wandelt den Rest in int um
                else:
                    durchmesser_int = int(durchmesser)  # Wandelt durchmesser direkt in int um
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

        werkstoff_like = f"%{werkstoff}%"
        lieferant_like = f"%{lieferant}%"

        if (durchmesser_int < 330 or durchmesser_int == 0) and (laenge_int >= 50 or laenge_int == 0):
            query = Database.QUERY_STANDARD
        elif durchmesser_int >= 330:
            query = Database.QUERY_D330
        else:
            query = Database.QUERY_L50

        conn = None
        try:
            conn = pyodbc.connect(Database.CONNECTION_STRING, timeout=900)
            cursor = conn.cursor()
            cursor.execute(query, start, ende, werkstoff_like, lieferant_like)

            total_kg_preis = 0
            i = 0
            artikelnummern = []
            abmessung = []
            kg_preise = []

            for row in cursor:
                kg_preis, artnr, klass = row
                if kg_preis is not None:
                    total_kg_preis += kg_preis
                    kg_preise.append(kg_preis)
                    artikelnummern.append(artnr)
                    abmessung.append(klass)
                    i += 1

            if i > 0:
                durchschnitt_kg_preis = total_kg_preis / i
                abweichung = 0
                for kg_preis in kg_preise:
                    abweichung += (kg_preis - durchschnitt_kg_preis)**2
                standardabweichung = (abweichung / i) ** 0.5 # wird momentan nicht verwendet, kann aber noch nützlich sein
                return durchschnitt_kg_preis, i, artikelnummern, abmessung
            else:
                return None, 0, [], []

        except pyodbc.Error as db_err:
            print(f"Datenbankfehler: {db_err}")
            return None, 0, [], []
        except Exception as e:
            print(f"Fehler: {e}")
            return None, 0, [], []
        finally:
            if conn:
                conn.close()
