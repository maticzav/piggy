from typing import Dict, List, TypedDict, Literal, Any, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from model.racun import Racun


class BarvaKuverte(enum.Enum):
    MODRA = "modra"
    RDECA = "rdeca"
    ZELENA = "zelena"
    RUMENA = "rumena"
    SIVE = "siva"


class IkonaKuverte(enum.Enum):
    KUVERTA = "kuverta"
    AVTO = "avto"
    MORJE = "morje"
    BANKA = "banka"


class Kuverta:
    """
    Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    barva in ikona pa pomagata pri ustvarjanju vizualne razlike.

    V kuverto dodajamo denar iz mesečnih prihodkov in začasnih prihodkov.
    Edina limita porabe v kuverti je prazna kuverta.
    """

    razpolozljive_barve = [barva.value for barva in BarvaKuverte]
    razpolozljive_ikone = [ikona.value for ikona in IkonaKuverte]

    def __init__(self, ime: str, racun: 'Racun', barva: 'BarvaKuverte', ikona: 'IkonaKuverte'):
        # Preveri vrednosti
        assert barva in Kuverta.razpolozljive_barve, "Neznana barva."
        assert ikona in Kuverta.razpolozljive_ikone, "Neznana ikona."

        self.ime: str = ime
        self.barva: 'BarvaKuverte' = barva
        self.ikona: 'IkonaKuverte' = ikona
        self.racun: 'Racun' = racun

    def __eq__(self, druga: Any) -> bool:
        return type(druga) == self.__name__ and self.ime == druga.ime

    def __hash__(self) -> int:
        return hash(self.ime)

    def __str__(self) -> str:
        return f"{self.barva.value.capitalize()} kuverta z ikono {self.ikona}"

    def __repr__(self) -> str:
        return f"Kuverta({self.ime}, barva={self.barva}, ikona={self.ikona})"

    # Izračunane vrednosti ---------------------------------------------------

    @property
    def namenjeno(self) -> int:
        """Pove koliko denarja je bilo namenjenega za kuverto."""
        vsota: int = 0
        for trans in self.racun._transakcije:
            if trans.je_prihodek:
                vsota += trans.namenjeno_v_kuverto(self)
        return vsota

    @property
    def porabljeno(self) -> int:
        """Vrne koliko denarja smo porabili iz kuverte."""
        vsota: int = 0
        for trans in self.transakcije:
            if trans.je_odhodek:
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

    @property
    def transakcije(self) -> List['Transakcija']:
        """Vrne seznam transakcij v tej kuverti."""
        for transakcija in self.racun.transakcije:
            if transakcija.kind == "Odhodek" and transakcija.je_kuverten and transakcija.kuverta == self:
                yield transakcija


# ----------------------------------------------------------------------------

class MesecniOdhodek(Kuverta):
    """
    Ustvari novo kuverto za stalen mesecni odhodek.
    """

    def __init__(self, opis: str, znesek: int, racun: 'Racun'):
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
