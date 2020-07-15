import hashlib
import os
import random

import appdirs
import bottle

from model import Racun, Uporabnik

# Config ---------------------------------------------------------------------

ime_aplikacije = "Piggy"
avtor_aplikacije = "maticzavadlal"
verzije_aplikacije = [
    "0.0.0"
]

skrivnost = os.getenv("SECRET", "skrivnost")
data_dir = appdirs.user_data_dir(
    ime_aplikacije, avtor_aplikacije, verzije_aplikacije[-1])

# Ustvari mapo s podatki aplikacije, če ta še ne obstaja.
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Seje -----------------------------------------------------------------------

uporabniki = {}

# Naloži uporabnike v aplikacijo.
for ime_datoteke in os.listdir(data_dir):
    uporabnik = Uporabnik.nalozi_stanje(
        os.path.join(data_dir, ime_datoteke))
    uporabniki[uporabnik.uporabnisko_ime] = uporabnik

SESSION_COOKIE = "Authorization"


def auth(fn):
    """Zavije funkcijo in vstavi uporabnika kot spremenljivko `gledalec` ("viewer")."""

    def wrapper(*a, **ka):
        uporabnisko_ime = bottle.request.get_cookie(
            SESSION_COOKIE, secret=skrivnost)
        vhodna_stran = bottle.request.path

        if uporabnisko_ime is None:
            bottle.redirect(f"/prijava?redirect={vhodna_stran}")
        gledalec = uporabniki[uporabnisko_ime]

        return fn(*a, **ka, gledalec=gledalec)
    return wrapper


# Static files ---------------------------------------------------------------


@bottle.get("/static/<path:path>")
def files(path):
    return bottle.static_file(path, root="public/")

# Spletni vmesnik ------------------------------------------------------------


@bottle.get("/")
@auth
def zacetna_stran(gledalec: 'Uporabnik'):
    return f"Hej {gledalec.uporabnisko_ime}"


@bottle.get("/racun/:ime")
@auth
def racun():
    return f"Racun {True}"

# API


@bottle.put('/api/racun')
@auth
def ustvari_racun(gledalec: 'Uporabnik'):
    ime = bottle.request.forms.getunicode("ime")
    davek = float(bottle.request.forms.getunicode("davek"))

    racun = gledalec.ustvari_racun(ime, davek)

    bottle.redirect(f"/racun/{racun.ime}")

# Authorizacija


@bottle.get("/prijava")
def prijava_get():
    redirect = bottle.request.query.getunicode("redirect", "/")
    return bottle.template("prijava.html", redirect=redirect)


@bottle.post("/prijava")
def prijava_post():
    # Form data
    uporabnisko_ime = bottle.request.forms.getunicode('uporabnisko_ime')
    geslo = bottle.request.forms.getunicode('geslo')
    redirect = bottle.request.forms.getunicode('redirect')

    h = hashlib.blake2b()
    h.update(geslo.encode(encoding='utf-8'))
    zasifrirano_geslo = h.hexdigest()

    if uporabnisko_ime not in uporabniki:
        uporabnik = Uporabnik(
            uporabnisko_ime,
            zasifrirano_geslo,
        )
        uporabniki[uporabnisko_ime] = uporabnik
    else:
        uporabnik = uporabniki[uporabnisko_ime]
        uporabnik.preveri_geslo(zasifrirano_geslo)

    # Ustvari sejo
    bottle.response.set_cookie(
        SESSION_COOKIE, uporabnik.uporabnisko_ime, path='/', secret=skrivnost)
    bottle.redirect('/')


@bottle.get('/odjava')
def odjava():
    bottle.response.delete_cookie(SESSION_COOKIE, path='/')
    bottle.redirect('/')


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    bottle.run(debug=True, reloader=True)
