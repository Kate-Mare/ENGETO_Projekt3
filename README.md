
# Election Scraper
Tento projekt extrahuje výsledky voleb z roku 2017 ze stránky [www.volby.cz](https://www.volby.cz).
Data stahuje pomocí knihovny "request" a zpracovává  dále za pomoci knihoven:
- `argparse`
- `BeautifulSoup`
- `pandas`
- `textwrap`
- `re`
- `sys`
- `logging`
- `urllib`
- `validators`

Ze zpracovaných dat následně vygeneruje výstupní CSV soubor obsahující informace o:
- jednotlivých obcích v rámci zvoleného územního celku
- počtu voličů
- počtu vydaných obálek
- počtu platných hlasů
- výsledcích voleb jednotlivých politických stran.

Přínosem tohoto projektu je zpracování volebních dat dle zvoleného územního celku v přehledné tabulce, 
kterou je možné dále využít např. k vizualizaci dat nebo pro případné další statistické operace.

# Instalace
1. Nejprve si vytvořte virtuální prostředí:
   ```bash
   python3 -m venv venv
    ```  
2.  Aktivujte virtuální prostředí:
    Aktivace pro Linux/Mac:
    ```bash
    source venv/bin/activate
    ```
    Aktivace ve Windows:
     ```bash
    venv\Scriptsctivate
    ```
3.  Nainstalujte potřebné knihovny ze souboru 'requirements.txt':
    ```bash
    pip install -r requirements.txt
    ```
# Spuštění projektu
Projekt spustíte z příkazového řádku zadáním názvu vstupního .py souboru a 2 povinných argumentů ve formátu:
python election_scraper.py <url_volebnich_vysledku> <output_file>
    ```bash
    python election_scraper.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2111"
     "vysledky_pribram.csv"
    ```

# Ukázka kódu
Tento kód ukazuje, jak se nejprve načte HTML zdrojový kód z webové stránky a následně jej zpracuje
pomocí knihovny BeautifulSoup na jednotlivé tagy, tedy části kódu. Projde jednotlivé tagy a hledá v nich 
všechny tabulky. V každé nalezené tabulce vyhledává odkazy na údaje o konkrétní obci.

```python
import sys
import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import textwrap
import re
import logging
from urllib.parse import urljoin
import validators

def get_html(url):
    #Funkce pro získání HTML.
    logger.info(f"Začínám stahovat data z URL: ...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Úspěšně stažena data z URL: ...")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Chyba při stahování dat z URL: ...")
        raise


def get_obce_links(url_celku):
    #Funkce pro získání odkazů na jednotlivé obce v rámci zadaného územního celku.
    html = get_html(url_celku)
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        logger.warning(f"Tabulky na stránce ... nebyly nalezeny.")
        return pd.DataFrame() #prázdný DataFrame, pokud nejsou žádné tabulky
    obce_links = []
    for table in tables:
        for link in table.select("a"):  # Filtrujeme pouze odkazy obsahující "xobec"
            href = link["href"]
            if "xobec" in href:
            # Najdeme rodičovskou buňku <td>
                td_parent = link.find_parent("td")
                ...
```

# Demo výstupy
Projekt generuje výsledky voleb z roku 2017 do CSV souboru ve formě tabulky,
která má sloupce jako 'cislo_obce', 'nazev_obce', 'volici', 'vydane_obalky',
'platne_hlasy', 'Blok proti islam.-Obran.domova' aj.

Ukázka výsledné CSV tabulky ve formátu Markdown:

+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+
|   cislo_obce | nazev_obce             |   volici |   vydane_obalky |   platne_hlasy |   Občanská demokratická strana |   Řád národa - Vlastenecká unie |
+==============+========================+==========+=================+================+================================+=================================+
|       529672 | Bezděkov pod Třemšínem |      134 |             105 |            103 |                             12 |                               0 |
+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+
|       564559 | Bohostice              |      167 |             108 |            108 |                             12 |                               0 |
+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+
|       539953 | Bohutín                |     1417 |             925 |            920 |                             93 |                               1 |
+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+
|       539970 | Borotice               |      302 |             202 |            202 |                             18 |                               1 |
+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+
|       539988 | Bratkovice             |      252 |             167 |            166 |                             29 |                               0 |
+--------------+------------------------+----------+-----------------+----------------+--------------------------------+---------------------------------+

# Autor
Projekt zpracovala:  Kateřina Marková
