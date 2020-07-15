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
    uporabnik = Uporabnik.uvozi_iz_datoteke(
        os.path.join(data_dir, ime_datoteke))
    uporabniki[uporabnik.email] = uporabnik

SESSION_COOKIE = "Authorization"


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


class Uporabnik(Uporabnik):

    # Razširjeno -------------------------------------------------------------

    def shrani(self):
        """Shrani stanje uporabnika."""
        self.izvozi_v_datoteko(os.path.join(data_dir, f"{self.email}.json"))


# Static files ---------------------------------------------------------------


@bottle.get("/static/<path:path>")
def files(path):
    return bottle.static_file(path, root="public/")

# Spletni vmesnik ------------------------------------------------------------


@bottle.get("/")
@bottle.view("index.html")
@auth
def domov(gledalec: 'Uporabnik'):
    return {
        "racuni": gledalec.racuni.values()
    }


@bottle.get("/racun/<ime>")
@bottle.view("racun.html")
@auth
def racun(ime: str, gledalec: 'Uporabnik'):
    racun = gledalec.racuni.get(ime)

    if racun is None:
        return bottle.HTTPError(404)

    return {"racun": racun}

# Errors


@bottle.error(404)
def error404(error):
    return bottle.template("error.html")
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


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    bottle.run(debug=True, reloader=True)
