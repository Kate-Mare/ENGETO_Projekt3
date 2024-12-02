
# Election Scraper
Tento projekt scrapuje výsledky voleb z roku 2017 ze stránky [www.volby.cz](https://www.volby.cz) 
a generuje výstupní CSV soubor obsahující informace o:
- obcích
- voličích
- vydaných obálkách
- platných hlasech
- výsledcích jednotlivých politických stran

Data jsou extrahována z externího API pomocí knihovny `requests` a analyzována za pomoci knihoven:

- `argparse`
- `BeautifulSoup`
- `pandas`
- `textwrap`
- `re`

# Instalace
1. Nejprve si vytvořte virtuální prostředí:
   ```bash
   python -m venv venv
    ```
2.  Aktivujte virtuální prostředí:
    ```bash
    source venv/bin/activate
    ```
3.  Nainstalujte potřebné knihovny ze souboru 'requirements.txt':
    ```bash
    pip install -r requirements.txt
    ```
# Spuštění projektu
Projekt spustíte z příkazového řádku s povinnými 2 argumenty (název .py souboru,
název generovaného .csv souboru):
    ```bash
    python election_scraper.py vysledky_pvychod.csv
    ```
# Ukázka kódu
Tento kód ukazuje, jak načíst HTML zdrojový kód z webové stránky a jak jej zpracovat 
pomocí knihovny BeautifulSoup.

```python
import requests
from bs4 import BeautifulSoup

# URL hlavní stránky
main_url = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109"

# Funkce pro načtení HTML
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Načtení seznamu obcí
def get_obce_links(main_url):
    html = get_html(main_url)
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.select('table')
    obce_links = []
    for table in tables:
        for link in table.select('a'):
            href = link['href']
            if "xobec" in href:
                full_url = f"https://www.volby.cz/pls/ps2017nss/...
                td_parent = link.find_parent("td")
```

# Demo výstupy
Projekt generuje výsledky voleb z roku 2017 do .csv souboru ve formě tabulky,
která má sloupce jako 'cislo_obce', 'nazev_obce', 'volici', 'vydane_obalky',
'platne_hlasy', 'Blok proti islam.-Obran.domova' aj.

+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+
|   cislo_obce | nazev_obce                       |   volici |   vydane_obalky |   platne_hlasy |   ANO 2011 |   Blok proti islam.-Obran.domova |
+==============+==================================+==========+=================+================+============+==================================+
|       538043 | Babice                           |      732 |             533 |            531 |        128 |                                0 |
+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+
|       538051 | Bašť                             |     1409 |             966 |            961 |        239 |                                0 |
+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+
|       534684 | Borek                            |      242 |             170 |            170 |         64 |                                0 |
+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+
|       538086 | Bořanovice                       |      627 |             440 |            440 |        103 |                                0 |
+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+
|       538094 | Brandýs nad Labem-Stará Boleslav |    13374 |            8625 |           8580 |       2311 |                               11 |
+--------------+----------------------------------+----------+-----------------+----------------+------------+----------------------------------+

# Autor
author: Kateřina Marková
email: cathy.markova@gmail.com
discord: kate_marko1_54460
