from typing import Optional

class Calculator:
    DICHTE_STAHL = 7.87 * 10**(-6)
    PI = 3.14159

    @staticmethod
    def stueckpreis_berechnen(werkstoff: str, durchschnitt: float, durchmesser: int, laenge: int) -> Optional[str]:
        if durchmesser <= 0 or laenge <= 0 or durchschnitt <= 0:
            return None

        radius = durchmesser / 2
        volumen_stahl = Calculator.PI * radius**2 * laenge
        masse_stahl = Calculator.DICHTE_STAHL * volumen_stahl
        stueckpreis = masse_stahl * durchschnitt
        return f"Der aktuelle Materialpreis für den Werkstoff {werkstoff} in der Abmessung D{durchmesser}x{laenge} beträgt: {stueckpreis:.2f} €/Stk."
