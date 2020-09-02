import json
from typing import Dict, List, TypedDict, Literal

from model.racun import Racun


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
        stanje = self.stanje  # če se zgodi napaka ne zbriše datoteke
        with open(ime_datoteke, 'w') as datoteka:
            json.dump(stanje, datoteka, ensure_ascii=False, indent=2)

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
