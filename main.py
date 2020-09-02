import hashlib
import os
import random

from typing import Dict, List, TYPE_CHECKING

import appdirs  # type:ignore
import bottle  # type:ignore
import pendulum

from model.uporabnik import Uporabnik
from model.kuverta import BarvaKuverte, IkonaKuverte
from model.transakcija import MesecniPrihodek, Odhodek, Prihodek

if TYPE_CHECKING:
    from model.transakcija import Transakcija, VrstaTransakcije

# Config ---------------------------------------------------------------------

ime_aplikacije = "Piggy"
avtor_aplikacije = "maticzavadlal"
# Verzije aplikacije pomagjo pri možnih spremembah oblike modela.
# Verzije naj bodo urejene od zadnje proti prvi različici aplikacije.
verzije_aplikacije = [
    "0.0.0"
]
trenutna_verzija_aplikacije = verzije_aplikacije[0]

skrivnost = os.getenv("SECRET", "skrivnost")
data_dir = appdirs.user_data_dir(
    ime_aplikacije,
    avtor_aplikacije,
    trenutna_verzija_aplikacije
)
import_dir = os.path.join(os.getcwd(), "import")


SESSION_COOKIE = "Authorization"

# Seje -----------------------------------------------------------------------

uporabniki: Dict[str, 'Uporabnik'] = {}

# Wrappers and Extensions


class Uporabnik(Uporabnik):

    # Razširjeno -------------------------------------------------------------

    def shrani(self) -> None:
        """Shrani stanje uporabnika."""
        self.izvozi_v_datoteko(os.path.join(data_dir, f"{self.email}.json"))

    @classmethod
    def uporabniske_datoteke_v(cls, path) -> List[str]:
        """Vrne seznam datotek, ki vsebujejo podatke o uporabnikih znotraj dane poti."""
        return [dat for dat in os.listdir(path) if dat.endswith(".json")]


def auth(fn):
    """Zavije funkcijo in vstavi uporabnika kot spremenljivko `gledalec` ("viewer")."""

    def wrapper(*a, **ka):
        email = bottle.request.get_cookie(
            SESSION_COOKIE, secret=skrivnost)
        vhodna_stran = bottle.request.path

        if email is None or email not in uporabniki:
            # Izbriši sejo
            bottle.response.delete_cookie(SESSION_COOKIE, path='/')
            bottle.redirect(f"/prijava?redirect={vhodna_stran}")
        gledalec = uporabniki[email]

        return fn(*a, **ka, gledalec=gledalec)
    return wrapper

# Static files ---------------------------------------------------------------


@bottle.get("/static/<path:path>")
def files(path):
    return bottle.static_file(path, root="public/")

# Spletni vmesnik ------------------------------------------------------------


@bottle.get("/")
@bottle.view("index.html")
@auth
def domov(gledalec: 'Uporabnik'):
    error = bottle.request.query.getunicode("error", None)

    return {
        "racuni": gledalec.racuni.values(),
        "error": error
    }


@bottle.get("/ustvari_racun")
@bottle.view("ustvari_racun.html")
@auth
def ustvari_racun(gledalec: 'Uporabnik'):
    return


@bottle.get("/racun/<ime>")
@bottle.view("racun.html")
@auth
def racun(ime: str, gledalec: 'Uporabnik'):
    sorting = bottle.request.query.getunicode("sort", "date")
    racun = gledalec.racuni.get(ime)

    if racun is None:
        return bottle.HTTPError(404)

    # Sortiraj
    transakcije = racun.transakcije
    if sorting == "description":
        transakcije.sort(key=lambda t: t.opis)
    elif sorting == "amount":
        transakcije.sort(key=lambda t: -t.znesek)
    elif sorting == "kind":
        transakcije.sort(key=lambda t: t.znesek)
    elif sorting == "envelope":
        transakcije.sort(key=lambda t: t.kuverta.ime)
    else:
        transakcije.sort(key=lambda t: t.datum, reverse=True)

    return {
        "racun": racun,
        "kuverte": racun.kuverte,
        "transakcije": transakcije,
        "sorting": sorting
    }


@bottle.get("/racun/<ime>/transakcija/<id:int>")
@bottle.view("transakcija.html")
@auth
def racun(ime: str, id: int, gledalec: 'Uporabnik'):
    racun = gledalec.racuni.get(ime)

    if racun is None:
        return bottle.HTTPError(404)

    transakcija = racun._transakcije[id]

    if transakcija is None:
        return bottle.HTTPError(404)

    return {
        "racun": racun,
        "kuverte": racun.kuverte,
        "transakcija": transakcija,
        "today": pendulum.now()
    }


@bottle.get("/racun/<ime>/ustvari_kuverto")
@bottle.view("ustvari_kuverto.html")
@auth
def ustvari_kuverto(ime: str, gledalec: 'Uporabnik'):
    racun = gledalec.racuni.get(ime)

    if racun is None:
        return bottle.HTTPError(404)

    return {
        "racun": racun,
        "kuverte": racun.kuverte,
        "barve": BarvaKuverte.values(),
        "ikone": IkonaKuverte.values()
    }


@bottle.get("/racun/<ime_racuna>/kuverta/<ime_kuverte>")
@bottle.view("kuverta.html")
@auth
def ustvari_kuverto(ime_racuna: str, ime_kuverte: str, gledalec: 'Uporabnik'):
    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        return bottle.HTTPError(404)

    kuverta = racun.kuverta.get(ime_kuverte)

    if kuverta is None:
        return bottle.HTTPError(404)

    return {
        "racun": racun,
        "kuverta": kuverta,
        "transakcije": kuverta.transakcije
    }


@bottle.get("/racun/<ime_racuna>/ustvari_transakcijo")
@bottle.view("ustvari_transakcijo.html")
@auth
def ustvari_transakcijo(ime_racuna: str, gledalec: 'Uporabnik'):
    error = bottle.request.query.getunicode("error", None)
    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        bottle.redirect("/")
        return

    return {
        "racun": racun,
        "kuverte": racun.kuverte,
        "error": error
    }


# Errors


@bottle.error(404)
def error404(error):
    return bottle.template("error.html")

# API


@bottle.post('/api/racun')
@auth
def ustvari_racun(gledalec: 'Uporabnik'):
    try:
        ime = bottle.request.forms.getunicode("ime")
        davek = int(bottle.request.forms.getunicode("davek"))

        racun = gledalec.ustvari_racun(ime, davek / 100)
        gledalec.shrani()

        bottle.redirect(f"/racun/{racun.ime}")
    except:
        bottle.redirect(f"/?error=Nekaj je šlo narobe.")


@bottle.post('/api/racun/<ime_racuna>/kuverta')
@auth
def ustvari_kuverto(ime_racuna: str, gledalec: 'Uporabnik'):
    ime = bottle.request.forms.getunicode("ime")
    barva = bottle.request.forms.getunicode("barva")
    ikona = bottle.request.forms.getunicode("ikona")

    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        return bottle.HTTPError(404)

    racun.ustvari_kuverto(ime, barva, ikona)
    gledalec.shrani()

    bottle.redirect(f"/racun/{racun.ime}")


@bottle.post("/api/racun/<ime_racuna>/transakcija/<vrsta_transakcije:re:(investicija)|(prihodek)|(odhodek)>")
@auth
def ustvari_transakcijo(ime_racuna: str, vrsta_transakcije: 'VrstaTransakcije', gledalec: 'Uporabnik'):
    opis = bottle.request.forms.getunicode("opis")
    znesek = int(bottle.request.forms.getunicode("znesek")) * 100

    # Try parsing the date.
    try:
        datum = pendulum.from_format(
            bottle.request.forms.getunicode("datum"), "DD-MM-YYYY")
    except:
        datum = pendulum.now()

    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        return bottle.HTTPError(404)

    if vrsta_transakcije == "investicija":
        racun.ustvari_investicijo(opis, znesek, datum)
    elif vrsta_transakcije == "prihodek":
        mesecni_prihodek = bool(
            bottle.request.forms.getunicode("mesecni_prihodek"))
        # Najdi kuverte
        razpored_po_kuvertah = {}
        for kljuc in bottle.request.forms.keys():
            if kljuc.startswith("kuverta_"):
                ime_kuverte = kljuc.replace("kuverta_", "")
                kuverta = racun.kuverta.get(ime_kuverte)

                if kuverta is None:
                    return bottle.HTTPError(400)

                namenjeno = bottle.request.forms.getunicode(kljuc)
                if namenjeno != "":
                    razpored_po_kuvertah[kuverta] = float(namenjeno) * 100

        # Preveri računico
        davek: float = racun.davek * znesek
        razporjeno_v_kuverte: int = sum(razpored_po_kuvertah.values())

        if znesek - davek - razporjeno_v_kuverte < 0:
            bottle.redirect(
                f"/racun/{ime_racuna}/ustvari_transakcijo?error=Napačen razpored.")
            return

        # Ustvari prihodek
        if mesecni_prihodek:
            racun.ustvari_mesecni_prihodek(
                opis=opis,
                znesek=znesek,
                datum=datum,
                razpored_po_kuvertah=razpored_po_kuvertah
            )
        else:
            racun.ustvari_prihodek(
                opis=opis,
                znesek=znesek,
                datum=datum,
                razpored_po_kuvertah=razpored_po_kuvertah
            )
    elif vrsta_transakcije == "odhodek":
        ime_kuverte = bottle.request.forms.getunicode("kuverta")
        # Najdi kuverto
        if ime_kuverte == "None":
            kuverta = None
        else:
            kuverta = racun.kuverta.get(ime_kuverte, None)
        # Ustvari odhodek
        racun.ustvari_odhodek(opis, znesek, datum, kuverta)

    gledalec.shrani()

    bottle.redirect(f"/racun/{racun.ime}")


@bottle.post("/api/racun/<ime_racuna>/transakcija/<id:int>")
@auth
def uredi_transakcijo(ime_racuna: str, id: int, gledalec: 'Uporabnik'):
    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        return bottle.HTTPError(404)

    transakcija = racun._transakcije[id]

    if transakcija is None:
        return bottle.HTTPError(404)

    # Uredi transakcijo
    # Opis
    opis = bottle.request.forms.getunicode("opis")
    # Datum
    try:
        datum = pendulum.from_format(
            bottle.request.forms.getunicode("datum"), "DD-MM-YYYY")
    except:
        datum = transakcija.datum

    transakcija.opis = opis
    transakcija.datum = datum

    # Odhodek
    if transakcija.je_odhodek:
        # Kuverta
        ime_kuverte = bottle.request.forms.getunicode("kuverta")
        if ime_kuverte == "None":
            kuverta = None
        else:
            kuverta = racun.kuverta.get(ime_kuverte, None)
        transakcija.kuverta = kuverta

    # Prihodek
    if transakcija.je_prihodek:
        # Razpored po kuvertah
        razpored_po_kuvertah = {}
        for kljuc in bottle.request.forms.keys():
            if kljuc.startswith("kuverta_"):
                ime_kuverte = kljuc.replace("kuverta_", "")
                kuverta = racun.kuverta.get(ime_kuverte)

                if kuverta is None:
                    return bottle.HTTPError(400)

                namenjeno = bottle.request.forms.getunicode(kljuc)
                if namenjeno != "":
                    razpored_po_kuvertah[kuverta] = float(namenjeno) * 100
        transakcija.razpored_po_kuvertah = razpored_po_kuvertah
        # Konec
        try:
            konec = pendulum.from_format(
                bottle.request.forms.getunicode("konec"), "DD-MM-YYYY")
        except:
            konec = None
        transakcija._konec = konec

    # Preveri računico
    davek: float = racun.davek * transakcija.znesek
    razporjeno_v_kuverte: int = sum(razpored_po_kuvertah.values())

    if transakcija.znesek - davek - razporjeno_v_kuverte < 0:
        bottle.redirect(
            f"/racun/{ime_racuna}/ustvari_transakcijo?error=Napačen razpored.")
        return

    racun._transakcije[id]
    gledalec.shrani()

    bottle.redirect(f"/racun/{ime_racuna}")


# Authorizacija


@bottle.get("/prijava")
@bottle.view("prijava.html")
def prijava_get():
    error = bottle.request.query.getunicode("error", None)
    redirect = bottle.request.query.getunicode("redirect", "/")

    return {
        "redirect": redirect,
        "error": error
    }


@bottle.post("/prijava")
def prijava_post():
    # Form data
    email = bottle.request.forms.getunicode('email')
    geslo = bottle.request.forms.getunicode('geslo')
    redirect = bottle.request.forms.getunicode('redirect')

    h = hashlib.blake2b()
    h.update(geslo.encode(encoding='utf-8'))
    zasifrirano_geslo = h.hexdigest()

    try:
        if email not in uporabniki:
            uporabnik = Uporabnik(email, zasifrirano_geslo)
            uporabniki[email] = uporabnik
            uporabnik.shrani()
        else:
            uporabnik = uporabniki[email]
            uporabnik.preveri_geslo(zasifrirano_geslo)

        # Ustvari sejo
        bottle.response.set_cookie(
            SESSION_COOKIE, uporabnik.email, path='/', secret=skrivnost)

        bottle.redirect('/')
    except ValueError as error:
        bottle.redirect(f"/prijava?redirect={redirect}&error={error}")
    else:
        bottle.redirect(
            f'/vpis?redirect={redirect}&error=Nekaj je šlo narobe.')


@bottle.get('/odjava')
@auth
def odjava(gledalec: 'Uporabnik'):
    gledalec.shrani()
    bottle.response.delete_cookie(SESSION_COOKIE, path='/')
    bottle.redirect('/')


# Zaženi ---------------------------------------------------------------------

if __name__ == '__main__':
    # Izpiše podatke
    print("# --------------------------------------")
    print(f"Datoteke uvozim iz: {import_dir}")
    print(f"Mapa aplikacije: {data_dir}")
    print(f"Verzija: ${trenutna_verzija_aplikacije}")
    print("# --------------------------------------")

    # Ustvari mapo s podatki aplikacije, če ta še ne obstaja.
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Naloži uporabnike v aplikacijo.
    for ime_datoteke in Uporabnik.uporabniske_datoteke_v(data_dir):
        datoteka = os.path.join(data_dir, ime_datoteke)
        uporabnik = Uporabnik.uvozi_iz_datoteke(datoteka)
        uporabniki[uporabnik.email] = uporabnik

    # Importaj podatke
    if os.path.exists(import_dir):
        for ime_datoteke in Uporabnik.uporabniske_datoteke_v(import_dir):
            # Naloži podatke
            datoteka = os.path.join(import_dir, ime_datoteke)
            uporabnik = Uporabnik.uvozi_iz_datoteke(datoteka)
            uporabniki[uporabnik.email] = uporabnik
            # Shrani v aplikacijo
            uporabnik.shrani()

    # Zaženi spletni vmesnik.
    bottle.run(debug=True, reloader=True)
