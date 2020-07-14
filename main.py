from model import Racun

moj_racun = Racun("Matičev račun", davek=0.5)

kuverta_hrana = moj_racun.ustvari_kuverto(ime="Hrana")
kuverta_obleke = moj_racun.ustvari_kuverto(ime="Obleke")

# Ustvari mesečne prihodke.
moj_racun.ustvari_mesecni_prihodek(opis="Žepnina", kolicina=20)
moj_racun.ustvari_mesecni_prihodek(opis="Delo pri Petru", kolicina=2000, razpored_po_kuvertah={
    kuverta_hrana: 200
})
moj_racun.ustvari_mesecni_prihodek(opis="Štipendija", kolicina=150, razpored_po_kuvertah={
    kuverta_hrana: 20,
    kuverta_obleke: 100
})

# Ustvari mesečne odhodke.
moj_racun.ustvari_mesecni_odhodek(opis="Najemnina za sobo", kolicina=250)


moj_racun.ustvari_prihodek(opis="Ukradel avto", kolicina=20)

moj_racun.ustvari_investicijo(opis="BitCoin bigbrain", kolicina=1000)

print(f"Investiraš lahko: {moj_racun.stanje_investicij}")
