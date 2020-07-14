from model import Racun

moj_racun = Racun("Matičev račun", davek=0.5)

kuverta_hrana = moj_racun.ustvari_kuverto(ime="Hrana")
kuverta_obleke = moj_racun.ustvari_kuverto(ime="Obleke")


# Ustvari mesecne stroške.
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

# Ustvari nekaj priložnostnih prihodkov

moj_racun.ustvari_prihodek(opis="Ukradel avto", znesek=20)

# Evidentiraj investicijo

moj_racun.ustvari_investicijo(opis="BitCoin bigbrain", znesek=1000)

# Naredi še nekaj odhodkov

moj_racun.ustvari_odhodek(opis="Kino", znesek=2)
moj_racun.ustvari_odhodek_iz_kuverte(
    opis="Kebab", znesek=10, kuverta=kuverta_hrana)

# Preveri koliko denarja ostane

print(f"""
Za investicije si namenil: {moj_racun.namenjeno_za_investiranje}
V kuverte je šlo: {moj_racun.namenjeno_za_kuverte}
Za ostalo ti ostane: {moj_racun.nerazporejeno_razpolozljivo}
""")


# Izvozi

moj_racun.izvozi_v_datoteko("test.json")


# Uvozi
uvozen_racun = Racun.uvozi_iz_datoteke("test.json")

print(f"""
Za investicije si namenil: {uvozen_racun.namenjeno_za_investiranje}
V kuverte je šlo: {uvozen_racun.namenjeno_za_kuverte}
Za ostalo ti ostane: {uvozen_racun.nerazporejeno_razpolozljivo}
""")
