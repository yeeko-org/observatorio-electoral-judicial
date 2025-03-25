import csv
from django.core.management.base import BaseCommand

from geo.models import Municipality
from utils.common import text_normalizer


class Command(BaseCommand):
    help = 'Load municipalities'

    def handle(self, *args, **options):

        municipios = LoadMunicipios()


class LoadMunicipios:
    municipalities = []
    states_ids = {}
    batch_size = 100
    errors = []

    def __init__(self):
        self.load_states()
        self.load_csv("geo/geo_files/municipios.csv")
        self.bulk_create()

    def load_csv(self, file_path):
        print("Loading municipalities")
        with open(file_path, newline='', encoding='latin1') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                inegi_code = row['CVE_MUN']
                state_inegi_code = row['CVE_ENT']
                state_id = self.states_ids.get(state_inegi_code)
                complete_code = f"{state_inegi_code}-{inegi_code}"
                name = row['NOM_MUN']
                std_name = text_normalizer(name)
                pob_total = row['POB_TOTAL'] or ""
                population = int(pob_total) if pob_total.isdigit() else None

                try:
                    municipality = Municipality(
                        inegi_code=inegi_code,
                        complete_code=complete_code,
                        name=name,
                        std_name=std_name,
                        state_id=state_id,
                        population=population
                    )
                    self.municipalities.append(municipality)
                except Exception as e:
                    self.errors.append(
                        f"Error creating municipality {inegi_code}: {e}")

    def load_states(self):
        print("Loading states")
        from geo.models import State
        for state in State.objects.all():
            self.states_ids[state.inegi_code] = state.pk

    def bulk_create(self):
        print("Bulk creating municipalities")
        for i in range(0, len(self.municipalities), self.batch_size):
            print(f"Creating municipalities from {i} to {i + self.batch_size}")
            Municipality.objects.bulk_create(
                self.municipalities[i:i + self.batch_size])
