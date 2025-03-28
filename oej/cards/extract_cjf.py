import re
from bs4 import BeautifulSoup
from oej.models import Biography
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry
import time
import random
import logging


class BiographyExtractor:
    """
    Class for extracting biographical information from HTML pages about people
    who work in the judicial power in Mexico and saving it to the Biography model.
    """
    available_routes = [
        "FichasJueMag", "FichasSecAct", "FichasDefensores",
        "FichasAdministrativos"]
    last_route = "FichasJueMag"
    base_url = "https://w3.cjf.gob.mx/sevie_page"

    def __init__(self, biography=Biography, is_recovery=False):
        """
        Initialize the extractor with HTML content and optional parameters.

        Args:
            biography (Biography): The Biography model instance
        """
        self.biography = biography
        self.exp = biography.exp
        self.is_recovery = is_recovery
        if biography.html_content:
            self.content = biography.html_content
        elif is_recovery:
            self.content = self.get_html_content()
        elif biography.ruta == 'plain':
            url = (f'{self.base_url}/fichas_page/Consultas/Fichas/'
                   f'{self.exp}.html')
            self.content = self.get_html_content(url)
        else:
            self.content = self.get_html_content()
        self.soup = BeautifulSoup(self.content, 'html.parser')
        if is_recovery:
            self.clean_recovery_url()

    def get_html_content(self, url=None):
        if self.is_recovery:
            # wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
            url = (f"https://web.archive.org/web/"
                   f"{self.biography.recover_timestamp}id_/"
                   f"{self.biography.recover_url}")
        elif not url:
            url = f'{self.base_url}/Fichas/{self.last_route}/{self.exp}.html'
        response = requests.get(url, verify=False)
        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning)
        # response.raise_for_status()
        if response.status_code == 200:
            return response.text
        if not self.is_recovery:
            next_route = self.available_routes.index(self.last_route) + 1
            if next_route < len(self.available_routes):
                self.last_route = self.available_routes[next_route]
                return self.get_html_content()
        raise Exception(f"Error fetching URL: {url}")

    def clean_recovery_url(self):
        # Convert to string to handle regex operations
        html_content = str(self.soup)

        # Step 1: Remove everything between toolbar comments
        pattern = r'<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->'
        html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)

        html_content = re.sub(r'</html>.*$', '</html>', html_content, flags=re.DOTALL)

        # Parse back to BeautifulSoup to properly handle tag removal
        clean_soup = BeautifulSoup(html_content, 'html.parser')

        if clean_soup.head:
            clean_soup.head.extract()

        self.soup = clean_soup

    def extract_full_name(self):
        """Extract the full name from the HTML."""
        name_section = self.soup.find(
            'span', style=lambda s: s and 'font-weight: 700' in s)
        if name_section:
            name_font = name_section.find(
                'font', face='Arial',
                style=lambda s: s and 'font-size: 16pt' in s)
            if name_font:
                return name_font.text.strip()
        alt_name_section = self.soup.find(
            'font', face='Verdana', size='4')
        if alt_name_section:
            return alt_name_section.text.strip()
        return None

    def extract_last_update(self, header_text):
        """Extract the last update date from the HTML."""
        header_lines = header_text.split('\n')
        last_update = None
        for line in header_lines:
            if 'ÚLTIMA ACTUALIZACIÓN' in line.upper():
                last_update = line.split(':')[-1].strip()
                break
        return last_update or "Desconocida"

    def save_to_model(self) -> Biography:
        """
        Returns:
            Biography: The saved Biography model instance
        """
        all_text = self.soup.get_text(strip=True, separator='\n')
        all_text = re.sub(r'\t+', ' ', all_text)
        all_text = all_text.strip()
        inits = ["CURRICULUM VITAE", "Nació en"]
        header_text = ""
        curriculum_text = all_text
        for init in inits:
            if init in all_text:
                header_text, curriculum_text = all_text.split(init)
                curriculum_text = f'{init}{curriculum_text}'
                break
        if "Última actualización" in curriculum_text:
            curriculum_text = curriculum_text.split("Última actualización")[0]

        if not self.biography.full_name:
            self.biography.full_name = self.extract_full_name()
        if not self.biography.html_content:
            self.biography.html_content = self.content
        self.biography.curriculum = curriculum_text
        if not self.biography.ruta:
            self.biography.ruta = self.last_route
        last_update = self.extract_last_update(header_text)
        if not last_update:
            last_update = self.extract_last_update(curriculum_text)
        self.biography.last_update = last_update

        self.biography.save()

        return self.biography


# if __name__ == "__main__":
def easy_extract():
    pending_bios = Biography.objects.filter(html_content__isnull=True)
    # for bio in pending_bios[:200]:
    for (idx, bio) in enumerate(pending_bios):
        if idx % 200 == 0:
            print(f"Processing biography {idx + 1} to {idx + 200}")
        try:
            extractor = BiographyExtractor(biography=bio)
            biography = extractor.save_to_model()
        except Exception as e:
            print(f"Error processing biography {bio.exp}: {e}")


def extract_historic():
    import time
    from django.utils import timezone
    from random import randint
    pending_bios = Biography.objects.filter(
        recover_timestamp__isnull=False, html_content__isnull=True)\
        .order_by('-recover_timestamp')
    print(f"Starting at {timezone.now()}")
    time.sleep(320)
    start_time = timezone.now()
    # for (idx, bio) in enumerate(pending_bios[:100]):
    for (idx, bio) in enumerate(pending_bios):
        if idx % 5 == 0:
            print(f"...Processing biography {idx + 1} to {idx + 5}")
        try:
            extractor = BiographyExtractor(bio, is_recovery=True)
            biography = extractor.save_to_model()
        except Exception as e:
            print(f"Error processing biography {bio.exp}: {e}")
            time.sleep(320)
        if idx % 15 == 0:
            time.sleep(60)
        time.sleep(randint(5, 8))

    end_time = timezone.now()
    duration = end_time - start_time
    print(f"Finished at {timezone.now()} in {duration}")

def drop_historic():
    Biography.objects\
        .filter(recover_timestamp__isnull=False, html_content__isnull=False)\
        .update(html_content=None, curriculum=None, full_name=None)


class KeepAlive:

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # List of common user agents to rotate
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    ]

    def __init__(self):
        pass


    def get_random_user_agent(self):
        """Return a random user agent."""
        return random.choice(self.USER_AGENTS)

    def create_session_with_retries(self):
        """Create a session with retry capabilities."""
        session = requests.Session()

        # Configure retry strategy
        retries = Retry(
            total=3,  # Total number of retries
            backoff_factor=2,  # Exponential backoff factor
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        )

        # Apply retry strategy to both http and https
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))

        return session

    def fetch_archived_page(self, recovery_timestamp, recovery_url, session=None):
        """Fetch a single archived page."""
        if session is None:
            session = self.create_session_with_retries()

        # Construct the Wayback Machine URL
        wayback_url = f"https://web.archive.org/web/{recovery_timestamp}id_/{recovery_url}"

        # Set headers with a random user agent
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        }

        try:
            self.logger.info(f"Fetching: {wayback_url}")
            response = session.get(wayback_url, headers=headers, timeout=30)

            # Check if the request was successful
            if response.status_code == 200:
                self.logger.info(f"Successfully fetched {wayback_url}")
                return True, response.text
            else:
                self.logger.warning(f"Failed to fetch {wayback_url}. Status code: {response.status_code}")
                return False, f"HTTP Error: {response.status_code}"

        except Exception as e:
            self.logger.error(f"Error fetching {wayback_url}: {str(e)}")
            return False, f"Exception: {str(e)}"

    def scrape_archived_pages(self, examples):
        """Scrape multiple archived pages with anti-blocking measures."""
        results = []
        session = self.create_session_with_retries()

        for i, example in enumerate(examples):
            # Extract the required information
            recovery_timestamp = example.get('recovery_timestamp')
            recovery_url = example.get('recovery_url')

            # Fetch the archived page
            success, content = self.fetch_archived_page(
                recovery_timestamp, recovery_url, session)

            # Store the result
            result = {
                **example,
                'success': success,
                'content': content if success else None,
                'error': None if success else content
            }
            results.append(result)

            # Log progress
            self.logger.info(f"Processed {i + 1}/{len(examples)} - "
                             f"{'Success' if success else 'Failed'}")

            # Add delays between requests to avoid being blocked
            if i < len(examples) - 1:
                if (i + 1) % 3 == 0:
                    # Longer delay every 3 requests
                    delay = random.uniform(10, 15)
                    self.logger.info(
                        f"Taking a longer break for {delay:.2f} seconds...")
                else:
                    # Normal delay between requests
                    delay = random.uniform(3, 7)
                    self.logger.info(f"Waiting for {delay:.2f} seconds...")
                time.sleep(delay)

        return results

    # Example usage
    def main(self):
        examples = [
            {
                "recovery_timestamp": "20030903002103",
                "recovery_url": "http://w3.cjf.gob.mx:80/sevie_page/Busquedas/Consultas/botones.asp?exp=3662&rutaFichas=FichasSecAct",
            },
            # Add other examples here
        ]

        results = self.scrape_archived_pages(examples)

        # Print summary
        success_count = sum(1 for r in results if r['success'])
        self.logger.info(f"Scraping completed: {success_count}/{len(results)} pages successfully scraped")

        # Process the results as needed
        # For example, save to files, database, etc.


def simple_explore():
    url = "https://www.cedulaprofesional.sep.gob.mx/cedula/presidencia/indexAvanzada.action"
    response = requests.get(url)
    text = response.text


