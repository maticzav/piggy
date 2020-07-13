import pendulum
import json

"""
POMEMBNO: 

Nekaj pomembnejših napotkov:
    1. količina je predstavljena s celimi števili v centih (1€ = 100).
"""

# ----------------------------------------------------------------------------


class Racun:
    """
    Račun predstavlja en račun posameznega uporabnika z danim davkom.
    Davka po ustvarjenju računa ni mogoče spremenit.

    Količino denarja, ki gre v kuverte, izračunamo tako,
    da seštejemo oziroma odštejemo skupaj vse ponavljajoce transakcije,
    in upoštevamo davek.

    razpolozljivo = (ponavljajoci_prihodki) * (1 - davek) - (ponavljajoci_izdatki)
    """

    def __init__(self, ime: str, davek: float):
        self.ime = ime
        assert (davek >= 0 and davek <= 1), "Davek mora predstavljat odstotek."
        self.davek = davek

        self.ponavljajoce_transakcije = []
        self.kuverte = []
        self.transakcije = []

        self.arhiviran = False

    # Izračunane vrednosti ---------------------------------------------------

    """Izračuna koliko denarja lahko razdelimo med kuverte."""
    @property
    def razpolozljiv_denar_za_kuverte(self):
        return self.vsi_prihodki * (1 - self.davek) - self.vsi_odhodki

    """Vsi prihodki do dne."""
    @property
    def vsi_prihodki(self):
        vsota = 0
        for transakcija in self.ponavljajoce_transakcije:
            if transakcija.je_dohodek:
                vsota += transakcija.skupna_kolicina
        for transakcija in self.transakcije:
            if transakcija.je_dohodek:
                vsota += transakcija.kolicina
        return vsota

    """Vsi odhodki do dne, kot pozitivna vsota."""
    @property
    def vsi_odhodki(self):
        vsota = 0
        for transakcija in self.ponavljajoce_transakcije:
            if transakcija.je_odhodek:
                vsota -= transakcija.skupna_kolicina
        for transakcija in self.transakcije:
            if transakcija.je_odhodek:
                vsota -= transakcija.kolicina
        return vsota

    """Ves denar, ki smo ga našparali z davkom."""
    @property
    def nasparano(self):
        return self.vsi_prihodki * self.davek

    """Denar, ki ni šel v šparovec in ga nismo porabili v kuvertah."""

    @property
    def ostalo(self):
        pass

    @property
    def porabljen_denar_v_kuvertah(self):
        return sum([kuverta.stanje for kuverta in self.kuverte])

    # Namere -----------------------------------------------------------------

    """Začne nov ponavljajoči prihodek."""

    def ustvari_ponavljajoco_transakcijo(self, opis: str, kolicina: int):
        transakcija = PonavljajocaTransakcija(opis=opis, kolicina=kolicina)
        self.ponavljajoce_transakcije.append(transakcija)
        return transakcija

    """Zaključi ponavljajočo transakcijo."""

    def koncaj_ponavljajoco_transakcijo(self, id):
        pass

    """Ustvari novo kuverto."""

    def ustvari_kuverto(self, opis: str):
        pass

    """Arhivira račun tako, da arhivira use ponavljajoče transakcije in kuverte."""

    def arhiviraj(self):
        pass


class Kuverta:
    """
    Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    barva in ikona pa pomagata pri ustvarjanju vizualne razlike.
    Limita je količina denarja, ki ga lahko porabimo iz kuverte.
    """

    def __init__(self, ime: str, limita: int, barva="modra", ikona="kuverta"):
        self.ime = ime
        self.limita = limita
        self.barva = barva
        self.ikona = ikona

        self.nastanek = pendulum.now()
        self.arhivirana = None

        self.transakcije = []

    # Izračunane vrednosti ---------------------------------------------------

    """
    Koliko denarja bi lahko porabili v kuverti od ustvarjenja do danes.
    """
    @property
    def skupna_limita(self):
        razlika = (self.arhivirana or pendulum.now()) - self.nastanek
        return (razlika.months + 1) * self.limita

    """Koliko denarja smo iz kuverte vzeli."""

    def vsi_odhodki(self):
        pass

    """Koliko denarja smo dodali v kuverto poleg namenjenga."""

    @property
    def vsi_dohodki(self):
        pass

    """Koliko denarja, upoštevajoč vse dohodke, prihodke in limito, je v kuverti."""
    @property
    def stanje(self):
        pass

    # Namere -----------------------------------------------------------------

    """
    Arhivira kuverto a obdrži vse izdatke.
    """

    def arhiviraj(self):
        self.arhivirana = pendulum.now()


class Transakcija:
    """
    Predstavlja prihodek ali odhodek.
    """

    def __init__(self, opis: str, kolicina: int):
        self.opis = opis
        self.kolicina = kolicina
        self.datum = pendulum.now()

    # Izračunane vrednosti ---------------------------------------------------

    """Pove ali je transakcija prihodek."""
    @property
    def je_dohodek(self):
        return self.kolicina >= 0

    """Pove ali je transakcija odhodek."""
    @property
    def je_odhodek(self):
        return self.kolicina < 0


class PonavljajocaTransakcija(Transakcija):
    """
    Ustvari transakcijo, ki se ponavlja vsak mesec.
    """

    def __init__(self, opis: str, kolicina: int):
        super().__init__(opis, kolicina)
        self.konec = None

    # Izračunane vrednosti ---------------------------------------------------

    """Preimenujemo datum iz Transakcije v zacetek."""
    @property
    def zacetek(self):
        return self.datum

    """
    Izračuna skupno kolicino transakcije do zdaj oziroma do prenehanja transakcije.
    Skupna količina je količina pomnožena s številom mesecev med začetkom in koncem.
    """
    @property
    def skupna_kolicina(self):
        razlika = (self.konec or pendulum.now()) - self.zacetek
        return self.kolicina * (razlika.months + 1)

    # Namere -----------------------------------------------------------------

    """Zaključi ponavljajočo transakcijo."""

    def koncaj(self):
        self.konec = pendulum.now()
