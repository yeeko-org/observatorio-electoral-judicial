import requests
from bs4 import BeautifulSoup
import json
import re
import urllib.parse
import time
import urllib3


class URLExtractor:

    def __init__(self, initial_url):
        """Initialize the extractor with the starting URL."""
        self.base_url = ("https://w3.cjf.gob.mx/sevie_page/busquedas"
                         "/Consultas/botones.asp")
        self.current_url = initial_url
        self.records = []
        self.visited_urls = set()

    def extract_href_from_last_a_tag(self, html_content):
        """Extract the href attribute from the last 'a' tag in the HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        all_a_tags = soup.find_all('a')
        if all_a_tags:
            last_a_tag = all_a_tags[-1]
            return last_a_tag.get('href')
        return None

    def extract_parameters(self, href):
        """Extract 'rutaFichas' and 'exp' parameters from the href."""
        if not href:
            return None, None

        # Extract parameters using regex
        exp_match = re.search(r'exp=(\d+)', href)
        ruta_match = re.search(r'rutaFichas=([^&]+)', href)

        exp = exp_match.group(1) if exp_match else None
        ruta_fichas = ruta_match.group(1) if ruta_match else None

        return exp, ruta_fichas

    def build_next_url(self, exp, ruta_fichas):
        """Build the next URL using the extracted parameters."""
        if not exp or not ruta_fichas:
            return None

        params = {
            'exp': exp,
            'rutaFichas': ruta_fichas
        }
        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def extract_and_build(self):
        """Extract information from the current URL and build the next one."""
        try:
            # Check if we've already visited this URL to avoid loops
            if self.current_url in self.visited_urls:
                print(f"URL already visited: {self.current_url}")
                return None

            self.visited_urls.add(self.current_url)

            response = requests.get(self.current_url, verify=False)
            urllib3.disable_warnings(
                # Suppress only the warnings about insecure requests
                urllib3.exceptions.InsecureRequestWarning)
            response.raise_for_status()  # Raise an exception for bad responses

            html_content = response.text
            href = self.extract_href_from_last_a_tag(html_content)

            if not href:
                print("No href found in the last 'a' tag.")
                return None

            exp, ruta_fichas = self.extract_parameters(href)

            if not exp or not ruta_fichas:
                print(f"Could not extract valid parameters from href: {href}")
                return None

            # Store the record
            next_url = self.build_next_url(exp, ruta_fichas)
            record = {
                'exp': exp,
                'rutaFichas': ruta_fichas,
                'url': next_url
            }
            self.records.append(record)

            # Build the next URL

            return next_url

        except requests.RequestException as e:
            print(f"Error making the request: {e}")
            return None

    def extract_all_records(self, max_records=100, delay=1):
        """Extract all records from the sequence of URLs."""
        count = 0
        while self.current_url and count < max_records:
            next_url = self.extract_and_build()
            if not next_url:
                print("No next URL found. Stopping.")
                break

            if next_url in self.visited_urls:
                print(f"Next URL already visited: {next_url}. Stopping.")
                break

            self.current_url = next_url
            count += 1

            # Add a delay to be nice to the server
            if delay > 0:
                time.sleep(delay)

        print(f"Extracted {len(self.records)} records.")
        return self.records

    def save_to_json(self, filename='records.json'):
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(json.dumps(self.records, indent=4))
            print(f"Records saved to {filename}.")
        except IOError as e:
            print(f"Error saving records to {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error saving to {filename}: {e}")

    def read_from_json(self, filename='records.json'):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                self.records = json.load(file)
            print(f"Records loaded from {filename}.")
        except IOError as e:
            print(f"Error loading records from {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error loading from {filename}: {e}")


if __name__ == "__main__":
    # Initial URL
    initial_url = ("https://w3.cjf.gob.mx/sevie_page/busquedas/Consultas"
                   "/botones.asp?exp=75315&rutaFichas=FichasJueMag")
    extractor = URLExtractor(initial_url)
    # records = extractor.extract_all_records(max_records=200, delay=1)
    records = extractor.extract_all_records(max_records=2000, delay=0)
    extractor.save_to_json('fixture/oej/fichas_records.json')


def save_in_model():
    from oej.models import Biography
    initial_url = ("https://w3.cjf.gob.mx/sevie_page/busquedas/Consultas"
                   "/botones.asp?exp=75315&rutaFichas=FichasJueMag")
    extractor = URLExtractor(initial_url)
    records_json = 'fixture/oej/fichas_records.json'
    extractor.read_from_json(records_json)
    Biography.objects.bulk_create(
        [Biography(exp=record['exp']) for record in extractor.records]
    )


def storage_sites():

    excludes = ["/index.htm", "/index.html", "Sin_Ficha"]
    prevs = ["FichasAdministrativos", "FichasDefensores",
             "FichasJueMag", "FichasSecAct"]

    timestamp = "20090911141716"
    original_url = ("http://w3.cjf.gob.mx:80/sevie_page/Fichas/"
                    "AGUILAR_MORALES_LUIS_MARIA.html")
    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    response = requests.get(wayback_url)
    text = response.text
    soup = BeautifulSoup(text, 'html.parser')
    # delete all content betweet <!-- BEGIN WAYBACK TOOLBAR INSERT -->
    # and <!-- END WAYBACK TOOLBAR INSERT -->
    for tag in soup.find_all("script"):
        tag.decompose()

    only_text = soup.get_text()


def other_storages_sites():

    examples = [
        "http://w3.cjf.gob.mx:80/sevie_page/Busquedas/Consultas/index_Ficha.asp?exp=13086&rutaFichas=FichasSecAct"
        "http://w3.cjf.gob.mx/sevie_page/Busquedas/Consultas/index_ficha.asp?exp=631&rutaFichas=FichasJueMag",
    ]
    exclusions = [
        "http://w3.cjf.gob.mx:80/sevie_page/Busquedas/Consultas/botones.asp?exp=5851&rutaFichas=FichasSecAct",
    ]


def save_plain_in_model():
    from oej.models import Biography
    items = [
        ("2023", "DÍAZ DE LEÓN D HERS ELVIA ROSA"),
        ("5328", "ARAGÓN MENDÍA ADOLFO O."),
        ("25292", "AGUINACO ALEMAN JOSE VICENTE"),
        ("973", "AGUILAR MORALES LUIS MARÍA"),
        ("142", "AZUELA GÜITRÓN MARIANO"),
        ("10734", "BORBOA REYES ALFREDO"),
        ("38335", "BARQUIN ÁLVAREZ MANUEL"),
        ("15338", "CARRASCO DAZA CONSTANCIO"),
        ("4172", "GALVÁN VILLAGÓMEZ ALONSO"),
        ("2336", "GONGORA PIMENTEL GENARO DAVID"),
        ("12987", "HERRERA TELLO MARÍA TERESA"),
        ("15074", "INFANTE GONZALES INDALFER"),
        ("2118", "LUNA RAMOS MARGARITA BEATRIZ"),
        ("30601", "LARA PONTE RODOLFO HECTOR"),
        ("960", "MARTÍNEZ GONZALEZ HILDA CECILIA"),
        ("790", "MARROQUÍN ZALETA JAIME MANUEL"),
        ("3493", "MARTÍN ARGUMOSA MARÍA CONCEPCIÓN ELISA"),
        ("25388", "MELGAR ADALID MARIO"),
        ("25387", "MÉNDEZ SILVA RICARDO"),
        ("20265", "OÑATE LABORDE ALFONSO"),
        ("7077", "PALLARES VALDEZ RAÚL ARMANDO"),
        ("52292", "QUIRÓS PÉREZ MIGUEL A."),
        ("38336", "SANCHEZ BRINGAS ENRIQUE"),
        ("3717", "TORRES MORALES GUADALUPE"),
        ("6902", "VELASCO VILLAVICENCIO ANTONIA HERLINDA"),
        ("364", "VARGAS CHÁVEZ LUIS GILBERTO"),
        ("38334", "VALLS HERNÁNDEZ SERGIO ARMANDO"),
    ]
    Biography.objects.bulk_create(
        [Biography(exp=exp, full_name=name, ruta="plain")
         for exp, name in items]
    )



