import json
from typing import Dict, List, TypedDict

import pendulum

"""
POMEMBNO:

Nekaj pomembnejših napotkov:
    1. količina je predstavljena s celimi števili v centih (1€ = 100).
"""

# ----------------------------------------------------------------------------

# """Slovarna predstavitev računa"""


# class IRacun(TypedDict):
#     ime: str
#     davek: str
#     """Najprej je treba naložit kuverte in mesečne odhodke, šele potem transakcije."""
#     kuverte: Dict[str, 'IKuverta']
#     mesecni_odhodki: Dict[str, 'IMesecniOdhodek']
#     arhiviran: bool


# class ITransakcija(TypedDict):
#     pass


# class IMesecniOdhodek(TypedDict):
#     pass


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

    # Izračunane vrednosti ---------------------------------------------------

    """Vrne vse prihodki med transakcijami."""

    @property
    def prihodki(self) -> List['Prihodek']:
        return [trans for trans in self.transakcije if trans.je_prihodek]

    """Vrne vse odhodke med transakcijami."""

    @property
    def odhodki(self) -> List['Odhodek']:
        return [trans for trans in self.transakcije if trans.je_odhodek]

    """Vsota, ki smo jo namenili za investicije."""
    @property
    def porabljeno_od_investicij(self) -> int:
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_investicija:
                vsota -= transakcija.znesek
        return vsota

    """Ves denar, ki smo ga našparali z davkom."""
    @property
    def namenjeno_za_investiranje(self) -> int:
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_prihodek:
                vsota += transakcija.investicija
        return vsota

    """Denar, ki ga še lahko investiramo."""
    @property
    def razpolozljivo_za_investicije(self) -> int:
        return self.namenjeno_za_investiranje - self.porabljeno_od_investicij

    """Denar, ki ni šel v investicije in ga nismo dali v kuverte."""

    @property
    def nerazporejeno_namenjeno(self) -> int:
        return sum([prihodek.nerazporejeno for prihodek in self.prihodki])

    """Nerazporejen denar, ki smo ga že porabili."""

    @property
    def nerazporejeno_porabljeno(self) -> int:
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_nerazporejen:
                vsota -= transakcija.znesek
        return vsota

    """Nerazporejen denar, ki smo ga že porabili."""

    @property
    def nerazporejeno_razpolozljivo(self) -> int:
        return self.nerazporejeno_namenjeno - self.nerazporejeno_porabljeno

    """Pove koliko denarja je bilo razporejenega v kuverte."""

    @property
    def namenjeno_za_kuverte(self) -> int:
        return sum([kuverta.namenjeno for kuverta in self.kuverte.values()])

    """Ustvari predstavitev racuna in vseh pomembnih podrazredov s slovarjem."""

    @property
    def stanje(self):
        return {
            'ime': self.ime,
            'davek': self.davek,
            # Kuverte so lahko ali navadne kuverte ali mesečni odhodki.
            'kuverte': [{
                'kind': type(kuverta).__name__,
                'hash': hash(kuverta),
                'ime': kuverta.ime,
                'barva': kuverta.barva,
                'ikona': kuverta.ikona,
                'znesek': kuverta.znesek if isinstance(kuverta, MesecniOdhodek) else None
            } for kuverta in self.kuverte.values()],
            'transakcije': [{
                'kind': type(transakcija).__name__,
                'opis': transakcija.opis,
                'znesek': abs(transakcija.znesek),
                'datum': transakcija.datum.to_iso8601_string(),
                # Predstavitev odhodka.
                'kuverta': hash(transakcija.kuverta) if isinstance(transakcija, Odhodek) and transakcija.kuverta is not None else None,
                'je_investicija': transakcija.je_investicija if isinstance(transakcija, Odhodek) else None,
                # Predstavitev prihodka.
                'razpored_po_kuvertah': [{
                    'hash': hash(kuverta),
                    'znesek': znesek
                } for (kuverta, znesek) in transakcija.razpored_po_kuvertah.items()] if isinstance(transakcija, Prihodek) else None,
                # Predstavitev ponavljajočega prihodka.
                'konec': transakcija.konec.to_iso8601_string() if isinstance(transakcija, MesecniPrihodek) else None
            } for transakcija in self.transakcije],
            'arhiviran': self.arhiviran
        }

    # Namere -----------------------------------------------------------------

    """Začne nov ponavljajoči prihodek."""

    def ustvari_mesecni_prihodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'MesecniPrihodek':
        trans = MesecniPrihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari enkratni prihodek."""

    def ustvari_prihodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'Prihodek':
        trans = Prihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
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

    def ustvari_odhodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            datum=datum,
            racun=self
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari novo investicijo."""

    def ustvari_investicijo(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            je_investicija=True,
            datum=datum
        )
        self.transakcije.append(trans)
        return trans

    """Ustvari nov odhodek v določeni kuverti."""

    def ustvari_odhodek_iz_kuverte(self, opis: str, znesek: int, kuverta: 'Kuverta', datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
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
        # Zaključi ponavljajoče prihodke.
        for prihodek in self.prihodki:
            if isinstance(prihodek, MesecniPrihodek):
                prihodek.zakljuci()

        self.arhiviran = True
        return self

    """Ustvari datoteko s trenutnim stanjem računa."""

    def izvozi_v_datoteko(self, ime_datoteke: str):
        with open(ime_datoteke, 'w') as datoteka:
            json.dump(self.stanje, datoteka,
                      ensure_ascii=False, indent=2)

    # Metode -----------------------------------------------------------------

    """Ustvari nov objekt Racun in vse potrebne podobjekte iz JSON."""

    @classmethod
    def uvozi_iz_json(cls, json):
        racun = cls(ime=json["ime"], davek=json["davek"])

        # Naloži kuverte
        kuverte_po_hashih = {}
        for j_kuverta in json["kuverte"]:
            if j_kuverta["kind"] == "Kuverta":
                kuverta = racun.ustvari_kuverto(
                    ime=j_kuverta["ime"],
                    barva=j_kuverta["barva"],
                    ikona=j_kuverta["ikona"],
                )
            elif j_kuverta["kind"] == "MesecniOdhodek":
                kuverta = racun.ustvari_mesecni_odhodek(
                    opis=j_kuverta["ime"],
                    znesek=j_kuverta["znesek"]
                )
            kuverte_po_hashih[j_kuverta["hash"]] = kuverta

        # Naloži transakcije
        for j_trans in json["transakcije"]:
            # Odhodek
            if j_trans["kind"] == "Odhodek":
                if j_trans.get("kuverta"):
                    racun.ustvari_odhodek_iz_kuverte(
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        datum=pendulum.parse(j_trans["datum"]),
                        kuverta=kuverte_po_hashih[j_trans["kuverta"]],
                    )
                elif j_trans.get("je_investicija", False):
                    racun.ustvari_investicijo(
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        datum=pendulum.parse(j_trans["datum"]),
                    )
                else:
                    racun.ustvari_odhodek(
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        datum=pendulum.parse(j_trans["datum"]),
                    )
            # Prihodek
            else:
                # Sestavi razpored po kuvertah
                razpored: Dict['Kuverta', int] = {}
                for rel in j_trans["razpored_po_kuvertah"]:
                    razpored[kuverte_po_hashih[rel["hash"]]] = rel["znesek"]

                # Ustvari transakcije.
                if j_trans["kind"] == "Prihodek":
                    racun.ustvari_prihodek(
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        datum=pendulum.parse(j_trans["datum"]),
                        razpored_po_kuvertah=razpored,
                    )
                if j_trans["kind"] == "MesecniPrihodek":
                    racun.ustvari_mesecni_prihodek(
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        datum=pendulum.parse(j_trans["datum"]),
                        razpored_po_kuvertah=razpored
                    )

        return racun

    """Uvozi Racun iz JSON datoteke."""

    @classmethod
    def uvozi_iz_datoteke(cls, ime_datoteke):
        with open(ime_datoteke) as datoteka:
            stanje = json.load(datoteka)
        return cls.uvozi_iz_json(stanje)


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
        return self.ime == druga.ime and self.racun == druga.racun

    def __hash__(self) -> int:
        return hash(self.ime)

    # Izračunane vrednosti ---------------------------------------------------

    """Pove koliko denarja je bilo namenjenega za kuverto."""

    @property
    def namenjeno(self) -> int:
        vsota: int = 0
        for trans in self.racun.transakcije:
            if trans.je_prihodek:
                vsota += trans.namenjeno_v_kuverto(self)
        return vsota

    """Vrne koliko denarja smo porabili iz kuverte."""

    @property
    def porabljeno(self) -> int:
        vsota: int = 0
        for trans in self.racun.transakcije:
            if trans.je_odhodek and trans.je_kuverten and trans.kuverta == self:
                vsota -= trans.znesek
        return vsota

    """Vrne koliko denarja je še v kuverti."""

    @property
    def razpolozljivo(self) -> int:
        return self.namenjeno - self.porabljeno

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

    def __init__(self, opis: str, znesek: int, racun: Racun, datum: pendulum.DateTime):
        self.opis: str = opis
        self.znesek: int = znesek
        self.datum: pendulum.DateTime = datum
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

    def __init__(self, opis: str, znesek: int, racun: Racun, datum: pendulum.DateTime, kuverta=None, je_investicija=False):
        # Preverimo vrednosti
        assert kuverta is None or not je_investicija, "Odhodek gre ali iz kuverte ali investicij."
        assert znesek >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            opis=opis,
            znesek=-znesek,
            racun=racun,
            datum=datum
        )
        self.kuverta: 'Kuverta' = kuverta
        self.je_investicija: bool = je_investicija

    # Izračunane vrednosti ---------------------------------------------------

    """Pove ali je odhodek iz kuverte."""
    @property
    def je_kuverten(self) -> bool:
        return self.kuverta is not None

    """Pove ali je odhodek splošen."""
    @property
    def je_nerazporejen(self) -> bool:
        return not self.je_kuverten and not self.je_investicija


class Prihodek(Transakcija):
    """
    Predstavlja enkratni prihodek, ki ga razdelimo med kuverte.
    """

    def __init__(self, opis: str, znesek: int, racun: 'Racun', datum: pendulum.DateTime, razpored_po_kuvertah: Dict['Kuverta', int] = {None: None}):
        # Preverimo podatke
        assert znesek >= 0, "Prihodek mora bit pozitiven."

        super().__init__(
            opis=opis,
            znesek=znesek,
            racun=racun,
            datum=datum
        )
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

    def __init__(self, opis: str, znesek: int, racun: Racun, datum: pendulum.DateTime, razpored_po_kuvertah={None: None}):
        super().__init__(
            opis=opis,
            znesek=znesek,
            racun=racun,
            razpored_po_kuvertah=razpored_po_kuvertah,
            datum=datum
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
