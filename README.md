# piggy

Budget planner za miljonarje.

## Zagon

Za zagon Piggy-ja je potrebno s spleta namestiti vse pomožne knjižnice. To lahko naredite z ukazom

```bash
pip install -r requirements.txt
```

Spletni vmesnik nato zaženete z

```bash
python main.py
```

## Nastavitev razvijalskega orodja

Priporočam, da si nastavite `virtualenv` pred začetkom razvijanja, da se knjižnice, ki jih uporablja Piggy ne bodo teple z ostalimi knjižnicami na vašem računalniku.

Kako namestiti `virtualenv` si lahko preberete [tukaj](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).

> Ne pozabite zagnati `virtualenv`!

Za razvijanje Piggy-ja je potrebno s spleta namestiti vse pomožne knjižnice. To lahko naredite z ukazom

```bash
pip install -r requirements.txt
```

Če boste uporabljali nove pomožne knjižnice, jih dodajte na seznam s pomočjo

```bash
pip freeze > requirements.txt
```

> VSCode: Če uporabljate za razvijanje VSCode je najlažje usposobit `virtualenv` tako, da iz terminala odprete VSCode (`code .`) in nato izberete default Python interpreter.