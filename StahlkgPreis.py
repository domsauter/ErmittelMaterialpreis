import pyodbc
import tkinter as tk
import os
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime, timedelta

def berechne_kg_preis(werkstoff, start=None, ende=None, durchmesser=None, lieferant=None):
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
        connection_string = (
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
        conn = pyodbc.connect(connection_string, timeout=900)

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
            kg_preis = row[0]
            artnr = row[1]
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
        return f"Datenbankfehler: {db_err}", 0, []
    except Exception as e:
        print(f"Fehler: {e}")
        return f"Fehler: {e}", 0, []
    finally:
        if conn:
            conn.close()


def kg_preis_ausgabe():
    werkstoff = werkstoff_var.get().strip()
    startdatum = startdatum_var.get().strip()
    enddatum = enddatum_var.get().strip()
    lieferant = lieferant_var.get().strip()
    durchmesser = durchmesser_var.get().strip()

    try:
        datetime.strptime(startdatum, '%Y-%m-%d')
        datetime.strptime(enddatum, '%Y-%m-%d')
    except ValueError:
        ergebnis_var.set("Bitte ein gültiges Datum im Format YYYY-MM-DD eingeben.")
        rueckgabe_datensaetze_var.set("")
        return

    durchschnitt, anzahl_datensaetze, artikelnummern = berechne_kg_preis(werkstoff, startdatum, enddatum, durchmesser, lieferant)

    if isinstance(durchschnitt, str):  # Falls ein Fehler auftritt
        ergebnis_var.set(durchschnitt)
        rueckgabe_datensaetze_var.set("")
    elif durchschnitt is not None:
        # Zeige den formatierten Text für das Ergebnis in der GUI
        ergebnis_var.set(f"Durchschnittlicher kg-Preis: {durchschnitt:.2f} €/kg")
        rueckgabe_datensaetze_var.set(f"Anzahl der gefundenen Datensätze: {anzahl_datensaetze}")
        ttk.Label(root, background=bg_color_main, text="Gefundene Datensätze:", font=font_text, foreground=fg_color_main).grid(row=12, column=0, columnspan=2, padx=10, pady=10)
        stueckpreis_berechnen(werkstoff, durchschnitt)

        # Zeige die Artikelnummern im Dropdown-Menü an
        if artikelnummern:
            artikelnummern_var.set(artikelnummern[0])  # Setze den Standardwert

            # Dropdown-Menü für Artikelnummern
            artikelnummern_dropdown = ttk.Combobox(root, textvariable=artikelnummern_var, values=artikelnummern, font=font_text)
            artikelnummern_dropdown.grid(row=13, column=0, columnspan=2, padx=0, pady=5)
            artikelnummern_dropdown.set(artikelnummern[0])  # Setzt die erste Artikelnummer als Standard
        else:
            artikelnummern_var.set("Keine Artikelnummern gefunden")
    else:
        ergebnis_var.set("Keine Daten gefunden oder Fehler bei der Berechnung.")
        rueckgabe_datensaetze_var.set("")

def stueckpreis_berechnen(werkstoff, durchschnitt):
    durchmesser_str = durchmesser_var.get().strip().replace('%', '')
    laenge_str = laenge_var.get().strip().replace('%', '')

    DICHTE_STAHL = 7.87 *10**(-6)
    PI = 3.14159

    try:
        # Werte konvertieren
        durchmesser = int(durchmesser_str)
        laenge = int(laenge_str)
    except ValueError:
        stueckpreis_var.set("Keine Angaben für die Abmessungen angegeben.")  # Wenn ein Wert ungültig ist
        return  # Falls die Konvertierung fehlschlägt (ungültige Eingabe)

    # Berechnung nur, wenn alle Werte gültig sind
    if durchmesser > 0 and laenge > 0 and durchschnitt > 0:
        radius = durchmesser / 2
        volumen_stahl = PI * radius**2 * laenge
        masse_stahl = DICHTE_STAHL * volumen_stahl
        stueckpreis = masse_stahl * durchschnitt
        stueckpreis_var.set(f"Der aktuelle Materialpreis für den Werkstoff {werkstoff} in der Abmessung D{durchmesser}x{laenge} beträgt: {stueckpreis:.2f} €/Stk.")  # Setze den berechneten Preis in das Label
    else:
        pass


root = tk.Tk()

# Style-Variablen
bg_color_main = "#44484C"
fg_color_main = "#C7CFD4"
fg_color_sec = "#14B1E7"
fg_color_alt = "#000"
font_ueberschrift = ("Tahoma", 11)
font_text = ("Tahoma", 10)

current_directory = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')

root.title("Stahl kg-Preis Berechnung")
ico = Image.open(logo_path)
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)
root["bg"] = bg_color_main

username = os.environ.get('USERNAME', '')
first_name = username.split('.')[0]
first_name = first_name.capitalize()

werkstoff_var = tk.StringVar()
startdatum_var = tk.StringVar(value=(datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
enddatum_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
durchmesser_var = tk.StringVar(value='%')
lieferant_var = tk.StringVar(value='%')
laenge_var = tk.StringVar(value='%')
artikelnummern_var = tk.StringVar()

# Benutzeroberfläche erstellen
ttk.Label(root, background=bg_color_main, text=f"Hallo {first_name}, hier kannst Du den ØStahl-kg-Preis auf verschiedenen Zeitebenen berechnen.", font=font_ueberschrift, foreground=fg_color_main).grid(row=0, column=0, padx=10, pady=15, sticky="w")

# Eingabefelder
ttk.Label(root, background=bg_color_main, text="Werkstoff (z.B. 16MnCr5, 18crnimo oder 42cr):", font=font_text, foreground=fg_color_main).grid(row=1, column=0, padx=10, pady=5, sticky="w")
werkstoff_entry = ttk.Entry(root, textvariable=werkstoff_var, font=font_text)
werkstoff_entry.insert(0, "16MnCr5")
werkstoff_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, background=bg_color_main, text="Startdatum (YYYY-MM-DD):", font=font_text, foreground=fg_color_main).grid(row=2, column=0, padx=10, pady=5, sticky="w")
ttk.Entry(root, textvariable=startdatum_var, font=font_text).grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, background=bg_color_main, text="Enddatum (YYYY-MM-DD):", font=font_text, foreground=fg_color_main).grid(row=3, column=0, padx=10, pady=5, sticky="w")
ttk.Entry(root, textvariable=enddatum_var, font=font_text).grid(row=3, column=1, padx=10, pady=5)

ttk.Label(root, background=bg_color_main, text="Durchmesser (optional):", font=font_text, foreground=fg_color_main).grid(row=4, column=0, padx=10, pady=5, sticky="w")
ttk.Entry(root, textvariable=durchmesser_var, font=font_text).grid(row=4, column=1, padx=10, pady=5)

ttk.Label(root, background=bg_color_main, text="Lieferant (optional):", font=font_text, foreground=fg_color_main).grid(row=5, column=0, padx=10, pady=5, sticky="w")
ttk.Entry(root, textvariable=lieferant_var, font=font_text).grid(row=5, column=1, padx=10, pady=5)

# Eingabe einer Länge um zusätzlich noch den Preis einer bestimmten Abmessung zu berechnen.
ttk.Label(root, background=bg_color_main, text="Hier kannst Du zusätzlich eine Länge eingeben, um den Materialpreis für Deine spezifische Abmessung zu berechnen.", font=font_ueberschrift, foreground=fg_color_main).grid(row=6, column=0, padx=10, pady=15, sticky="w")
ttk.Label(root, background=bg_color_main, text="Länge (optional):", font=font_text, foreground=fg_color_main).grid(row=7, column=0, padx=10, pady=5, sticky="w")
ttk.Entry(root, textvariable=laenge_var, font=font_text).grid(row=7, column=1, padx=10, pady=5)

tk.Button(root, text="Berechnen", command=kg_preis_ausgabe, font=font_text, fg=fg_color_alt).grid(row=8, column=0, columnspan=2, pady=10)

# Ergebnisanzeige
ergebnis_var = tk.StringVar()
ttk.Label(root, background=bg_color_main, textvariable=ergebnis_var, wraplength=600, font=font_text, foreground=fg_color_main).grid(row=9, column=0, columnspan=2, padx=10, pady=10)
stueckpreis_var = tk.StringVar()
ttk.Label(root, background=bg_color_main, textvariable=stueckpreis_var, wraplength=600, font=font_text, foreground=fg_color_main).grid(row=10, column=0, columnspan=2, padx=10, pady=10)
rueckgabe_datensaetze_var = tk.StringVar()
ttk.Label(root, background=bg_color_main, textvariable=rueckgabe_datensaetze_var, wraplength=600, font=font_text, foreground=fg_color_main).grid(row=11, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()
