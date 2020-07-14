import unittest

from model import Racun


class IntegrationTests(unittest.TestCase):

    # ------------------------------------------------------------------------

    # Postavi račun.
    def setUp(self):
        self.racun = Racun("Testen račun", davek=0.5)

    # Račun ------------------------------------------------------------------

    def test_racun_pravilno_izracuna_investicije(self):
        self.racun.ustvari_mesecni_prihodek(
            opis="Mesečni Prihodek", znesek=100)
        self.racun.ustvari_prihodek(opis="Enkratni prihodek", znesek=10)
        self.racun.ustvari_investicijo(opis="Investicija", znesek=20)

        self.assertEqual(self.racun.namenjeno_za_investiranje, 55)
        self.assertEqual(self.racun.porabljeno_od_investicij, 20)
        self.assertEqual(self.racun.razpolozljivo_za_investicije, 35)

    def test_racun_pravilno_izracuna_nerazporejen_denar(self):
        kuverta = self.racun.ustvari_kuverto("Kuverta")

        self.racun.ustvari_mesecni_prihodek(
            opis="Mesečni Prihodek",
            znesek=100,
            razpored_po_kuvertah={
                kuverta: 30
            }
        )
        self.racun.ustvari_prihodek(
            opis="Enkratni prihodek",
            znesek=50,
            razpored_po_kuvertah={
                kuverta: 10
            }
        )
        self.racun.ustvari_odhodek("Splošen odhodek", znesek=30)

        self.assertEqual(self.racun.nerazporejeno_razpolozljivo, 5)
        self.assertEqual(self.racun.nerazporejeno_namenjeno, 35)
        self.assertEqual(self.racun.nerazporejeno_porabljeno, 30)

    def test_racun_pravilno_izracuna_denar_v_kuvertah(self):
        prva_kuverta = self.racun.ustvari_kuverto("Prva Kuverta")
        druga_kuverta = self.racun.ustvari_kuverto("Druga Kuverta")

        self.racun.ustvari_mesecni_prihodek(
            opis="Mesečni Prihodek",
            znesek=100,
            razpored_po_kuvertah={
                prva_kuverta: 30
            }
        )
        self.racun.ustvari_prihodek(
            opis="Enkratni prihodek",
            znesek=50,
            razpored_po_kuvertah={
                druga_kuverta: 10
            }
        )
        self.assertEqual(self.racun.namenjeno_za_kuverte, 40)

    # Kuverte ----------------------------------------------------------------

    def test_kuverte_neki(self):
        pass

# kuverta_hrana = moj_racun.ustvari_kuverto(ime="Hrana")
# kuverta_obleke = moj_racun.ustvari_kuverto(ime="Obleke")


# # Ustvari mesecne stroške.
# najemnina_stanovanje = moj_racun.ustvari_mesecni_odhodek(
#     opis="Stanovanje", znesek=200)

# # Ustvari mesečne prihodke.
# moj_racun.ustvari_mesecni_prihodek(opis="Delo pri Petru", znesek=2000, razpored_po_kuvertah={
#     kuverta_hrana: 200,
#     najemnina_stanovanje: 150,
# })
# moj_racun.ustvari_mesecni_prihodek(opis="Štipendija", znesek=150, razpored_po_kuvertah={
#     kuverta_hrana: 20,
#     kuverta_obleke: 100,
# })

# # Ustvari nekaj priložnostnih prihodkov

# moj_racun.ustvari_prihodek(opis="Ukradel avto", znesek=20)

# # Evidentiraj investicijo

# moj_racun.ustvari_investicijo(opis="BitCoin bigbrain", znesek=1000)

# # Naredi še nekaj odhodkov

# moj_racun.ustvari_odhodek(opis="Kino", znesek=2)
# moj_racun.ustvari_odhodek_iz_kuverte(
#     opis="Kebab", znesek=10, kuverta=kuverta_hrana)

# # Preveri koliko denarja ostane

# print(f"""
# Za investicije si namenil: {moj_racun.namenjeno_za_investiranje}
# V kuverte je šlo: {moj_racun.namenjeno_za_kuverte}
# Za ostalo ti ostane: {moj_racun.nerazporejeno_razpolozljivo}
# """)


# print("Za najemnino dobimo iz:")
# for prihodek in najemnina_stanovanje.prihodki:
#     print(prihodek.opis)

class TestirajJSON(unittest.TestCase):
    def test_pravilno_nalozi_json(self):
        pass

    def test_pravilno_naredi_json(self):
        pass


if __name__ == '__main__':
    unittest.main()
