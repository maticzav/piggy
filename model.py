import json
from typing import Dict, List, TypedDict, Literal

import pendulum

"""
POMEMBNO:

Nekaj pomembnejših napotkov:
    1. količina je predstavljena s celimi števili v centih (1€ = 100).
"""

# ----------------------------------------------------------------------------


class Uporabnik:
    """Predstavlja posameznega uporabnika in njegov račun."""

    def __init__(self, email: str, geslo: str):
        self.email: str = email
        self.geslo: str = geslo
        self.racuni: Dict[str, 'Racun'] = {}

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def stanje(self):
        """Slovarni prikaz uporabnika."""
        return {
            'email': self.email,
            'geslo': self.geslo,
            'racuni': [{
                'ime': racun.ime,
                'racun': racun.stanje
            } for racun in self.racuni.values()]
        }

    # Namere -----------------------------------------------------------------

    def pravilno_geslo(self, geslo: str) -> bool:
        """Pove ali je geslo pravilno."""
        return self.geslo == geslo

    def preveri_geslo(self, geslo: str):
        """Preveri ali je geslo pravilno."""
        if self.geslo != geslo:
            raise ValueError('Geslo je napačno!')

    def ustvari_racun(self, ime: str, davek: float) -> 'Racun':
        """Ustvari nov račun."""
        racun = Racun(ime, davek)
        return self.dodaj_racun(racun)

    def dodaj_racun(self, racun: 'Racun') -> 'Racun':
        """Dodaj račun."""
        self.racuni[racun.ime] = racun
        return racun

    def arhiviraj_racun(self, ime: str) -> 'Racun':
        """Arhivira račun."""
        return self.racuni[ime].arhiviraj()

    def izvozi_v_datoteko(self, ime_datoteke: str):
        """Shrani stanje v datateko."""
        with open(ime_datoteke, 'w') as datoteka:
            json.dump(self.stanje, datoteka, ensure_ascii=False, indent=2)

    # Metode -----------------------------------------------------------------

    @classmethod
    def uvozi_iz_json(cls, json):
        """Ustvari razred Uporabnik iz json reprezentacije uporabnika."""
        email = json['email']
        geslo = json['geslo']

        # Sestavi uporabnika
        uporabnik = cls(email, geslo)
        for racun in json["racuni"]:
            uporabnik.dodaj_racun(Racun.uvozi_iz_json(racun["racun"]))

        return uporabnik

    @classmethod
    def uvozi_iz_datoteke(cls, ime_datoteke: str):
        """Naloži stanje iz datoteke."""
        with open(ime_datoteke) as datoteka:
            stanje = json.load(datoteka)
            return cls.uvozi_iz_json(stanje)


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
        self._kuverte: Dict[str, 'Kuverta'] = dict()
        self.arhiviran: bool = False

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def prihodki(self) -> List['Prihodek']:
        """Vrne vse prihodki med transakcijami."""
        return [trans for trans in self.transakcije if trans.je_prihodek]

    @property
    def odhodki(self) -> List['Odhodek']:
        """Vrne vse odhodke med transakcijami."""
        return [trans for trans in self.transakcije if trans.je_odhodek]

    @property
    def porabljeno_od_investicij(self) -> int:
        """Vsota, ki smo jo namenili za investicije."""
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_investicija:
                vsota -= transakcija.znesek
        return vsota

    @property
    def namenjeno_za_investiranje(self) -> int:
        """Ves denar, ki smo ga našparali z davkom."""
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_prihodek:
                vsota += transakcija.investicija
        return vsota

    @property
    def razpolozljivo_za_investicije(self) -> int:
        """Denar, ki ga še lahko investiramo."""
        return self.namenjeno_za_investiranje - self.porabljeno_od_investicij

    @property
    def nerazporejeno_namenjeno(self) -> int:
        """Denar, ki ni šel v investicije in ga nismo dali v kuverte."""
        return sum([prihodek.nerazporejeno for prihodek in self.prihodki])

    @property
    def nerazporejeno_porabljeno(self) -> int:
        """Nerazporejen denar, ki smo ga že porabili."""
        vsota: int = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_nerazporejen:
                vsota -= transakcija.znesek
        return vsota

    @property
    def nerazporejeno_razpolozljivo(self) -> int:
        """Nerazporejen denar, ki smo ga že porabili."""
        return self.nerazporejeno_namenjeno - self.nerazporejeno_porabljeno

    @property
    def namenjeno_za_kuverte(self) -> int:
        """Pove koliko denarja je bilo razporejenega v kuverte."""
        return sum([kuverta.namenjeno for kuverta in self.kuverte])

    @property
    def kuverte(self) -> List['Kuverta']:
        """Vrne kuverte iz računa."""
        return self._kuverte.values()

    @property
    def kuverta(self) -> Dict[str, 'Kuverta']:
        """Vrne slovar kuvert po imenih."""
        return self._kuverte

    @property
    def stanje(self):
        """Ustvari predstavitev racuna in vseh pomembnih podrazredov s slovarjem."""
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
            } for kuverta in self.kuverte],
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

    def ustvari_mesecni_prihodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'MesecniPrihodek':
        """Začne nov ponavljajoči prihodek."""
        trans = MesecniPrihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    def ustvari_prihodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'Prihodek':
        """Ustvari enkratni prihodek."""
        trans = Prihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self.transakcije.append(trans)
        return trans

    def ustvari_mesecni_odhodek(self, opis: str, znesek: int) -> 'MesecniOdhodek':
        """Začne nov mesečni odhodek."""
        kuverta = MesecniOdhodek(
            opis=opis,
            znesek=znesek,
            racun=self
        )
        self._kuverte[kuverta.ime] = kuverta
        return kuverta

    def ustvari_odhodek(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        """Ustvari enkraten odhodek na računu."""
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            datum=datum,
            racun=self
        )
        self.transakcije.append(trans)
        return trans

    def ustvari_investicijo(self, opis: str, znesek: int, datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        """Ustvari novo investicijo."""
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            je_investicija=True,
            datum=datum
        )
        self.transakcije.append(trans)
        return trans

    def ustvari_odhodek_iz_kuverte(self, opis: str, znesek: int, kuverta: 'Kuverta', datum: pendulum.DateTime = pendulum.now()) -> 'Odhodek':
        """Ustvari nov odhodek v določeni kuverti."""
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            kuverta=kuverta
        )
        self.transakcije.append(trans)
        return trans

    def ustvari_kuverto(self, ime: str, barva: str = "modra", ikona: str = "kuverta") -> 'Kuverta':
        """Ustvari novo kuverto."""
        kuverta = Kuverta(
            ime=ime,
            barva=barva,
            ikona=ikona,
            racun=self
        )
        self._kuverte[kuverta.ime] = kuverta
        return kuverta

    def arhiviraj(self):
        """Arhivira račun tako, da arhivira use ponavljajoče transakcije in kuverte."""
        # Zaključi ponavljajoče prihodke.
        for prihodek in self.prihodki:
            if isinstance(prihodek, MesecniPrihodek):
                prihodek.zakljuci()

        self.arhiviran = True
        return self

    def izvozi_v_datoteko(self, ime_datoteke: str):
        """Ustvari datoteko s trenutnim stanjem računa."""
        with open(ime_datoteke, 'w') as datoteka:
            json.dump(self.stanje, datoteka,
                      ensure_ascii=False, indent=2)

    # Metode -----------------------------------------------------------------

    @classmethod
    def uvozi_iz_json(cls, json):
        """Ustvari nov objekt Racun in vse potrebne podobjekte iz JSON."""
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

    @classmethod
    def uvozi_iz_datoteke(cls, ime_datoteke):
        """Uvozi Racun iz JSON datoteke."""
        with open(ime_datoteke) as datoteka:
            stanje = json.load(datoteka)
        return cls.uvozi_iz_json(stanje)


# ----------------------------------------------------------------------------

BarvaKuverte = Literal["modra", "rdeca", "zelena", "rumena", "siva"]
IkonaKuverte = Literal["kuverta", "avto", "morje", "banka"]


class Kuverta:
    """
    Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    barva in ikona pa pomagata pri ustvarjanju vizualne razlike.

    V kuverto dodajamo denar iz mesečnih prihodkov in začasnih prihodkov.
    Edina limita porabe v kuverti je prazna kuverta.
    """

    razpolozljive_barve = ["modra", "rdeca", "zelena", "rumena", "siva"]
    razpolozljive_ikone = ["kuverta", "avto", "morje", "banka"]

    def __init__(self, ime: str, racun: Racun, barva: BarvaKuverte, ikona: IkonaKuverte):
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

    @property
    def namenjeno(self) -> int:
        """Pove koliko denarja je bilo namenjenega za kuverto."""
        vsota: int = 0
        for trans in self.racun.transakcije:
            if trans.je_prihodek:
                vsota += trans.namenjeno_v_kuverto(self)
        return vsota

    @property
    def porabljeno(self) -> int:
        """Vrne koliko denarja smo porabili iz kuverte."""
        vsota: int = 0
        for trans in self.racun.transakcije:
            if trans.je_odhodek and trans.je_kuverten and trans.kuverta == self:
                vsota -= trans.znesek
        return vsota

    @property
    def razpolozljivo(self) -> int:
        """Vrne koliko denarja je še v kuverti."""
        return self.namenjeno - self.porabljeno

    @property
    def prihodki(self) -> List['Prihodek']:
        """Vrne seznam vseh prihodkov, ki smo jih dali v to kuverto."""
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

    @property
    def razpolozljivo(self) -> int:
        """Mesečni odhodek je zmeraj plačan v celoti."""
        return 0

    @property
    def placano(self) -> bool:
        """Pove ali smo namenili dovolj denarja za odhodek."""
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

    @property
    def je_prihodek(self):
        """Pove ali je transakcija prihodek."""
        return self.znesek >= 0

    @property
    def je_odhodek(self):
        """Pove ali je transakcija odhodek."""
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

    @property
    def je_kuverten(self) -> bool:
        """Pove ali je odhodek iz kuverte."""
        return self.kuverta is not None

    @property
    def je_nerazporejen(self) -> bool:
        """Pove ali je odhodek splošen."""
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

    @property
    def investicija(self) -> int:
        """Vrne koliko denarja od prihodka smo dali v investicije."""
        return int(self.znesek * self.racun.davek)

    @property
    def nerazporejeno(self) -> int:
        """Pove koliko denarja nismo razporedili."""
        return self.znesek - sum(self.razpored_po_kuvertah.values()) - self.investicija

    def namenjeno_v_kuverto(self, kuverta: 'Kuverta') -> int:
        """Pove koliko denarja v transakciji je bilo namenjenega v dano kuverto."""
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

    @property
    def zacetek(self):
        """Preimenujemo datum iz Transakcije v zacetek."""
        return self.datum

    @property
    def konec(self):
        """Vrne datum zaprtja oziroma zdajšnji datum, če se prihodek še ni zaključil."""
        return self.__konec or pendulum.now()

    @property
    def odprt_mescev(self):
        """Vrne koliko časa je ta prihodek že aktiven."""
        casovna_razlika = self.konec - self.zacetek
        return casovna_razlika.months + 1

    @property
    def investicija(self):
        """Vrne skupno investicijo čez več mescev."""
        return super().investicija * self.odprt_mescev

    @property
    def nerazporejeno(self):
        """Pove koliko denarja nismo razporedili."""
        return super().nerazporejeno * self.odprt_mescev

    def namenjeno_v_kuverto(self, kuverta: 'Kuverta') -> int:
        """Pove koliko denarja smo namenili v kuverto do sedaj."""
        return super().namenjeno_v_kuverto(kuverta) * self.odprt_mescev

    # Namere -----------------------------------------------------------------

    def zakljuci(self):
        """Zaključi mesečni prihodek."""
        self.__konec = pendulum.now()
