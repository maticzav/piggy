import json
from typing import Dict, List, Literal, TypedDict, Optional, TYPE_CHECKING
import enum

import pendulum

if TYPE_CHECKING:
    from pendulum import DateTime, Period
    from model.racun import Racun
    from model.kuverta import Kuverta


class VrstaTransakcije(str, enum.Enum):
    PRIHODEK = "prihodek"
    ODHODEK = "odhodek"


class Transakcija:
    """
    Predstavlja prihodek ali odhodek.
    """

    def __init__(
        self,
        id: int,
        opis: str,
        znesek: int,
        racun: 'Racun',
        datum: 'DateTime'
    ):
        self.id: int = id
        self.opis: str = opis
        self.znesek: int = znesek
        self.datum: 'DateTime' = datum
        self.racun: 'Racun' = racun

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def je_prihodek(self) -> bool:
        """Pove ali je transakcija prihodek."""
        return self.kind == VrstaTransakcije.PRIHODEK

    @property
    def je_odhodek(self) -> bool:
        """Pove ali je transakcija odhodek."""
        return self.kind == VrstaTransakcije.ODHODEK

    @property
    def kind(self) -> 'VrstaTransakcije':
        """Vrne vrsto transakcije."""
        raise NotImplementedError("Transakcija nima vrste.")

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

    def __init__(
        self,
        id: int,
        opis: str,
        znesek: int,
        racun: 'Racun',
        datum: 'DateTime',
        kuverta: Optional['Kuverta'] = None,
        je_investicija: bool = False
    ):
        # Preverimo vrednosti
        assert kuverta is None or not je_investicija, "Odhodek gre ali iz kuverte ali investicij."
        assert znesek >= 0, "Količino je treba podati kot nenegativno vrednost."

        super().__init__(
            id=id,
            opis=opis,
            znesek=-znesek,
            racun=racun,
            datum=datum
        )
        self.kuverta: Optional['Kuverta'] = kuverta
        self.je_investicija: bool = je_investicija

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def kind(self) -> 'VrstaTransakcije':
        return VrstaTransakcije.ODHODEK

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

    def __init__(
        self,
        id: int,
        opis: str,
        znesek: int,
        racun: 'Racun',
        datum: 'DateTime',
        razpored_po_kuvertah: Dict['Kuverta', int] = dict()
    ):
        # Preverimo podatke
        assert znesek >= 0, "Prihodek mora bit pozitiven."

        super().__init__(
            id=id,
            opis=opis,
            znesek=znesek,
            racun=racun,
            datum=datum
        )
        self.razpored_po_kuvertah = razpored_po_kuvertah

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def kind(self) -> 'VrstaTransakcije':
        return VrstaTransakcije.PRIHODEK

    @property
    def je_mesecni(self) -> bool:
        """To ni mesečni prihodek."""
        return False

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

    @property
    def je_mesecni(self) -> bool:
        """Pove ali je prihodek mesečni prihodek."""
        return isinstance(self, MesecniPrihodek)


class MesecniPrihodek(Prihodek):
    """
    Predstavlja prihodek, ki se ponavlja mesečno.
    """

    def __init__(
        self,
        id: int,
        opis: str,
        znesek: int,
        racun: 'Racun',
        datum: 'DateTime',
        konec: Optional['DateTime'] = None,
        razpored_po_kuvertah: Dict['Kuverta', int] = dict()
    ):
        super().__init__(
            id=id,
            opis=opis,
            znesek=znesek,
            racun=racun,
            razpored_po_kuvertah=razpored_po_kuvertah,
            datum=datum
        )
        self._konec: Optional['DateTime'] = konec

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def je_mesecni(self) -> bool:
        """To je mesečni prihodek."""
        return True

    @property
    def zacetek(self) -> 'DateTime':
        """Preimenujemo datum iz Transakcije v zacetek."""
        return self.datum

    @property
    def konec(self) -> 'DateTime':
        """Vrne datum zaprtja oziroma zdajšnji datum, če se prihodek še ni zaključil."""
        return self._konec or pendulum.now()

    @property
    def odprt_mescev(self) -> int:
        """Vrne koliko časa je ta prihodek že aktiven."""
        casovna_razlika: 'Period' = self.konec - self.zacetek
        return casovna_razlika.months + 1

    @property
    def investicija(self) -> int:
        """Vrne skupno investicijo čez več mescev."""
        return super().investicija * self.odprt_mescev

    @property
    def nerazporejeno(self) -> int:
        """Pove koliko denarja nismo razporedili."""
        return super().nerazporejeno * self.odprt_mescev

    def namenjeno_v_kuverto(self, kuverta: 'Kuverta') -> int:
        """Pove koliko denarja smo namenili v kuverto do sedaj."""
        return super().namenjeno_v_kuverto(kuverta) * self.odprt_mescev

    # Namere -----------------------------------------------------------------

    def zakljuci(self) -> None:
        """Zaključi mesečni prihodek."""
        self._konec = pendulum.now()
