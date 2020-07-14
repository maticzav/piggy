from model import Racun

moj_racun = Racun("Matičev račun", davek=0.5)

moj_racun.ustvari_mesecni_prihodek(opis="Žepnina", kolicina=20)
moj_racun.ustvari_mesecni_prihodek(
    opis="Delo pri Petru", kolicina=2000)
# moj_racun.us(
#     opis="Najemnina za sobo", kolicina=-250)

print(moj_racun.nasparano)
