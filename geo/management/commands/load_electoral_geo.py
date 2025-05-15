import csv
from django.core.management.base import BaseCommand

from geo.models import (
    Section, State, Circunscription, JudicialElectoralDistrict)
import json


class Command(BaseCommand):
    help = 'Load geo electoral data'

    def handle(self, *args, **options):

        sections = LoadSections()


class LoadSections:

    sections = []
    states_ids = {}
    batch_size = 5000
    errors = []

    def __init__(self):
        self.section_data = {}
        self.load_json("geo/geo_files/secciones.json")
        # self.set_circunscription()
        # self.load_district_id()
        # self.bulk_create()

    def load_json(self, file_path):
        print("Loading geo data")
        with open(file_path, encoding='utf-8') as jsonfile:
            self.section_data = json.load(jsonfile)

    def prepare_sections(self):
        print("Preparing sections")
        sections = self.section_data.get("secciones", [])
        for section in sections:
            pass
            try:
                section = Section(

                )
                self.sections.append(section)
            except Exception as e:
                self.errors.append(
                    f"Error creating section {section}: {e}")

    def set_circunscription(self):
        states = self.section_data.get("estados", [])
        for state in states:
            state_obj = State.objects.get(id=state['idEstado'])
            circ_id = state.get("idCircunscripcion")
            circunscription = Circunscription.objects.get(id=circ_id)
            state_obj.circunscription = circunscription
            state_obj.save()

    def create_judicial_electoral_district(self):
        """
        Create JudicialElectoralDistrict instances from the loaded data.
        """
        print("Creating JudicialElectoralDistrict instances")
        sections = self.section_data.get("secciones", [])
        all_jed_by_state = {state_id: {} for state_id in range(1, 33)}
        for section in sections:
            federal_district = section.get("idDistritoFederal")
            judicial_district = section.get("idDistritoJudicial")
            state_id = section.get("idEstado")
            all_jed_by_state[state_id].setdefault(
                judicial_district, set()
            )
            all_jed_by_state[state_id][judicial_district].add(
                federal_district
            )
        # print("all_jed", all_jed)
        return all_jed_by_state

    def explore_by_federal(self):
        """
        Create JudicialElectoralDistrict instances from the loaded data.
        """
        print("Creating JudicialElectoralDistrict instances")
        sections = self.section_data.get("secciones", [])
        all_jed_by_state = {state_id: {} for state_id in range(1, 33)}
        for section in sections:
            federal_district = section.get("idDistritoFederal")
            judicial_district = section.get("idDistritoJudicial")
            state_id = section.get("idEstado")
            all_jed_by_state[state_id].setdefault(
                federal_district, set()
            )
            all_jed_by_state[state_id][federal_district].add(
                judicial_district
            )
        # print("all_jed", all_jed)
        return all_jed_by_state

    def load_district_id(self):
        """
        Load the district ID from the JSON file.
        """
        sections = self.section_data.get("secciones", [])
        all_states = {}
        for section in sections:
            circuit_id = section.get("idCircuito")
            state_id = section.get("idEstado")
            all_states.setdefault(state_id, circuit_id)
        for state_id, circuit in all_states.items():
            state = State.objects.get(id=state_id)
            state.circuit = circuit
            state.save()

    def bulk_create(self):
        print("Bulk creating municipalities")
        for i in range(0, len(self.sections), self.batch_size):
            print(f"Creating sections from {i} to {i + self.batch_size}")
            Section.objects.bulk_create(
                self.sections[i:i + self.batch_size])


def load_district_id():
    load = LoadSections()
    all_oej = load.create_judicial_electoral_district()
    for state_id, judicial_districts in all_oej.items():
        print(f"-" * 20)
        print(f"State ID: {state_id}")
        for judicial_district, federal_districts in judicial_districts.items():
            print(f"  Judicial District: {judicial_district}")
            print(f"    Federal Districts: {federal_districts}")
            # for federal_district in federal_districts:
            #     judicial_electoral_district = JudicialElectoralDistrict(
            #         state_id=state_id,
            #         judicial_district=judicial_district,
            #         federal_district=federal_district
            #     )
            #     judicial_electoral_district.save()

    federal_districts = load.explore_by_federal()
    for state_id, federal_districts in federal_districts.items():
        print(f"-" * 20)
        print(f"State ID: {state_id}")
        for federal_district, judicial_districts in federal_districts.items():
            print(f"  Federal District: {federal_district}")
            print(f"    Judicial Districts: {judicial_districts}")

