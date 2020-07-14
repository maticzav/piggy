from model import Racun

moj_racun = Racun("Matičev račun", davek=0.5)

kuverta_hrana = moj_racun.ustvari_kuverto(ime="Hrana")
kuverta_obleke = moj_racun.ustvari_kuverto(ime="Obleke")

najemnina_stanovanje = moj_racun.ustvari_mesecni_odhodek(
    opis="Stanovanje", znesek=200)

# Ustvari mesečne prihodke.
moj_racun.ustvari_mesecni_prihodek(opis="Žepnina", znesek=20)
moj_racun.ustvari_mesecni_prihodek(opis="Delo pri Petru", znesek=2000, razpored_po_kuvertah={
    kuverta_hrana: 200,
    najemnina_stanovanje: 150,
})
moj_racun.ustvari_mesecni_prihodek(opis="Štipendija", znesek=150, razpored_po_kuvertah={
    kuverta_hrana: 20,
    kuverta_obleke: 100,
})

# Ustvari mesečne odhodke.
moj_racun.ustvari_mesecni_odhodek(opis="Najemnina za sobo", znesek=250)


moj_racun.ustvari_prihodek(opis="Ukradel avto", znesek=20)

moj_racun.ustvari_investicijo(opis="BitCoin bigbrain", znesek=1000)

print(f"Stanovanje plačano: {najemnina_stanovanje.placano}")
print(f"Investiraš lahko: {moj_racun.stanje_investicij}")

print("Za najemnino dobimo iz:")
for prihodek in najemnina_stanovanje.prihodki:
    print(prihodek.opis)
