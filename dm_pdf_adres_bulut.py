"""divanmakam.com konu sayfalarindaki PDF eklerinin adreslerini toplar (GitHub Actions'ta calisir).

Girdi: konular.txt (her satir bir konu adresi). Cikti: pdf_adres.json {konu adresi: [ek adresi, ...]} (bos liste: PDF yok).
Kaldigi yerden devam eder; --sinir N (en cok N konu) ve --dakika M (en cok M dakika) ile parca parca calisir.
Siteyi yormamak icin istekler arasi 1 sn. Ust uste cok hata olursa (engellenme) durur.
"""
import json
import os
import re
import sys
import time
import urllib.request

SITE = "https://divanmakam.com"
CIKTI = "pdf_adres.json"


def arg(ad, varsayilan):
    return type(varsayilan)(sys.argv[sys.argv.index(ad) + 1]) if ad in sys.argv else varsayilan


def kaydet(sonuc):
    json.dump(sonuc, open(CIKTI + ".yeni", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    os.replace(CIKTI + ".yeni", CIKTI)


def main():
    sinir, dakika = arg("--sinir", 10 ** 6), arg("--dakika", 50)
    bitis = time.time() + dakika * 60
    konular = [l.strip() for l in open("konular.txt", encoding="utf-8") if l.strip()]
    sonuc = json.load(open(CIKTI, encoding="utf-8")) if os.path.exists(CIKTI) else {}
    kalan = [u for u in konular if u not in sonuc][:sinir]
    print("konu %d, yapilmis %d, bu parcada en cok %d" % (len(konular), len(konular) - len([u for u in konular if u not in sonuc]), len(kalan)), flush=True)
    hata_ust_uste, yapilan = 0, 0
    for url in kalan:
        if time.time() > bitis:
            break
        try:
            istek = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nota-arsivi; kisisel arsiv)"})
            s = urllib.request.urlopen(istek, timeout=60).read().decode("utf-8", "replace")
            ekler = []
            for ek in re.findall(r'href="(/attachments/[^"/]+-pdf\.\d+/)"', s):
                if SITE + ek not in ekler:
                    ekler.append(SITE + ek)
            sonuc[url] = ekler
            hata_ust_uste = 0
            yapilan += 1
        except Exception as e:  # noqa: BLE001
            hata_ust_uste += 1
            print("hata:", url, e, flush=True)
            if hata_ust_uste >= 20:
                print("ust uste 20 hata: site erisimi engelliyor olabilir, duruldu", flush=True)
                break
            time.sleep(10)
        time.sleep(1)
        if yapilan and yapilan % 200 == 0:
            kaydet(sonuc)
    kaydet(sonuc)
    pdfli = sum(1 for v in sonuc.values() if v)
    print("bu parcada %d konu; toplam %d/%d (pdf'li %d, pdf'siz %d)" % (yapilan, len(sonuc), len(konular), pdfli, len(sonuc) - pdfli))
    if len([u for u in konular if u not in sonuc]) == 0:
        open("BITTI", "w").close()


if __name__ == "__main__":
    main()
