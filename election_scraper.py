"""
projekt_3.py: třetí projekt do Engeto Online Python Akademie
author: Kateřina Marková
email: cathy.markova@gmail.com
discord: kate_marko1_54460
"""

import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import textwrap
import re

# URL hlavní stránky
main_url = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109"


# Funkce pro načtení HTML
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


# Funkce pro vytvoření seznamu názvů obcí pro vybraný územní celek
def get_obce_links(main_url):
    html = get_html(main_url)
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.select('table')
    obce_links = []
    for table in tables:
        for link in table.select('a'):
            href = link['href']
            if "xobec" in href:
                full_url = f"https://www.volby.cz/pls/ps2017nss/{href}"
                td_parent = link.find_parent("td")
                if td_parent:
                    obec_td = td_parent.find_next_sibling("td", attrs={
                        "class": "overflow_name",
                        "headers": lambda x: x in ["t1sa1 t1sb2", "t2sa1 t2sb2", "t3sa1 t3sb2"]
                    })
                    if obec_td:
                        nazev_obce = obec_td.text.strip()
                        obce_links.append((link.text.strip(), nazev_obce, full_url))
                        print(f"Přidána obec: {nazev_obce} (URL: {full_url})")

    return obce_links

# Získání detailů pro jednotlivé obce
def get_obec_details(obec_url):
    html = get_html(obec_url)
    soup = BeautifulSoup(html, 'html.parser')
    try:
        volici_td = soup.select_one('td[headers="sa2"]')
        volici = int(volici_td.text.strip().replace('\xa0', '').replace(',', ''))\
            if volici_td and volici_td.text else None

        vydane_obalky_td = soup.select_one('td[headers="sa3"]')
        vydane_obalky = int(
            vydane_obalky_td.text.strip().replace('\xa0', '').replace(',', ''))\
            if vydane_obalky_td and vydane_obalky_td.text else None

        platne_hlasy_td = soup.select_one('td[headers="sa6"]')
        platne_hlasy = int(
            platne_hlasy_td.text.strip().replace('\xa0', '').replace(',', ''))\
            if platne_hlasy_td and platne_hlasy_td.text else None

        # Získání volebních výsledků pro jednotlivé politické strany
        party_results = {}
        rows = soup.select('table tr')
        for row in rows:
            try:
                headers_patterns = re.compile(r"(t[1-3]sa[1-2] t[1-3]sb[2-3])")
                party_td = row.find(
                    "td",
                    attrs={
                        "class": "overflow_name",
                        "headers": re.compile(headers_patterns)
                    }
                )
                votes_td = row.find(
                    "td",
                    attrs={
                        "class": "cislo",
                        "headers": re.compile(headers_patterns)
                    }
                )

                if party_td and votes_td:
                    party_name = party_td.text.strip()
                    votes = int(votes_td.text.strip().replace('\xa0', '').replace(',', ''))
                    party_results[party_name] = votes
                else:
                    if not party_td:
                        print(f"Chyba: Nenalezen <td> pro politickou stranu v řádku: {row}")
                    if not votes_td:
                        print(f"Chyba: Nenalezen <td> pro počet hlasů v řádku: {row}")
            except Exception as e:
                print(f"Chyba při zpracování řádku: {e}")
    except Exception as e:
            print(f"Chyba při zpracování obce {obec_url}: {e}")
            return {"volici": None, "vydane_obalky": None,
                    "platne_hlasy": None, **{}}
    return {"volici": volici, "vydane_obalky": vydane_obalky, "platne_hlasy": platne_hlasy, **party_results}

# Iterace přes všechny obce a získání volebních dat
def scrape_all_obce(main_url):
    obce_links = get_obce_links(main_url)
    all_data = []
    all_parties = set()
    for obec in obce_links:
        print(f"Zpracovávám obec: {obec[1]} ({obec[0]})")
        details = get_obec_details(obec[2])
        details["cislo_obce"] = obec[0]
        details["nazev_obce"] = obec[1]
        all_parties.update(details.keys() - {"cislo_obce", "nazev_obce", "volici", "vydane_obalky", "platne_hlasy"})
        all_data.append(details)
    return all_data, sorted(all_parties)


# Generování README.md souboru
def generate_readme(demo_table):
    readme_content = textwrap.dedent(f"""
# Election Scraper
Tento projekt extrahuje výsledky voleb z roku 2017 ze stránky [www.volby.cz](https://www.volby.cz).
Data stahuje pomocí knihovny "request" a zpracovává  dále za pomoci knihoven:
- `argparse`
- `BeautifulSoup`
- `pandas`
- `textwrap`
- `re`
 
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
    venv\Scripts\activate
    ```
3.  Nainstalujte potřebné knihovny ze souboru 'requirements.txt':
    ```bash
    pip install -r requirements.txt
    ```
# Spuštění projektu
Projekt spustíte z příkazového řádku zadáním názvu vstupního .py souboru a 2 povinných argumentů ve formátu:
python election_scraper.py <url_volebnich_vysledku> <output_file>
    ```bash
    python election_scraper.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109"
     vysledky_pvychod.csv
    ```
    
# Ukázka kódu
Tento kód ukazuje, jak se nejprve načte HTML zdrojový kód z webové stránky a následně jej zpracuje
pomocí knihovny BeautifulSoup na jednotlivé tagy, tedy části kódu. Projde jednotlivé tagy a hledá v nich 
všechny tabulky. V každé nalezené tabulce vyhledává odkazy na údaje o konkrétní obci.

```python
import requests
from bs4 import BeautifulSoup

# URL hlavní stránky
main_url = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109"

# Funkce pro načtení vybrané HTML
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Funkce pro vytvoření seznamu názvů obcí pro vybraný územní celek
def get_obce_links(main_url):
    html = get_html(main_url)
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.select('table')
    obce_links = []
    for table in tables:
        for link in table.select('a'):
            href = link['href']
            if "xobec" in href:
                full_url = f"https://www.volby.cz/pls/ps2017nss/..."
                td_parent = link.find_parent("td")
                ...
```

# Demo výstupy
Projekt generuje výsledky voleb z roku 2017 do CSV souboru ve formě tabulky,
která má sloupce jako 'cislo_obce', 'nazev_obce', 'volici', 'vydane_obalky',
'platne_hlasy', 'Blok proti islam.-Obran.domova' aj.

Ukázka výsledné CSV tabulky ve formátu Markdown:

{demo_table}

# Autor
Projekt zpracovala:  Kateřina Marková
""")

    # Uložení obsahu do README.md
    with open("README.md", "w", encoding="utf-8-sig") as file:
        file.write(readme_content)

    print("README.md byl úspěšně vygenerován.")


# Hlavní funkce
def main():
    # Zpracování argumentů příkazového řádku
    parser = argparse.ArgumentParser(description="Scrapování dat z volební stránky.")

    # Přidání povinného argumentu pro URL volebních výsledků
    parser.add_argument("url_volebnich_vysledku",
                        help="URL volebních výsledků "
                             "(např. https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109)")

    # Přidání druhého povinného argumentu pro název výstupního souboru
    parser.add_argument("output_file", help="Název výstupního souboru (např. vysledky.csv)")
    args = parser.parse_args()

    # Použití 1. argumentu
    print(f"URL volebních výsledků: {args.url_volebnich_vysledku}")

    # Získání dat
    all_data, all_parties = scrape_all_obce(main_url)

    # Připrava seznamu všech sloupců do tabulky výsledného CSV
    columns = ["cislo_obce", "nazev_obce", "volici", "vydane_obalky", "platne_hlasy"] + all_parties

    # Vytvoření DataFrame a explicitní nastavení sloupců
    df = pd.DataFrame(all_data, columns=columns)

    # Vyplnění prázdných hodnot (např. pro strany, které nemají hlas v některé obci) hodnotou 0
    df.fillna(0, inplace=True)

    # Uložení do CSV (použití 2. argumentu)
    df.to_csv(args.output_file, index=False, sep=";", encoding='utf-8-sig')
    print(f"Výsledky byly uloženy do '{args.output_file}'.")

    # Generování ukázky z CSV
    selected_columns = df.columns[:7]
    demo_table = df[selected_columns].iloc[:5].to_markdown(index=False, tablefmt="grid")
    demo_table = demo_table.lstrip("\ufeff")  # Odstraní BOM, pokud existuje

    # Kontrola a odstranění BOM
    if demo_table.startswith("\ufeff"):
        demo_table = demo_table[1:]

    # Zarovnání obsahu tabulky
    demo_table = textwrap.dedent(demo_table)

    # Generování README.md
    generate_readme(demo_table)


if __name__ == "__main__":
    main()