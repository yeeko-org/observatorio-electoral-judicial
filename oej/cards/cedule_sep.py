import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin


class CedulaProfesionalFinder:
    """
    A class to search for professional licenses (cédulas profesionales)
    using the Registro Nacional de Profesionistas website.
    """

    def __init__(self, base_url="https://www.cedulaprofesional.sep.gob.mx/cedula/"):
        """
        Initialize the finder with the base URL of the search page.

        Args:
            base_url: The base URL of the professional license website
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "es,es-ES;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.cedulaprofesional.sep.gob.mx",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty"
        }
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Set up a logger for this class"""
        logger = logging.getLogger('CedulaProfesionalFinder')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _get_search_page(self):
        """Get the search page and extract necessary cookies and tokens"""
        search_url = urljoin(self.base_url, "presidencia/indexAvanzada.action")
        self.logger.info(f"Getting search page: {search_url}")

        try:
            response = self.session.get(
                search_url,
                headers={
                    "User-Agent": self.headers["User-Agent"],
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": self.headers["Accept-Language"]
                }
            )
            response.raise_for_status()

            # Update referer header for subsequent requests
            self.headers["Referer"] = search_url

            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error accessing search page: {e}")
            return None

    def search_by_name(self, first_name, first_last_name, second_last_name=""):
        """
        Search for a professional license by name.

        Args:
            first_name: First name of the person
            first_last_name: First last name of the person
            second_last_name: Second last name of the person (optional)

        Returns:
            A dictionary with the search results or error message
        """
        # Get the search page first to set up cookies and session
        search_page = self._get_search_page()
        if not search_page:
            return { "success": False, "error": "Failed to access search page" }

        # Prepare the search data in the format expected by the server
        search_json = {
            "maxResult": "1000",
            "nombre": first_name.upper(),
            "paterno": first_last_name.upper(),
            "materno": second_last_name.upper() if second_last_name else "",
            "idCedula": ""
        }

        # Format data as expected by the server (json parameter with JSON string value)
        search_data = {
            "json": json.dumps(search_json)
        }

        # Log the exact payload being sent
        self.logger.info(f"Search payload: {search_data}")

        # The search endpoint
        search_endpoint = urljoin(self.base_url, "buscaCedulaJson.action")

        return self._try_search_endpoint(search_endpoint, search_data)

    def _try_search_endpoint(self, endpoint, data):
        """Try to search using the given endpoint"""
        self.logger.info(f"Trying search endpoint: {endpoint}")

        try:
            response = self.session.post(
                endpoint,
                data=data,  # This is now properly formatted
                headers=self.headers,
                timeout=15
            )

            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response headers: {response.headers}")

            # When debugging, output the first part of the response content
            content_snippet = response.text[:500]
            self.logger.info(f"Response content (first 500 chars): {content_snippet}")

            if response.status_code != 200:
                self.logger.error(f"Search request failed: HTTP {response.status_code}")
                return { "success": False, "error": f"HTTP error {response.status_code}" }

            # Try to parse as JSON first
            try:
                result = response.json()
                return self._parse_json_results(result)
            except ValueError:
                self.logger.warning("Response is not JSON, trying to parse as HTML")
                # If not JSON, try to parse as HTML
                return self._parse_html_results(response.text)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            return { "success": False, "error": str(e) }

    def _parse_json_results(self, json_data):
        """Parse JSON results from the API"""
        self.logger.info(f"Parsing JSON response: {json_data}")

        licenses = []

        # The API sometimes returns the data in different formats
        # Try different potential structures
        items = json_data.get('items', [])
        if not items and isinstance(json_data, list):
            items = json_data

        if not items:
            self.logger.warning("No items found in JSON response")
            return { "success": True, "results": [] }

        for item in items:
            license_info = {
                'id_cedula': item.get('idCedula'),
                'nombre': item.get('nombre'),
                'paterno': item.get('paterno'),
                'materno': item.get('materno'),
                'genero': item.get('sexo'),
                'profesion': item.get('titulo'),
                'anio_expedicion': item.get('anioreg'),
                'institucion': item.get('desins'),
                'tipo': item.get('tipo')
            }
            licenses.append(license_info)

        return { "success": True, "results": licenses }

    def _parse_html_results(self, html_content):
        """Parse HTML response to extract license information"""
        self.logger.info("Parsing HTML response")

        soup = BeautifulSoup(html_content, 'html.parser')
        licenses = []

        # Check if there's an error message
        error_div = soup.find('div', class_='alert-danger')
        if error_div and error_div.get_text():
            error_msg = error_div.get_text().strip()
            return { "success": False, "error": error_msg }

        # Try to find results in detail sections
        id_cedula = soup.find(id='detalleCedula')
        nombre = soup.find(id='detalleNombre')
        genero = soup.find(id='detalleGenero')
        profesion = soup.find(id='detalleProfesion')
        fecha = soup.find(id='detalleFecha')
        institucion = soup.find(id='detalleInstitucion')
        tipo = soup.find(id='detalleTipo')

        if id_cedula and nombre:
            nombre_text = nombre.get_text().strip()
            license_info = {
                'id_cedula': id_cedula.get_text().strip(),
                'nombre': nombre_text,
                'genero': genero.get_text().strip() if genero else "",
                'profesion': profesion.get_text().strip() if profesion else "",
                'anio_expedicion': fecha.get_text().strip() if fecha else "",
                'institucion': institucion.get_text().strip() if institucion else "",
                'tipo': tipo.get_text().strip() if tipo else ""
            }
            licenses.append(license_info)

        # Look for grid content if detail view isn't available
        grid_container = soup.find(id='cedulasGrid')
        if grid_container:
            # Try to extract data from the grid
            rows = grid_container.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 9:
                    license_info = {
                        'id_cedula': cells[0].get_text().strip(),
                        'nombre': cells[1].get_text().strip(),
                        'paterno': cells[2].get_text().strip(),
                        'materno': cells[3].get_text().strip(),
                        'genero': cells[4].get_text().strip(),
                        'profesion': cells[5].get_text().strip(),
                        'anio_expedicion': cells[6].get_text().strip(),
                        'institucion': cells[7].get_text().strip(),
                        'tipo': cells[8].get_text().strip()
                    }
                    licenses.append(license_info)

        return { "success": True, "results": licenses } if licenses else { "success": True, "results": [] }

    def get_bulk_results(self, people_list):
        """
        Process a list of people and get their license information.

        Args:
            people_list: A list of dictionaries containing 'first_name',
                       'first_last_name', and optionally 'second_last_name'

        Returns:
            A list of dictionaries with results for each person
        """
        self.logger.info(f"Processing bulk search for {len(people_list)} people")
        results = []

        for i, person in enumerate(people_list):
            self.logger.info(f"Processing person {i + 1}/{len(people_list)}")

            # Add a small delay between requests to avoid overloading the server
            if i > 0:
                time.sleep(2.5)

            first_name = person.get('first_name', '')
            first_last_name = person.get('first_last_name', '')
            second_last_name = person.get('second_last_name', '')

            license_info = self.search_by_name(
                first_name,
                first_last_name,
                second_last_name
            )

            results.append({
                'person': person,
                'license_info': license_info
            })

        return results


def main():
    # Create an instance of the finder
    finder = CedulaProfesionalFinder()

    # Search for a single person
    result = finder.search_by_name(
        first_name="IXEL",
        first_last_name="MENDOZA",
        second_last_name="ARAGON"
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # You can uncomment this to test bulk search
    """
    # Bulk search for multiple people
    people = [
        {
            'first_name': 'MARIA',
            'first_last_name': 'LOPEZ',
            'second_last_name': 'GARCIA'
        },
        {
            'first_name': 'CARLOS',
            'first_last_name': 'MARTINEZ',
            'second_last_name': 'HERNANDEZ'
        }
    ]

    bulk_results = finder.get_bulk_results(people)
    for result in bulk_results:
        print(f"Person: {result['person']}")
        print(f"License info: {result['license_info']}")
        print("-" * 50)
    """


if __name__ == "__main__":
    main()