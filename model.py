from typing import Dict, List
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
    """

    def __init__(self, ime: str, davek: float):
        # Preveri vrednosti
        assert (davek >= 0 and davek <= 1), "Davek mora predstavljat odstotek."

        self.ime: str = ime
        self.davek: float = davek
        self.transakcije: List['Transakcija'] = list()
        self.kuverte: List['Kuverta'] = list()
        self.arhiviran: bool = False

        self.__transakcije_po: Dict[str, 'Transakcija'] = dict()

    # Izračunane vrednosti ---------------------------------------------------

    # """Vsi prihodki do dne."""
    # @property
    # def vsi_prihodki(self):
    #     vsota = 0
    #     for transakcija in self.ponavljajoce_transakcije:
    #         if transakcija.je_dohodek:
    #             vsota += transakcija.skupna_kolicina
    #     for transakcija in self.transakcije:
    #         if transakcija.je_dohodek:
    #             vsota += transakcija.kolicina
    #     return vsota

    # """Vsi odhodki do dne, kot pozitivna vsota."""
    # @property
    # def vsi_odhodki(self):
    #     vsota = 0
    #     for transakcija in self.ponavljajoce_transakcije:
    #         if transakcija.je_odhodek:
    #             vsota -= transakcija.skupna_kolicina
    #     for transakcija in self.transakcije:
    #         if transakcija.je_odhodek:
    #             vsota -= transakcija.kolicina
    #     return vsota

    """Ves denar, ki smo ga našparali z davkom."""
    @property
    def nasparano(self):
        return sum([prihodek.investicija for prihodek in self.transakcije if prihodek.je_prihodek])

    """Denar, ki ni šel v šparovec in ga nismo porabili v kuvertah."""

    @property
    def ostalo(self):
        pass

    @property
    def porabljen_denar_v_kuvertah(self):
        return sum([kuverta.stanje for kuverta in self.kuverte])

    # Namere -----------------------------------------------------------------

    """Začne nov ponavljajoči prihodek."""

    def ustvari_mesecni_prihodek(self, opis: str, kolicina: int, razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'MesecniPrihodek':
        trans = MesecniPrihodek(
            opis=opis,
            kolicina=kolicina,
            racun=self,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari enkratni prihodek."""

    def ustvari_prihodek(self, opis: str, kolicina: int, razpored_po_kuvertah: Dict['Kuverta', int] = {}):
        trans = Prihodek(
            opis=opis,
            kolicina=kolicina,
            razred=self,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    """Zaključi ponavljajočo transakcijo."""

    def koncaj_ponavljajoco_transakcijo(self, id):
        pass

    """Ustvari novo kuverto."""

    def ustvari_kuverto(self, opis: str, barva: str, ikona: str):
        pass

    """Arhivira račun tako, da arhivira use ponavljajoče transakcije in kuverte."""

    def arhiviraj(self):
        pass

# ----------------------------------------------------------------------------


class Transakcija:
    """
    Predstavlja prihodek ali odhodek.
    """

    def __init__(self, opis: str, kolicina: int, racun: Racun):
        self.opis: str = opis
        self.kolicina: int = kolicina
        self.datum: pendulum.DateTime = pendulum.now()
        self.racun: Racun = racun

    # Izračunane vrednosti ---------------------------------------------------

    """Pove ali je transakcija prihodek."""
    @property
    def je_prihodek(self):
        return self.kolicina >= 0

    """Pove ali je transakcija odhodek."""
    @property
    def je_odhodek(self):
        return self.kolicina < 0

    # """Vrne vrednost transakcije."""
    # @property
    # def vrednost(self):
    #     return self.kolicina


class Odhodek(Transakcija):
    """
    Odhodek je enkraten znesek, ki ga lahko vzamemo iz investicij,
    posamezne kuverte ali iz ostalega denarja.
    """

    def __init__(self, opis: str, kolicina: int, racun: Racun, kuverta=None, investicija=False):
        # Preverimo vrednosti
        assert (
            kuverta != None and investicija), "Odhodek gre ali iz kuverte ali investicij."
        assert kolicina >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            opis=opis,
            kolicina=kolicina,
            racun=racun
        )
        self.kuverta = kuverta
        self.investicija = investicija


class MesecniOdhodek(Transakcija):
    """
    Ustvari transakcijo, ki se ponavlja vsak mesec.
    """

    def __init__(self, opis: str, kolicina: int, racun: Racun):
        # Preveri vrednosti
        assert kolicina >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            opis=opis,
            kolicina=-kolicina,
            racun=racun
        )
        self.__konec = None

    # Izračunane vrednosti ---------------------------------------------------

    """Preimenujemo datum iz Transakcije v zacetek."""
    @property
    def zacetek(self):
        return self.datum

    @property
    def konec(self):
        return self.__konec or pendulum.now()

    """
    Izračuna skupno kolicino transakcije do zdaj oziroma do prenehanja transakcije.
    Skupna količina je količina pomnožena s številom mesecev med začetkom in koncem.
    """
    @property
    def vsota(self):
        casovna_razlika = self.konec - self.zacetek
        return self.kolicina * (casovna_razlika.months + 1)

    # Namere -----------------------------------------------------------------

    """Zaključi ponavljajočo transakcijo."""

    def zakljuci(self):
        self.__konec = pendulum.now()


class Prihodek(Transakcija):
    """
    Predstavlja enkratni prihodek, ki ga razdelimo med kuverte.
    """

    def __init__(self, opis: str, kolicina: int, racun: 'Racun', razpored_po_kuvertah: Dict['Kuverta', int] = {None: None}):
        # Preverimo podatke
        assert kolicina >= 0, "Prihodek mora bit pozitiven."

        super().__init__(opis=opis, kolicina=kolicina, racun=racun)
        self.razpored_po_kuvertah = razpored_po_kuvertah

    # Izračunane vrednosti ---------------------------------------------------

    """Vrne koliko denarja od prihodka smo dali v investicije."""

    @property
    def investicija(self) -> int:
        return int(self.kolicina * self.racun.davek)

    """Pove koliko denarja nismo razporedili."""
    @property
    def nerazporejeno(self) -> int:
        return self.kolicina - sum(self.razpored_po_kuvertah.values()) - self.investicija


class MesecniPrihodek(Prihodek):
    """
    Predstavlja prihodek, ki se ponavlja mesečno.
    """

    def __init__(self, opis: str, kolicina: int, racun: Racun, razpored_po_kuvertah={None: None}):
        super().__init__(
            opis=opis,
            kolicina=kolicina,
            racun=racun,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.__konec = None

    # Izračunane vrednosti ---------------------------------------------------

    """Preimenujemo datum iz Transakcije v zacetek."""
    @property
    def zacetek(self):
        return self.datum

    """Vrne datum zaprtja oziroma zdajšnji datum, če se prihodek še ni zaključil."""

    @property
    def konec(self):
        return self.__konec or pendulum.now()

    """Vrne skupno investicijo čez več mescev."""

    @property
    def investicija(self):
        casovna_razlika = self.konec - self.zacetek
        return super().investicija * (casovna_razlika.months + 1)

    """Pove koliko denarja nismo razporedili."""
    @property
    def nerazporejeno(self):
        casovna_razlika = self.konec - self.zacetek
        return super().nerazporejeno * (casovna_razlika.months + 1)

    # Namere -----------------------------------------------------------------

    """Zaključi mesečni prihodek."""

    def zakljuci(self):
        self.__konec = pendulum.now()


# ----------------------------------------------------------------------------


class Kuverta:
    """
    Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    barva in ikona pa pomagata pri ustvarjanju vizualne razlike.

    V kuverto dodajamo denar iz mesečnih prihodkov in začasnih prihodkov.
    Edina limita porabe v kuverti je prazna kuverta.
    """

    def __init__(self, ime: str, barva: str = "modra", ikona: str = "kuverta"):
        self.ime = ime
        self.barva = barva
        self.ikona = ikona
        # self.transakcije = []
