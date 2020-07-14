from typing import Dict, List
import pendulum
import json

"""
POMEMBNO:

Nekaj pomembnejših napotkov:
    1. količina je predstavljena s celimi števili v centih (1€ = 100).

TODO: MesecniOdhodek bo bolje predstavljen kot še ena kuverta s posebnimi metodami.
"""

# ----------------------------------------------------------------------------


class Racun:
    """
    Račun predstavlja en račun posameznega uporabnika z danim davkom.
    Davka po ustvarjenju računa ni mogoče spremenit.
    """

    def __init__(self, ime: str, davek: float):
        # Preveri vrednosti
        assert davek >= 0 and davek <= 1, "Davek mora predstavljat odstotek."

        self.ime: str = ime
        self.davek: float = davek
        self.transakcije: List['Transakcija'] = list()
        self.kuverte: Dict[str, 'Kuverta'] = dict()
        self.arhiviran: bool = False

        self.__transakcije_po: Dict[str, 'Transakcija'] = dict()

    # Izračunane vrednosti ---------------------------------------------------

    """Vrne vse prihodki med transakcijami."""

    @property
    def prihodki(self) -> List['Prihodek']:
        return [trans for trans in self.transakcije if trans.je_prihodek]

    """Vrne vse odhodke med transakcijami."""

    @property
    def odhodki(self) -> List['Odhodek']:
        return [trans for trans in self.transakcije if trans.je_odhodek]

    """Ves denar, ki smo ga našparali z davkom."""
    @property
    def stanje_investicij(self) -> int:
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_prihodek:
                vsota += transakcija.investicija
            if transakcija.je_odhodek and transakcija.je_investicija:
                vsota += transakcija.znesek
        return vsota

    """Denar, ki ni šel v investicije in ga nismo dali v kuverte."""

    @property
    def stanje_nerazporejeno(self) -> int:
        for transakcija in self.transakcije:
            pass
        return 0

    # Namere -----------------------------------------------------------------

    """Začne nov ponavljajoči prihodek."""

    def ustvari_mesecni_prihodek(self, opis: str, znesek: int, razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'MesecniPrihodek':
        trans = MesecniPrihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari enkratni prihodek."""

    def ustvari_prihodek(self, opis: str, znesek: int, razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'Prihodek':
        trans = Prihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    """Začne nov mesečni odhodek."""

    def ustvari_mesecni_odhodek(self, opis: str, znesek: int) -> 'MesecniOdhodek':
        kuverta = MesecniOdhodek(
            opis=opis,
            znesek=znesek,
            racun=self
        )
        self.kuverte[hash(kuverta)] = kuverta
        return kuverta

    """Ustvari enkraten odhodek na računu."""

    def ustvari_odhodek(self, opis: str, znesek: int) -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari novo investicijo."""

    def ustvari_investicijo(self, opis: str, znesek: int) -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            je_investicija=True
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari nov odhodek v določeni kuverti."""

    def ustvari_odhodek_iz_kuverte(self, opis: str, znesek: int, kuverta: 'Kuverta') -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            kuverta=kuverta
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari novo kuverto."""

    def ustvari_kuverto(self, ime: str, barva: str = "modra", ikona: str = "kuverta") -> 'Kuverta':
        kuverta = Kuverta(
            ime=ime,
            barva=barva,
            ikona=ikona,
            racun=self
        )
        self.kuverte[hash(kuverta)] = kuverta
        return kuverta

    """Arhivira račun tako, da arhivira use ponavljajoče transakcije in kuverte."""

    def arhiviraj(self):
        pass


# ----------------------------------------------------------------------------


class Kuverta:
    """
    Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    barva in ikona pa pomagata pri ustvarjanju vizualne razlike.

    V kuverto dodajamo denar iz mesečnih prihodkov in začasnih prihodkov.
    Edina limita porabe v kuverti je prazna kuverta.

    Barve:
        - modra
        - rdeca
        - zelena
        - rumena
        - siva
    Ikone:
        - kuverta
        - avto
        - morje
        - banka
    """

    razpolozljive_barve = ["modra", "rdeca", "zelena", "rumena", "siva"]
    razpolozljive_ikone = ["kuverta", "avto", "morje", "banka"]

    def __init__(self, ime: str, racun: Racun, barva: str, ikona: str):
        # Preveri vrednosti
        assert barva in Kuverta.razpolozljive_barve, "Neznana barva."
        assert ikona in Kuverta.razpolozljive_ikone, "Neznana ikona."

        self.ime: str = ime
        self.barva: str = barva
        self.ikona: str = ikona
        self.racun: 'Racun' = racun

    def __eq__(self, druga: 'Kuverta') -> bool:
        return self.ime == druga.ime

    def __hash__(self) -> int:
        return hash(self.ime)

    # Izračunane vrednosti ---------------------------------------------------

    """Vrne koliko denarja je še v kuverti."""

    @property
    def razpolozljivo(self) -> int:
        vsota: int = 0
        for trans in self.racun.transakcije:
            if trans.je_prihodek:
                vsota += trans.namenjeno_v_kuverto(self)
            if trans.je_odhodek and False:
                pass
        return vsota

    """Vrne seznam vseh prihodkov, ki smo jih dali v to kuverto."""

    @property
    def prihodki(self) -> List['Prihodek']:
        return [prihodek for prihodek in self.racun.prihodki if prihodek.namenjeno_v_kuverto(self) > 0]


class MesecniOdhodek(Kuverta):
    """
    Ustvari novo kuverto za stalen mesecni odhodek.
    """

    def __init__(self, opis: str, znesek: int, racun: Racun):
        # Preveri vrednosti
        assert znesek >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            ime=opis,
            barva="siva",
            ikona="banka",
            racun=racun,
        )
        self.znesek = znesek

    # Izračunane vrednosti ---------------------------------------------------

    """Mesečni odhodek je zmeraj plačan v celoti."""
    @property
    def razpolozljivo(self) -> int:
        return 0

    """Pove ali smo namenili dovolj denarja za odhodek."""

    @property
    def placano(self) -> bool:
        return super().razpolozljivo >= self.znesek


# ----------------------------------------------------------------------------


class Transakcija:
    """
    Predstavlja prihodek ali odhodek.
    """

    def __init__(self, opis: str, znesek: int, racun: Racun):
        self.opis: str = opis
        self.znesek: int = znesek
        self.datum: pendulum.DateTime = pendulum.now()
        self.racun: Racun = racun

    # Izračunane vrednosti ---------------------------------------------------

    """Pove ali je transakcija prihodek."""
    @property
    def je_prihodek(self):
        return self.znesek >= 0

    """Pove ali je transakcija odhodek."""
    @property
    def je_odhodek(self):
        return self.znesek < 0

    # """Vrne vrednost transakcije."""
    # @property
    # def vrednost(self):
    #     return self.znesek


class Odhodek(Transakcija):
    """
    Odhodek je enkraten znesek, ki ga lahko vzamemo iz investicij,
    posamezne kuverte ali iz ostalega denarja.

    Če kuverta ni definirana in odhodek ni označen za investicijo
    predvidevamo da je splošen odhodek.
    """

    def __init__(self, opis: str, znesek: int, racun: Racun, kuverta=None, je_investicija=False):
        # Preverimo vrednosti
        assert kuverta is None or not je_investicija, "Odhodek gre ali iz kuverte ali investicij."
        assert znesek >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            opis=opis,
            znesek=-znesek,
            racun=racun
        )
        self.kuverta: 'Kuverta' = kuverta
        self.je_investicija: bool = je_investicija

    # Izračunane vrednosti ---------------------------------------------------

    """Pove ali je odhodek iz kuverte."""
    @property
    def je_kuverten(self) -> bool:
        return self.kuverta != None

    """Pove ali je odhodek splošen."""
    @property
    def je_splosen(self) -> bool:
        return not self.je_kuverten and not self.je_investicija


class Prihodek(Transakcija):
    """
    Predstavlja enkratni prihodek, ki ga razdelimo med kuverte.
    """

    def __init__(self, opis: str, znesek: int, racun: 'Racun', razpored_po_kuvertah: Dict['Kuverta', int] = {None: None}):
        # Preverimo podatke
        assert znesek >= 0, "Prihodek mora bit pozitiven."

        super().__init__(opis=opis, znesek=znesek, racun=racun)
        self.razpored_po_kuvertah = razpored_po_kuvertah

    # Izračunane vrednosti ---------------------------------------------------

    """Vrne koliko denarja od prihodka smo dali v investicije."""

    @property
    def investicija(self) -> int:
        return int(self.znesek * self.racun.davek)

    """Pove koliko denarja nismo razporedili."""
    @property
    def nerazporejeno(self) -> int:
        return self.znesek - sum(self.razpored_po_kuvertah.values()) - self.investicija

    """Pove koliko denarja v transakciji je bilo namenjenega v dano kuverto."""

    def namenjeno_v_kuverto(self, kuverta: 'Kuverta') -> int:
        return self.razpored_po_kuvertah.get(kuverta, 0)


class MesecniPrihodek(Prihodek):
    """
    Predstavlja prihodek, ki se ponavlja mesečno.
    """

    def __init__(self, opis: str, znesek: int, racun: Racun, razpored_po_kuvertah={None: None}):
        super().__init__(
            opis=opis,
            znesek=znesek,
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

    """Vrne koliko časa je ta prihodek že aktiven."""
    @property
    def odprt_mescev(self):
        casovna_razlika = self.konec - self.zacetek
        return casovna_razlika.months + 1

    """Vrne skupno investicijo čez več mescev."""

    @property
    def investicija(self):
        return super().investicija * self.odprt_mescev

    """Pove koliko denarja nismo razporedili."""
    @property
    def nerazporejeno(self):
        return super().nerazporejeno * self.odprt_mescev

    """Pove koliko denarja smo namenili v kuverto do sedaj."""

    def namenjeno_v_kuverto(self, kuverta: 'Kuverta') -> int:
        return super().namenjeno_v_kuverto(kuverta) * self.odprt_mescev

    # Namere -----------------------------------------------------------------

    """Zaključi mesečni prihodek."""

    def zakljuci(self):
        self.__konec = pendulum.now()
