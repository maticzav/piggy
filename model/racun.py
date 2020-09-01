import json
from typing import Dict, List, Literal, TypedDict, TYPE_CHECKING

import pendulum

if TYPE_CHECKING:
    from pendulum import DateTime

from model.kuverta import Kuverta, MesecniOdhodek, BarvaKuverte, IkonaKuverte
from model.transakcija import Transakcija, Odhodek, Prihodek, MesecniPrihodek


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
        self._transakcije: List['Transakcija'] = list()
        self._kuverte: Dict[str, 'Kuverta'] = dict()
        self.arhiviran: bool = False

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def prihodki(self) -> List['Prihodek']:
        """Vrne vse prihodki med transakcijami."""
        return [trans for trans in self._transakcije if trans.je_prihodek]

    @property
    def odhodki(self) -> List['Odhodek']:
        """Vrne vse odhodke med transakcijami."""
        return [trans for trans in self._transakcije if trans.je_odhodek]

    @property
    def transakcije(self) -> List['Transakcija']:
        """Vrne vse transakcije, tudi mesečne "podvojene"."""
        danes = pendulum.now()
        transakcije: List['Transakcija'] = []

        for transakcija in self._transakcije:
            if transakcija.kind == "MesecniPrihodek":
                for mesec in range(0, transakcija.odprt_mescev):
                    transakcije.append(Transakcija(
                        opis=transakcija.opis,
                        znesek=transakcija.znesek,
                        racun=self,
                        datum=transakcija.datum.add(months=mesec)
                    ))
            else:
                transakcije.append(transakcija)

        transakcije.sort(key=lambda trans: -trans.datum.float_timestamp)

        return transakcije

    @property
    def porabljeno_od_investicij(self) -> int:
        """Vsota, ki smo jo namenili za investicije."""
        vsota: int = 0
        for transakcija in self._transakcije:
            if transakcija.je_odhodek and transakcija.je_investicija:
                vsota -= transakcija.znesek
        return vsota

    @property
    def namenjeno_za_investiranje(self) -> int:
        """Ves denar, ki smo ga našparali z davkom."""
        vsota: int = 0
        for transakcija in self._transakcije:
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
        for transakcija in self._transakcije:
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

    # JSON -------------------------------------------------------------------

    @property
    def stanje(self):
        """Ustvari predstavitev racuna in vseh pomembnih podrazredov s slovarjem."""
        return {
            'ime': self.ime,
            'davek': self.davek,
            'kuverte': self.stanje_kuvert,
            'transakcije': self.stanje_transakcij,
            'arhiviran': self.arhiviran
        }

    @property
    def stanje_transakcij(self):
        """Vrne stanje transakcij v slovarni obliki."""
        return [{
            # Kuverte so lahko ali navadne kuverte ali mesečni odhodki.
            'kind': transakcija.kind,
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
        } for transakcija in self._transakcije]

    @property
    def stanje_kuvert(self):
        """Vrne stanje kuvert na računu v slovarni obliki."""
        return [{
            'kind': type(kuverta).__name__,
            'hash': hash(kuverta),
            'ime': kuverta.ime,
            'barva': kuverta.barva,
            'ikona': kuverta.ikona,
            'znesek': kuverta.znesek if isinstance(kuverta, MesecniOdhodek) else None
        } for kuverta in self.kuverte]

    # Namere -----------------------------------------------------------------

    def ustvari_mesecni_prihodek(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'MesecniPrihodek':
        """Začne nov ponavljajoči prihodek."""
        trans = MesecniPrihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self._transakcije.append(trans)
        return trans

    def ustvari_prihodek(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'Prihodek':
        """Ustvari enkratni prihodek."""
        trans = Prihodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )
        self._transakcije.append(trans)
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

    def ustvari_odhodek(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now(), kuverta: 'Kuverta' = None) -> 'Odhodek':
        """Ustvari enkraten odhodek na računu ali v kuverti."""
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            datum=datum,
            racun=self,
            kuverta=kuverta
        )
        self._transakcije.append(trans)
        return trans

    def ustvari_investicijo(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now()) -> 'Odhodek':
        """Ustvari novo investicijo."""
        trans = Odhodek(
            opis=opis,
            znesek=znesek,
            racun=self,
            je_investicija=True,
            datum=datum
        )
        self._transakcije.append(trans)
        return trans

    def ustvari_kuverto(self, ime: str, barva: 'BarvaKuverte' = BarvaKuverte.MODRA, ikona: 'IkonaKuverte' = IkonaKuverte.KUVERTA) -> 'Kuverta':
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
                    racun.ustvari_odhodek(
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
