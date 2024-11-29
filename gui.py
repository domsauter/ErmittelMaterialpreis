import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from database import Database
from calculator import Calculator

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_styles()
        self.setup_variables()
        self.create_widgets()

    def setup_window(self):
        self.root.title("Stahl kg-Preis Berechnung")
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        if os.path.exists(logo_path):
            ico = Image.open(logo_path)
            photo = ImageTk.PhotoImage(ico)
            self.root.wm_iconphoto(False, photo)

    def setup_styles(self):
        self.styles: Dict[str, Any] = {
            'bg_color': "#44484C",
            'fg_color': "#C7CFD4",
            'fg_color_sec': "#14B1E7",
            'fg_color_alt': "#000",
            'font_ueberschrift': ("Tahoma", 11),
            'font_text': ("Tahoma", 10)
        }
        self.root["bg"] = self.styles['bg_color']

    def setup_variables(self):
        self.variables: Dict[str, tk.StringVar] = {
            'werkstoff': tk.StringVar(value="16MnCr5"),
            'startdatum': tk.StringVar(value=(datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')),
            'enddatum': tk.StringVar(value=datetime.today().strftime('%Y-%m-%d')),
            'durchmesser': tk.StringVar(),
            'lieferant': tk.StringVar(),
            'laenge': tk.StringVar(),
            'artikelnummern': tk.StringVar(),
            'ergebnis': tk.StringVar(),
            'stueckpreis': tk.StringVar(),
            'rueckgabe_datensaetze': tk.StringVar()
        }

    def create_widgets(self):
        self.create_labels()
        self.create_entries()
        self.create_button()
        self.create_result_labels()

    def create_labels(self):
        username = os.environ.get('USERNAME', '').split('.')[0].capitalize()
        ttk.Label(self.root, background=self.styles['bg_color'], 
                  text=f"Hallo {username}, hier kannst Du den ØStahl-kg-Preis auf verschiedenen Zeitebenen berechnen.", 
                  font=self.styles['font_ueberschrift'], foreground=self.styles['fg_color']).grid(row=0, column=0, padx=10, pady=15, sticky="w")

        labels = [
            ("Werkstoff (z.B. 16MnCr5, 18crnimo oder 42cr):", 1),
            ("Startdatum (YYYY-MM-DD):", 2),
            ("Enddatum (YYYY-MM-DD):", 3),
            ("Durchmesser (optional):", 4),
            ("Lieferant (optional):", 5),
            ("Hier kannst Du zusätzlich eine Länge eingeben, um den Materialpreis für Deine spezifische Abmessung zu berechnen.", 6),
            ("Länge (optional):", 7)
        ]

        for text, row in labels:
            font = self.styles['font_ueberschrift'] if row == 6 else self.styles['font_text']
            ttk.Label(self.root, background=self.styles['bg_color'], text=text, 
                      font=font, foreground=self.styles['fg_color']).grid(row=row, column=0, padx=10, pady=5, sticky="w")

    def create_entries(self):
        entries = ['werkstoff', 'startdatum', 'enddatum', 'durchmesser', 'lieferant', 'laenge']
        for i, var in enumerate(entries):
            if i != len(entries) - 1:
                ttk.Entry(self.root, textvariable=self.variables[var], 
                      font=self.styles['font_text']).grid(row=i+1, column=1, padx=10, pady=5)
            else:
                ttk.Entry(self.root, textvariable=self.variables[var], 
                      font=self.styles['font_text']).grid(row=i+2, column=1, padx=10, pady=5)


    def create_button(self):
        tk.Button(self.root, text="Berechnen", command=self.kg_preis_ausgabe, 
                  font=self.styles['font_text'], fg=self.styles['fg_color_alt']).grid(row=8, column=0, columnspan=2, pady=10)

    def create_result_labels(self):
        for i, var in enumerate(['ergebnis', 'stueckpreis', 'rueckgabe_datensaetze']):
            ttk.Label(self.root, background=self.styles['bg_color'], textvariable=self.variables[var], 
                      wraplength=800, font=self.styles['font_text'], 
                      foreground=self.styles['fg_color']).grid(row=9+i, column=0, columnspan=2, padx=10, pady=10)

    def kg_preis_ausgabe(self):
        if not self.validate_dates():
            return

        werkstoff = self.variables['werkstoff'].get().strip()
        startdatum = self.variables['startdatum'].get().strip()
        enddatum = self.variables['enddatum'].get().strip()
        lieferant = self.variables['lieferant'].get().strip()
        durchmesser = self.variables['durchmesser'].get().strip()

        durchschnitt, anzahl_datensaetze, artikelnummern = Database.berechne_kg_preis(werkstoff, startdatum, enddatum, durchmesser, lieferant)

        if durchschnitt is not None:
            self.variables['ergebnis'].set(f"Durchschnittlicher kg-Preis: {durchschnitt:.2f} €/kg")
            self.variables['rueckgabe_datensaetze'].set(f"Anzahl der gefundenen Datensätze: {anzahl_datensaetze}")
            self.stueckpreis_berechnen(werkstoff, durchschnitt)
            self.show_artikelnummern(artikelnummern)
        else:
            self.variables['ergebnis'].set("Keine Daten gefunden oder Fehler bei der Berechnung.")
            self.variables['rueckgabe_datensaetze'].set("")

    def validate_dates(self) -> bool:
        try:
            datetime.strptime(self.variables['startdatum'].get().strip(), '%Y-%m-%d')
            datetime.strptime(self.variables['enddatum'].get().strip(), '%Y-%m-%d')
            return True
        except ValueError:
            self.variables['ergebnis'].set("Bitte ein gültiges Datum im Format YYYY-MM-DD eingeben.")
            self.variables['rueckgabe_datensaetze'].set("")
            return False

    def stueckpreis_berechnen(self, werkstoff: str, durchschnitt: float):
        try:
            durchmesser = int(self.variables['durchmesser'].get().strip().replace('%', ''))
            laenge = int(self.variables['laenge'].get().strip().replace('%', ''))
            result = Calculator.stueckpreis_berechnen(werkstoff, durchschnitt, durchmesser, laenge)
            self.variables['stueckpreis'].set(result if result else "Keine Angaben für die Abmessungen angegeben.")
        except ValueError:
            self.variables['stueckpreis'].set("Keine Angaben für die Abmessungen angegeben.")

    def show_artikelnummern(self, artikelnummern: list[str]):
        if artikelnummern:
            ttk.Label(self.root, background=self.styles['bg_color'], text="Gefundene Datensätze:", 
                      font=self.styles['font_text'], foreground=self.styles['fg_color']).grid(row=12, column=0, columnspan=2, padx=10, pady=10)
            
            self.variables['artikelnummern'].set(artikelnummern[0])
            artikelnummern_dropdown = ttk.Combobox(self.root, textvariable=self.variables['artikelnummern'], 
                                                   values=artikelnummern, font=self.styles['font_text'])
            artikelnummern_dropdown.grid(row=13, column=0, columnspan=2, padx=0, pady=5)
            artikelnummern_dropdown.set(artikelnummern[0])
        else:
            self.variables['artikelnummern'].set("Keine Artikelnummern gefunden")

    def run(self):
        self.root.mainloop()
