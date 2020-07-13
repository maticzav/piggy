from pendulum import

'''
POMEMBNO: 

Nekaj pomembnejših napotkov:
    1. količina je predstavljena s celimi števili v centih.
'''

# ----------------------------------------------------------------------------


class Racun:
    '''
    Ime računa naj bo lahko zapomnljivo ime, davek pa število med 0 in 1, 
    ki predstavlja kolikšni delež od vsakega zaslužka gre v "šparovec".
    '''

    def __init__(self, ime: str, davek: float):
        self.ime = ime  # str
        self.davek = davek  # float
        self.kuverte = []  # [Kuverta]
        self.prihodki = []  # [PonavljajocaTransakcija]

    '''
    Izračuna preostali denar, ki ni bil razporejen med kuverte,
    na dan podan z datumom.
    '''
    @property
    def razpolozljiv_denar_dne(self, datum=datetime.now()):
        kolicina = 0

        # Prištej prihodke
        for prihodek in self.prihodki:
            if prihodek.datum < datum:
                kolicina += prihodek.kolicina

        # Odštej odhodke.
        for kuverta in self.kuverte:
            kuverta.

    '''Začne nov ponavljajoči prihodek.'''

    def dodaj_ponavljajoc_prihodek(self, opis: str, kolicina: int, zacetek=datetime.now()):
        prihodek = PonavljajocaTransakcija(
            opis=opis, kolicina=kolicina, zacetek=zacetek)
        self.prihodki.append(prihodek)
        return prihodek


class Transakcija:


class PonavljajocaTransakcija:
    '''
    Ustvari transakcijo, ki se ponavlja vsak mesec.
    Pozitivne količine predstavljajo prihodek, negativne količine pa izdatek.
    '''

    def __init__(self, opis: str, kolicina: float, zacetek=datetime.now()):
        self.opis = opis
        self.kolicina = kolicina
        self.zacetek = zacetek
        self.konec = None

    '''Izračuna doprinos transakcije do dne.'''
    def doprinos_do_dne(datum=datetime.now()):
        konec = min(datum, self.konec or datum)
        delta

    '''Zaključi ponavljajočo transakcijo'''

    def koncaj(self):
        self.konec = datetime.now()


class Prihodek:
    # Ustvari novo transakcijo z danim opisom.
    def __init__(self, opis: str, kolicina: int, datum: datetime = datetime.now()):
        self.opis = opis
        self.kolicina = kolicina
        self.datum = datum


class Izdatek


class Kuverta:
    # Ustvari novo kuverto. Ime kuverte pomaga uporabniku najti kuverto,
    #   barva in ikona pa pomagata pri ustvarjanju vizualne razlike.
    #   Limita je količina denarja, ki ga lahko porabimo iz posamezne kuverte.
    def __init__(self, ime: str, barva="modra", ikona="kuverta", limita: float):
        self.ime = ime
        self.limita = limita
        self.barva = barva
        self.ikona = ikona
        self.izdatki = []
