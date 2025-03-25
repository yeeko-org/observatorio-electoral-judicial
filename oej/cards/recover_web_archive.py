from oej.models import Biography
import json

examples = [
    # "mx,gob,cjf,w3)/sevie_page/fichas/fichasadministrativos/24766.html",
    "http://w3.cjf.gob.mx/sevie_page/Fichas/FichasAdministrativos/24766.html",
    "http://w3.cjf.gob.mx:80/sevie_page/Fichas/FichasDefensores/10262.html"
    "http://w3.cjf.gob.mx:80/sevie_page/FichasSecAct/11512.html",
    "http://w3.cjf.gob.mx/sevie_page/Fichas/FichasJueMag/10009.html",
    "http://w3.cjf.gob.mx:80/sevie_page/FichasSecAct/11512.html",
    "http://w3.cjf.gob.mx:80/sevie_page/Fichas/AGUILAR_MORALES_LUIS_MARIA.html",
    "http://w3.cjf.gob.mx:80/sevie_page/Fichas/GONGORA_PIMENTEL_GENARO_DAVID.html",
    "http://w3.cjf.gob.mx:80/sevie_page/Fichas/JOSE_GUADALUPE_TAFOYA_HERNANDEZ.htm",
    "http://w3.cjf.gob.mx:80/sevie_page/fichas_page/Consultas/Fichas/10734.html"
]


class SiteRecover:

    def __init__(self):
        ready_exp = Biography.objects\
            .filter(exp__isnull=False).values_list("exp", flat=True)
        self.ready_exp = set(ready_exp)
        incomplete_exp = Biography.objects\
            .filter(exp__isnull=True).values_list("exp", flat=True)
        self.incomplete_exp = set(incomplete_exp)
        unique_bios = self.get_unique_bios()
        unique_bios = unique_bios.values()
        saved_bios = [bio for bio in unique_bios if bio["saved"]]
        new_bios = [bio for bio in unique_bios if not bio["saved"]]
        print(f"unique_bios: {len(unique_bios)}")
        print(f"saved_bios: {len(saved_bios)}")
        print("new_bios:", len(new_bios))
        self.saved_bios = saved_bios
        self.new_bios = new_bios
        self.save_bios(self.new_bios)

    def get_unique_bios(self):
        records = self.read_from_json()
        unique_bios = {}
        ready_bios = set()
        for page in records[1:]:
            if page[4] != "200":
                continue
            original_url = page[2]
            last_elem = original_url.split("/")[-1]
            if not last_elem.endswith(".html"):
                continue
            elem_id = last_elem.split(".")[0]
            try:
                int(elem_id)
            except ValueError:
                continue
            if elem_id in self.ready_exp:
                ready_bios.add(elem_id)
                continue
            timestamp = page[1]
            timestamp = int(timestamp)
            saved_bio = unique_bios.get(elem_id, {})
            if timestamp > saved_bio.get("timestamp", 0):
                route = "plain" if "fichas_page" in original_url else None
                unique_bios[elem_id] = {
                    "url": original_url,
                    "timestamp": timestamp,
                    "exp": elem_id,
                    "saved": elem_id in self.incomplete_exp,
                    "route": route
                }
        print(f"ready_bios: {len(ready_bios)}")
        return unique_bios

    def save_bios(self, bios: list):
        biographies = [
            Biography(
                exp=bio["exp"], recover_url=bio["url"],
                recover_timestamp=bio["timestamp"], ruta=bio["route"]
            ) for bio in bios
        ]
        Biography.objects.bulk_create(biographies)

    def read_from_json(self, filename='fixture/oej/storaged_bios.json'):
        try:
            print(f"Records loaded from {filename}.")
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except IOError as e:
            print(f"Error loading records from {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error loading from {filename}: {e}")


recovery = SiteRecover()


# Biography.objects.filter(recover_timestamp__isnull=False).delete()

