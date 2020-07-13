from model import Racun

moj_racun = Racun("Matičev račun", davek=0.5)

moj_racun.ustvari_ponavljajoco_transakcijo(opis="Žepnina", kolicina=20)
moj_racun.ustvari_ponavljajoco_transakcijo(
    opis="Delo pri Petru", kolicina=2000)
moj_racun.ustvari_ponavljajoco_transakcijo(
    opis="Najemnina za sobo", kolicina=-250)

print(moj_racun.razpolozljiv_denar_za_kuverte)
