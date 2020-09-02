import json
from typing import Dict, List, Literal, TypedDict, TYPE_CHECKING, Optional

import pendulum

if TYPE_CHECKING:
    from pendulum import DateTime

from model.kuverta import BarvaKuverte, IkonaKuverte, Kuverta, MesecniOdhodek
from model.transakcija import VrstaTransakcije, Transakcija, Odhodek, Prihodek, MesecniPrihodek


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
        self._transakcije: Dict[int, 'Transakcija'] = dict()
        self._kuverte: Dict[str, 'Kuverta'] = dict()
        self.arhiviran: bool = False

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def transakcije(self) -> List['Transakcija']:
        """Vrne vse transakcije, tudi mesečne "podvojene"."""
        danes = pendulum.now()
        transakcije: List['Transakcija'] = []

        for transakcija in self._transakcije.values():
            if isinstance(transakcija, MesecniPrihodek):
                for mesec in range(0, transakcija.odprt_mescev):
                    transakcije.append(Prihodek(
                        id=transakcija.id,
                        opis=transakcija.opis,
                        znesek=transakcija.znesek,
                        racun=self,
                        datum=transakcija.datum.add(months=mesec),
                        razpored_po_kuvertah=transakcija.razpored_po_kuvertah,
                    ))
            else:
                transakcije.append(transakcija)

        transakcije.sort(key=lambda trans: -trans.datum.float_timestamp)

        return transakcije

    @property
    def prihodki(self) -> List['Prihodek']:
        """Vrne vse prihodke med transakcijami."""
        return [trans for trans in self._transakcije.values() if trans.je_prihodek]

    @property
    def odhodki(self) -> List['Odhodek']:
        """Vrne vse odhodke med transakcijami."""
        return [trans for trans in self._transakcije.values() if trans.je_odhodek]

    @property
    def porabljeno_od_investicij(self) -> float:
        """Vsota, ki smo jo namenili za investicije."""
        vsota: float = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_investicija:
                vsota -= transakcija.znesek
        return vsota

    @property
    def namenjeno_za_investiranje(self) -> float:
        """Ves denar, ki smo ga našparali z davkom."""
        vsota: float = 0
        for transakcija in self.transakcije:
            if transakcija.je_prihodek:
                vsota += transakcija.investicija
        return vsota

    @property
    def razpolozljivo_za_investicije(self) -> float:
        """Denar, ki ga še lahko investiramo."""
        return self.namenjeno_za_investiranje - self.porabljeno_od_investicij

    @property
    def nerazporejeno_namenjeno(self) -> float:
        """Denar, ki ni šel v investicije in ga nismo dali v kuverte."""
        return sum([tran.nerazporejeno for tran in self.transakcije if tran.je_prihodek])

    @property
    def nerazporejeno_porabljeno(self) -> float:
        """Nerazporejen denar, ki smo ga že porabili."""
        vsota: float = 0
        for transakcija in self.transakcije:
            if transakcija.je_odhodek and transakcija.je_nerazporejen:
                vsota -= transakcija.znesek
        return vsota

    @property
    def nerazporejeno_razpolozljivo(self) -> float:
        """Nerazporejen denar, ki smo ga že porabili."""
        return self.nerazporejeno_namenjeno - self.nerazporejeno_porabljeno

    @property
    def namenjeno_za_kuverte(self) -> float:
        """Pove koliko denarja je bilo razporejenega v kuverte."""
        return sum([kuverta.namenjeno for kuverta in self.kuverte])

    @property
    def porabljeno_od_kuvert(self) -> float:
        """Pove koliko denarja, ki smo ga dali v kuverte smo že porabili."""
        return sum([kuverta.porabljeno for kuverta in self.kuverte])

    @property
    def razpolozljivo_od_kuvert(self) -> float:
        return self.namenjeno_za_kuverte - self.porabljeno_od_kuvert

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
        transakcije = []

        for id, transakcija in self._transakcije.items():
            # Razpored po kuvertah
            razpored_po_kuvertah = [{
                'hash': hash(kuverta),
                'znesek': znesek
            } for (kuverta, znesek) in transakcija.razpored_po_kuvertah.items()] if isinstance(transakcija, Prihodek) else dict()
            # Kuverta
            kuverta = hash(transakcija.kuverta) if isinstance(
                transakcija, Odhodek) and transakcija.kuverta is not None else None
            # Konec
            konec = transakcija._konec.to_iso8601_string(
            ) if transakcija.je_prihodek and transakcija.je_mesecni and transakcija._konec else None

            transakcije.append({
                'id': id,
                # Kuverte so lahko ali navadne kuverte ali mesečni odhodki.
                'kind': transakcija.kind,
                'opis': transakcija.opis,
                'znesek': abs(transakcija.znesek),
                'datum': transakcija.datum.to_iso8601_string(),
                # Predstavitev odhodka.
                'kuverta': kuverta,
                'je_investicija': transakcija.je_investicija if isinstance(transakcija, Odhodek) else None,
                # Predstavitev prihodka.
                'je_mesecni_prihodek': transakcija.je_prihodek and transakcija.je_mesecni,
                'razpored_po_kuvertah': razpored_po_kuvertah,
                # Predstavitev ponavljajočega prihodka.
                'konec': konec
            })

        return transakcije

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

    def id_nove_transakcije(self):
        """Vrne ID, ki ga naj uporabimo za naslednjo transakcijo."""
        ids = list(self._transakcije.keys())
        ids.append(0)
        return max(ids) + 1

    def ustvari_mesecni_prihodek(
            self,
            opis: str,
            znesek: int,
            datum: 'DateTime' = pendulum.now(),
            razpored_po_kuvertah: Dict['Kuverta', int] = {},
    ) -> 'MesecniPrihodek':
        """Začne nov ponavljajoči prihodek."""
        id = self.id_nove_transakcije()

        trans = MesecniPrihodek(
            id=id,
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )

        self._transakcije[id] = trans

        return trans

    def ustvari_prihodek(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now(), razpored_po_kuvertah: Dict['Kuverta', int] = {}) -> 'Prihodek':
        """Ustvari enkratni prihodek."""
        id = self.id_nove_transakcije()

        trans = Prihodek(
            id=id,
            opis=opis,
            znesek=znesek,
            racun=self,
            datum=datum,
            razpored_po_kuvertah=razpored_po_kuvertah
        )

        self._transakcije[id] = trans

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
        id = self.id_nove_transakcije()

        trans = Odhodek(
            id=id,
            opis=opis,
            znesek=znesek,
            datum=datum,
            racun=self,
            kuverta=kuverta
        )

        self._transakcije[id] = trans

        return trans

    def ustvari_investicijo(self, opis: str, znesek: int, datum: 'DateTime' = pendulum.now()) -> 'Odhodek':
        """Ustvari novo investicijo."""
        id = self.id_nove_transakcije()

        trans = Odhodek(
            id=id,
            opis=opis,
            znesek=znesek,
            racun=self,
            je_investicija=True,
            datum=datum
        )

        self._transakcije[id] = trans

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
            id = j_trans["id"]

            # Odhodek
            if j_trans["kind"] == VrstaTransakcije.ODHODEK:
                kuverta = kuverte_po_hashih[j_trans["kuverta"]
                                            ] if j_trans["kuverta"] else None
                trans = Odhodek(
                    id=id,
                    opis=j_trans["opis"],
                    znesek=j_trans["znesek"],
                    datum=pendulum.parse(j_trans["datum"]),
                    racun=racun,
                    kuverta=kuverta,
                    je_investicija=j_trans.get("je_investicija", False)
                )

            # Prihodek
            if j_trans["kind"] == VrstaTransakcije.PRIHODEK:
                # Sestavi razpored po kuvertah
                razpored: Dict['Kuverta', int] = dict()
                for rel in j_trans["razpored_po_kuvertah"]:
                    razpored[kuverte_po_hashih[rel["hash"]]] = rel["znesek"]

                # Ustvari transakcije.
                if j_trans["je_mesecni_prihodek"]:
                    trans = MesecniPrihodek(
                        id=id,
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        racun=racun,
                        datum=pendulum.parse(j_trans["datum"]),
                        konec=pendulum.parse(
                            j_trans["konec"]) if j_trans["konec"] else None,
                        razpored_po_kuvertah=razpored
                    )
                else:
                    trans = Prihodek(
                        id=id,
                        opis=j_trans["opis"],
                        znesek=j_trans["znesek"],
                        racun=racun,
                        datum=pendulum.parse(j_trans["datum"]),
                        razpored_po_kuvertah=razpored,
                    )

            # Dodaj v zbir id-jev.
            racun._transakcije[id] = trans
        return racun

    @classmethod
    def uvozi_iz_datoteke(cls, ime_datoteke):
        """Uvozi Racun iz JSON datoteke."""
        with open(ime_datoteke) as datoteka:
            stanje = json.load(datoteka)
        return cls.uvozi_iz_json(stanje)
