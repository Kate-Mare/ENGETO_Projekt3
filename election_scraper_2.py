"""
projekt_3.py: třetí projekt do Engeto Online Python Akademie
author: Kateřina Marková
email: cathy.markova@gmail.com
discord: kate_marko1_54460
"""


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

# Nastavení loggeru
logging.basicConfig(
    level=logging.INFO,  # Nastavení úrovně logování
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formát logu
    handlers=[
        logging.FileHandler("volebnivysledky.log"),  # Logování do souboru
        logging.StreamHandler(),  # Zobrazení logů v konzoli
    ],
)
logger = logging.getLogger(__name__)


def get_html(url):
    """ Funkce pro získání HTML."""
    logger.info(f"Začínám stahovat data z URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Úspěšně stažena data z URL: {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Chyba při stahování dat z URL: {url} - {e}")
        raise


def get_obce_links(url_celku):
    """ Funkce pro získání odkazů na jednotlivé obce v rámci zadaného územního celku."""
    html = get_html(url_celku)
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        logger.warning(f"Tabulky na stránce {url_celku} nebyly nalezeny.")
        return pd.DataFrame()  # prázdný DataFrame, pokud nejsou žádné tabulky
    obce_links = []
    for table in tables:
        for link in table.select("a"):  # Filtrujeme pouze odkazy obsahující "xobec"
            href = link["href"]
            if "xobec" in href:  # Najdeme rodičovskou buňku <td>
                td_parent = link.find_parent("td")
                if td_parent:
                    # Hledáme následující buňku obsahující název obce
                    obec_td = td_parent.find_next_sibling("td")
                    if obec_td:
                        cislo_obce = link.text.strip()  # Číslo obce z odkazu
                        nazev_obce = obec_td.text.strip()  # Název obce z následující buňky
                        url_obec = urljoin(url_celku, href)  # Vytvoření plné URL obce
                        obce_links.append({"cislo_obce": cislo_obce, "nazev_obce": nazev_obce, "url_obec": url_obec})
                        logger.info(f"Přidána obec: {nazev_obce} (URL: {url_obec})")
    if not obce_links:
        logger.warning(f"Nebyly nalezeny žádné odkazy na obce na stránce {url_celku}.")

    # Převedeme list obce_links na  DataFrame pro jednodušší manipulaci s daty
    return pd.DataFrame(obce_links)


def get_obec_details(url_obec):
    """ Funkce pro stahování obsahu stránky (HTML kódu) pro jednotlivé obce."""
    html = get_html(url_obec)
    soup = BeautifulSoup(html, "html.parser")
    try:
        # Zpracování základních detailů
        results = parse_basic_details(soup, url_obec) or {}

        # Zpracování volebních výsledků pro politické strany
        party_results = parse_party_results(soup) or {}

        # Sloučení základních údajů a výsledků politických stran do jednoho slovníku results
        results.update(party_results)
    except Exception as e:
        logger.error(f"Chyba při zpracování obce {url_obec}: {e}")
        return {"volici": None, "vydane_obalky": None, "platne_hlasy": None}

    return results


def parse_number(text):
    """Funkce převádí text na celé číslo."""
    try:
        return int(text.strip().replace("\xa0", "").replace(",", ""))
    except ValueError:
        return None


def parse_basic_details(soup, url_obec):
    """Získání základních údajů o počtu voličů, vydaných obálek a platných hlasů."""
    results = {}  # prázdný slovník pro ukládání dat

    volici_td = soup.select_one('td[headers="sa2"]')
    results["volici"] = parse_number(volici_td.text) if volici_td else None
    if not volici_td:
        logger.warning(f"Volici nebyli nalezeni na stránce {url_obec}.")

    vydane_obalky_td = soup.select_one('td[headers="sa3"]')
    results["vydane_obalky"] = parse_number(vydane_obalky_td.text) if vydane_obalky_td else None

    platne_hlasy_td = soup.select_one('td[headers="sa6"]')
    results["platne_hlasy"] = parse_number(platne_hlasy_td.text) if platne_hlasy_td else None

    return results


def parse_party_results(soup):
    """Získání výsledků pro jednotlivé politické strany."""
    party_results = {}  # prázdný slovník pro ukládání výsledků voleb jednotlivých stran
    rows = soup.select("table tr")

    for row in rows:
        # Regex pro filtrování atributů "headers"
        headers_patterns = re.compile(r"(t[1-3]sa[1-2] t[1-3]sb[2-3])")
        party_td = row.find("td", class_="overflow_name")
        votes_td = row.find("td", attrs={"class": "cislo", "headers": headers_patterns})

        if party_td and votes_td:
            party_name = party_td.text.strip()
            votes = parse_number(votes_td.text)
            party_results[party_name] = votes
        else:
            if not party_td:
                logger.warning(f"Chyba: Nenalezen <td> pro politickou stranu v řádku: {row}")
            if not votes_td:
                logger.warning(f"Chyba: Nenalezen <td> pro počet hlasů v řádku: {row}")

    return party_results


def scrape_all_obce(url_celku):
    """Iterace přes všechny obce a získání volebních dat."""
    df_obce = get_obce_links(url_celku)
    if df_obce.empty:
        logger.warning(f"Žádné obce nebyly nalezeny pro URL: {url_celku}")
        return pd.DataFrame()

    all_data = []  # prázdný seznam pro uložení výsledků
    for _, obec in df_obce.iterrows():
        logger.info(f"Zpracovávám obec: {obec['nazev_obce']} ({obec['cislo_obce']})")
        try:
            results = get_obec_details(obec["url_obec"])
            if results: # Pokud funkce vrátila výsledky
                df_obec = pd.DataFrame([results]) #Převod původního dictu results na DataFrame
                # Přidání informací o obci
                df_obec["cislo_obce"] = obec["cislo_obce"]
                df_obec["nazev_obce"] = obec["nazev_obce"]
                all_data.append(df_obec)
            else:
                logger.warning(f"Žádná data nebyla nalezena pro obec: {obec['nazev_obce']}")
        except Exception as e:
            logger.error(f"Chyba při zpracování obce {obec['nazev_obce']}: {e}")
            continue

    if all_data:
        # Připrava seznamu všech sloupců do tabulky výsledného CSV
        columns = [
            "cislo_obce",
            "nazev_obce",
            "volici",
            "vydane_obalky",
            "platne_hlasy",
        ]

        # Spojení všech DataFrame
        final_df = pd.concat(all_data, ignore_index=True).fillna(0)

        # Uspořádání sloupců podle požadovaného pořadí
        final_df = final_df.reindex(columns=columns + [col for col in final_df.columns if col not in columns],
                                    fill_value=0)

        logger.info(
            f"Zpracování dokončeno. Celkem obcí: {len(all_data)}. Tabulka obsahuje {final_df.shape[0]} řádků a {final_df.shape[1]} sloupců.")
        return final_df
    else:
        logger.warning("Žádná data nebyla nalezena. Vrací se prázdný DataFrame.")
        return pd.DataFrame()


def generate_readme(df, demo_table):
    """Generování README.md souboru."""
    if df.empty:
        logger.warning("Výstupní DataFrame je prázdný. README.md nebude obsahovat ukázková data.")
        return
    if not demo_table:
        logger.warning("Ukázková tabulka nebyla vygenerována. README.md nebude obsahovat ukázku dat.")
        return
    # Obsah README
    readme_content = textwrap.dedent(

        f"""
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

{demo_table}

# Autor
Projekt zpracovala:  Kateřina Marková
        """
    )

    # Uložení obsahu do README.md
    with open("README.md", "w", encoding="utf-8-sig") as file:
        file.write(readme_content)
    logger.info("README.md byl úspěšně vygenerován.")


def main():
    """Hlavní funkce"""
    def parse_arguments():
        """Zpracování argumentů příkazového řádku"""
        parser = argparse.ArgumentParser(description="Scrapování dat z volební stránky.")
        # Přidání povinného argumentu pro URL volebních výsledků
        parser.add_argument("url_volebnich_vysledku", help="URL volebních výsledků ")
        # Přidání druhého povinného argumentu pro název výstupního souboru
        parser.add_argument("output_file", help="Název výstupního souboru (.csv)")
        return parser.parse_args()

    def validate_arguments(args):
        """Kontrola validace argumentů"""
        if not validators.url(args.url_volebnich_vysledku):
            logger.warning("První argument musí být platná URL!")
            sys.exit(1)

        if not args.output_file.endswith(".csv"):
            logger.warning("Druhý argument musí být název souboru s příponou .csv!")
            sys.exit(1)

    def save_to_csv(df, output_file):
        """Uložení DataFrame do CSV (použití 2. argumentu)"""
        # Vyplnění prázdných hodnot (např. pro strany, které nemají hlas v některé obci) hodnotou 0
        df.fillna(0, inplace=True)
        df.to_csv(output_file, index=False, sep=";", encoding="utf-8-sig")
        logger.info(f"Výsledky byly uloženy do '{output_file}'.")

    def generate_demo_table(df):
        """Generování ukázkové tabulky z CSV"""
        selected_columns = df.columns[:7]
        demo_table = df[selected_columns].iloc[:5].to_markdown(index=False, tablefmt="grid")
        return textwrap.dedent(demo_table).lstrip("\ufeff")  # Odstraní BOM, pokud existuje

    # 1. Zpracování argumentů příkazového řádku
    args = parse_arguments()

    # 2. Validace argumentů
    validate_arguments(args)

    # 3. Scrapování dat
    logger.info(f"URL volebních výsledků: {args.url_volebnich_vysledku}")
    df = scrape_all_obce(args.url_volebnich_vysledku)
    if df.empty or len(df.columns) < 7:
        logger.warning("Extrahování dat nebylo úspěšné. DataFrame neobsahuje dostatek"
                       "sloupců pro ukázkovou tabulku.")
        sys.exit(1)

    # 4. Uložení dat do CSV
    save_to_csv(df, args.output_file)

    # 5. Generování ukázky tabulky
    demo_table = generate_demo_table(df)

    # 6. Generování README.md
    generate_readme(df, demo_table)


if __name__ == "__main__":
    main()
