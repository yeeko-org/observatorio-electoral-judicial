import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin
from oej.models import ProfessionalLicense, Candidate


class CedulaProfesionalFinder:
    """
    A class to search for professional licenses (cédulas profesionales)
    using the Registro Nacional de Profesionistas website.
    """

    def __init__(
            self,
            base_url="https://www.cedulaprofesional.sep.gob.mx/cedula/",
            candidate: Candidate | None = None
    ):
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
        self.candidate: Candidate | None = candidate
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

    def search_by_name(self, candidate: Candidate):
        """
        Search for a professional license by name.

        Args:
            candidate: A Candidate object with the first name and last names
            of the person.
        """
        self.candidate = candidate
        search_page = self._get_search_page()
        if not search_page:
            return { "success": False, "error": "Failed to access search page" }

        # Prepare the search data in the format expected by the server
        second = candidate.last_name_2.upper() if candidate.last_name_2 else ""
        find_names = candidate.find_names
        all_licences = []
        unique_ids = set()
        some_is_exact = False
        for first_name in find_names:
            search_json = {
                "maxResult": "1000",
                "nombre": first_name.upper(),
                "paterno": candidate.last_name_1.upper(),
                "materno": second,
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

            new_licences = self._try_search_endpoint(search_endpoint, search_data)

            if not new_licences:
                self.logger.error(f"No licenses found for {candidate}")
                return
            for licence in new_licences:
                if licence["id_licence"] in unique_ids:
                    continue
                unique_ids.add(licence["id_licence"])
                licence["candidate"] = candidate
                other_data = licence.get("other_data", {})
                name = other_data.get("nombre", "")
                # licence["is_exact"] = name == candidate.first_name
                is_exact = name == candidate.first_name
                licence["is_exact"] = is_exact
                if is_exact:
                    some_is_exact = True
                all_licences.append(licence)
            time.sleep(1)
        if some_is_exact:
            all_licences = [licence for licence in all_licences
                            if licence["is_exact"]]

        ProfessionalLicense.objects.bulk_create(
            [ProfessionalLicense(**licence) for licence in all_licences]
        )
        self.logger.info(f"Found {len(all_licences)} licenses for {candidate}")

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

            # self.logger.info(f"Response status: {response.status_code}")
            # self.logger.info(f"Response headers: {response.headers}")
            # When debugging, output the first part of the response content
            # content_snippet = response.text[:500]
            # self.logger.info(f"Response content (first 500 chars): {content_snippet}")

            if response.status_code != 200:
                self.logger.error(f"Search request failed: HTTP {response.status_code}")
                return []

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
            return []

    def _parse_json_results(self, json_data):
        """Parse JSON results from the API"""
        # self.logger.info(f"Parsing JSON response: {json_data}")

        licenses = []

        # The API sometimes returns the data in different formats
        # Try different potential structures
        items = json_data.get('items', [])
        if not items and isinstance(json_data, list):
            items = json_data

        if not items:
            self.logger.warning("No items found in JSON response")
            return []

        for item in items:
            other_data = {
                'nombre': item.get('nombre'),
                'paterno': item.get('paterno'),
                'materno': item.get('materno'),
                'genero': item.get('sexo'),
            }
            title = item.get('titulo')
            license_info = {
                'id_licence': item.get('idCedula'),
                'year': item.get('anioreg'),
                'institution': item.get('desins'),
                'licence_type': item.get('tipo'),
                'other_data': other_data
            }
            license_info = self.add_title(license_info, title)
            licenses.append(license_info)

        return licenses

    def _parse_html_results(self, html_content):
        """Parse HTML response to extract license information"""
        self.logger.info("Parsing HTML response")

        soup = BeautifulSoup(html_content, 'html.parser')
        licenses = []

        # Check if there's an error message
        error_div = soup.find('div', class_='alert-danger')
        if error_div and error_div.get_text():
            error_msg = error_div.get_text().strip()
            self.logger.error(f"Error message: {error_msg}")
            return []

        # Look for grid content if detail view isn't available
        grid_container = soup.find(id='cedulasGrid')
        if grid_container:
            # Try to extract data from the grid
            rows = grid_container.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 9:
                    other_data = {
                        "nombre": cells[1].get_text().strip(),
                        'paterno': cells[2].get_text().strip(),
                        'materno': cells[3].get_text().strip(),
                        "genero": cells[4].get_text().strip(),
                    }
                    title = cells[5].get_text().strip()
                    license_info = {
                        'id_licence': cells[0].get_text().strip(),
                        'year': cells[6].get_text().strip(),
                        'institution': cells[7].get_text().strip(),
                        'licence_type': cells[8].get_text().strip(),
                        'other_data': other_data
                    }
                    license_info = self.add_title(license_info, title)
                    licenses.append(license_info)

        return licenses

    def add_title(self, licence_info, title):
        """Add title components to the license information"""
        inits = ["COMO", "EN", "DE"]
        for init in inits:
            if f" {init} " in title:
                level, career = title.split(f" {init} ", 1)
                licence_info["level"] = level
                licence_info["career"] = career
                break
        licence_info["title"] = title
        return licence_info

    def get_bulk_results(self, candidates):
        self.logger.info(f"Processing bulk search for "
                         f"{candidates.count()} people")

        for candidate in candidates:
            self.search_by_name(candidate)


def search_candidates():
    candidates = Candidate.objects.filter(licenses__isnull=True)\
        .distinct()
    finder = CedulaProfesionalFinder()
    finder.get_bulk_results(candidates)


def update_titles():
    # licenses = ProfessionalLicense.objects.filter(career__isnull=True)
    licenses = ProfessionalLicense.objects.all()
    finder = CedulaProfesionalFinder()
    for license in licenses:
        title = license.title
        licence_info = finder.add_title({}, title)
        license.career = licence_info.get("career")
        license.level = licence_info.get("level")
        license.save()
