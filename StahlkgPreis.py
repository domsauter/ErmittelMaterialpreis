import pyodbc
import tkinter as tk
import os
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime, timedelta

def berechne_kg_preis(werkstoff, startdatum=None, enddatum=None, lieferant=None):
    # Standardwerte setzen
    if startdatum is None:
        startdatum = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')  # 30 Tage zurück
    if enddatum is None:
        enddatum = datetime.today().strftime('%Y-%m-%d')  # Heute
    if lieferant is None:
        lieferant = '%'  # Alle Lieferanten (Wildcards für LIKE-Abfrage)

    # Werkstoff für die SQL-Abfrage vorbereiten, um ihn flexibel zu machen
    werkstoff_like = f"%{werkstoff}%"

    conn = None  # Variable vorab definieren
    try:
        # Verbindungszeichenfolge (angepasst)
        connection_string = (
            "DSN=your_dsn;"
            "SERVER=your_server;"
            "DATABASE=your_database;"
            "SERVERTYPE=INGRES;"
            "DATEALIAS=ansidate;"
            "BLANKDATE=NULL;"
            "DATE1582=NULL;"
            "SELECTLOOPS=N;"
            "NUMERIC_OVERFLOW=IGNORE"
        )

        # Verbindung zur Datenbank herstellen
        conn = pyodbc.connect(connection_string, timeout=900)

        # SQL-Abfrage (angepasst und parametrisiert)
        query = """
        SELECT TOP 5000
            (tabelle1.spalte1 / tabelle2.spalte2) AS kg_preis  -- Berechnung des kg-Preises
        FROM datenbank.tabelle1 tabelle1
        JOIN datenbank.tabelle2 tabelle2 ON tabelle1.spalte3 = tabelle2.spalte3
        JOIN datenbank.tabelle3 tabelle3 ON tabelle1.spalte4 = tabelle3.spalte4
        WHERE tabelle3.datum_spalte BETWEEN ? AND ?
            AND tabelle2.gruppen_spalte BETWEEN '50' AND '54'
            AND LOWER(tabelle2.material_spalte) LIKE LOWER(?)  -- Werkstoff als Teilstring abfragen und Groß-/Kleinschreibung nicht beachten
            AND tabelle2.material_spalte NOT LIKE '%TLB%'  -- TLB ausschließen
            AND tabelle2.gewicht_spalte <> 0  -- Gewicht ungleich 0
            AND tabelle1.menge_spalte <> 0  -- Menge ungleich 0
            AND tabelle3.lieferant_spalte LIKE ?  
        """
        
        # Abfrage ausführen und Parameter übergeben
        cursor = conn.cursor()
        cursor.execute(query, startdatum, enddatum, werkstoff_like, lieferant)

        # Summen und Zähler für den kg-Preis berechnen
        total_kg_preis = 0
        i = 0
        
        # Alle Zeilen durchgehen und den kg-Preis aufsummieren
        for row in cursor:
            kg_preis = row[-1]  # Der kg-Preis ist in der letzten Spalte
            if kg_preis is not None:
                total_kg_preis += kg_preis
                i += 1
        
        # Durchschnitt berechnen
        if i > 0:
            durchschnitt_kg_preis = total_kg_preis / i
            return durchschnitt_kg_preis
        else:
            return None

    except Exception as e:
        print(f"Fehler beim Ausführen der Datenbankabfrage: {e}")
        return f"Fehler: {e}"
    finally:
        if conn:
            conn.close()

# Funktion, die beim Button-Klick aufgerufen wird
def kg_ausgabe():
    werkstoff = werkstoff_var.get().strip()
    startdatum = startdatum_var.get().strip()
    enddatum = enddatum_var.get().strip()
    lieferant = lieferant_var.get().strip()

    durchschnitt = berechne_kg_preis(werkstoff, startdatum, enddatum, lieferant)
    
    if isinstance(durchschnitt, str):  # Wenn ein Fehlertext zurückgegeben wurde
        ergebnis_var.set(durchschnitt)
    elif durchschnitt is not None:
        ergebnis_var.set(f"Durchschnittlicher kg-Preis: {durchschnitt:.2f} €/kg")
    else:
        ergebnis_var.set("Keine Daten gefunden oder Fehler bei der Berechnung.")

# Hauptfenster erstellen
root = tk.Tk()

# Hintergrundfarbe definieren
bg_color_main = "#FFF"
bg_color_sec = "#034EA2"

# Den Pfad zum aktuellen Verzeichnis bekommen
current_directory = os.path.dirname(
