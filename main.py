import hashlib
import os
import random

import appdirs
import bottle
import pendulum

from model import Kuverta, Racun, Uporabnik, VrstaTransakcije

# Config ---------------------------------------------------------------------

ime_aplikacije = "Piggy"
avtor_aplikacije = "maticzavadlal"
verzije_aplikacije = [
    "0.0.0"
]

skrivnost = os.getenv("SECRET", "skrivnost")
data_dir = appdirs.user_data_dir(
    ime_aplikacije, avtor_aplikacije, verzije_aplikacije[-1])


SESSION_COOKIE = "Authorization"

# Seje -----------------------------------------------------------------------

uporabniki = {}

# Wrappers and Extensions


class Uporabnik(Uporabnik):

    # Razširjeno -------------------------------------------------------------

    def shrani(self):
        """Shrani stanje uporabnika."""
        self.izvozi_v_datoteko(os.path.join(data_dir, f"{self.email}.json"))


def auth(fn):
    """Zavije funkcijo in vstavi uporabnika kot spremenljivko `gledalec` ("viewer")."""

    def wrapper(*a, **ka):
        email = bottle.request.get_cookie(
            SESSION_COOKIE, secret=skrivnost)
        vhodna_stran = bottle.request.path

        if email is None:
            bottle.redirect(f"/prijava?redirect={vhodna_stran}")
        gledalec = uporabniki[email]

        return fn(*a, **ka, gledalec=gledalec)
    return wrapper

# Static files ---------------------------------------------------------------


@bottle.get("/static/<path:path>")
def files(path):
    return bottle.static_file(path, root="public/")

# Spletni vmesnik ------------------------------------------------------------

# TODO: Back button!!!


@bottle.get("/")
@bottle.view("index.html")
@auth
def domov(gledalec: 'Uporabnik'):
    return {
        "racuni": gledalec.racuni.values()
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
    racun = gledalec.racuni.get(ime)

    if racun is None:
        return bottle.HTTPError(404)

    return {
        "racun": racun,
        "kuverte": racun.kuverte,
        "transakcije": racun.transakcije
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
        "barve": Kuverta.razpolozljive_barve,
        "ikone": Kuverta.razpolozljive_ikone
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
    racun = gledalec.racuni.get(ime_racuna)
    if racun is None:
        return bottle.HTTPError(404)

    return {
        "racun": racun,
    }


# Errors


@bottle.error(404)
def error404(error):
    return bottle.template("error.html")

# API


@bottle.post('/api/racun')
@auth
def ustvari_racun(gledalec: 'Uporabnik'):
    ime = bottle.request.forms.getunicode("ime")
    davek = int(bottle.request.forms.getunicode("davek"))

    racun = gledalec.ustvari_racun(ime, davek / 100)
    gledalec.shrani()

    bottle.redirect(f"/racun/{racun.ime}")


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
    datum = pendulum.now()

    racun = gledalec.racuni.get(ime_racuna)

    if racun is None:
        return bottle.HTTPError(404)

    if vrsta_transakcije == "investicija":
        racun.ustvari_investicijo(opis, znesek, datum)
    elif vrsta_transakcije == "prihodek":
        # Najdi kuverte
        razpored_po_kuvertah = {}
        for kljuc in bottle.request.forms.keys():
            if kljuc.startswith("kuverta"):
                ime_kuverte = kljuc.replace("kuverta", "")
                kuverta = racun.kuverta.get(ime_kuverte)

                if kuverta is None:
                    return bottle.HTTPError(400)
                razpored_po_kuvertah[kuverta] = int(
                    bottle.request.forms.getunicode(kljuc))
        # Ustvari prihodek
        racun.ustvari_prihodek(opis, znesek, datum, razpored_po_kuvertah)
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

# Authorizacija


@bottle.get("/prijava")
@bottle.view("prijava.html")
def prijava_get():
    redirect = bottle.request.query.getunicode("redirect", "/")
    return {"redirect": redirect}


@bottle.post("/prijava")
def prijava_post():
    # Form data
    email = bottle.request.forms.getunicode('email')
    geslo = bottle.request.forms.getunicode('geslo')
    redirect = bottle.request.forms.getunicode('redirect')

    h = hashlib.blake2b()
    h.update(geslo.encode(encoding='utf-8'))
    zasifrirano_geslo = h.hexdigest()

    if email not in uporabniki:
        uporabnik = Uporabnik(email, zasifrirano_geslo)
        uporabniki[email] = uporabnik
        uporabnik.shrani()
    else:
        uporabnik = uporabniki[email]
        # TODO: povej, da je napačno geslo.
        uporabnik.preveri_geslo(zasifrirano_geslo)

    # Ustvari sejo
    bottle.response.set_cookie(
        SESSION_COOKIE, uporabnik.email, path='/', secret=skrivnost)

    bottle.redirect('/')


@bottle.get('/odjava')
def odjava():
    bottle.response.delete_cookie(SESSION_COOKIE, path='/')
    bottle.redirect('/')


# Zaženi ---------------------------------------------------------------------

if __name__ == '__main__':
    # Ustvari mapo s podatki aplikacije, če ta še ne obstaja.
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Naloži uporabnike v aplikacijo.
    for ime_datoteke in os.listdir(data_dir):
        uporabnik = Uporabnik.uvozi_iz_datoteke(
            os.path.join(data_dir, ime_datoteke))
        uporabniki[uporabnik.email] = uporabnik

    # Zaženi spletni vmesnik.
    bottle.run(debug=True, reloader=True)
