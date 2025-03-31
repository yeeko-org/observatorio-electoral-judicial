import json
import os
import re
from oej.models import Position, Seat, Candidate
from geo.models import Body, Power


class LoadCandidates:

    def __init__(self):
        self.data = []
        self.position: Position | None = None
        pass

    def load_base_data(self):
        powers = [
            {"key_name": "PE", "name": "Poder Ejecutivo", "icon": "account_balance"},
            {"key_name": "PJ", "name": "Poder Judicial", "icon": "balance"},
            {"key_name": "PL", "name": "Poder Legislativo", "icon": "history_edu"},
            {"key_name": "EF", "name": "En Funciones", "icon": "gavel"}
        ]
        for power in powers:
            try:
                power_obj = Power.objects.get(key_name=power["key_name"])
                for key, value in power.items():
                    setattr(power_obj, key, value)
                power_obj.save()
            except Power.DoesNotExist:
                power_obj = Power.objects.create(**power)
        bodies = [
            {
                "name": "Suprema Corte de Justicia de la Nación",
                "short_name": "SCJN"
            },
            {
                "name": "Tribunal Electoral del Poder Judicial de la Federación",
                "short_name": "TEPJF"
            },
            {
                "name": "Tribunal de Disciplina Judicial",
                "short_name": "TDJ"
            },
            {
                "name": "Distritos Judiciales Federales",
                "short_name": "DJF"
            },
            {
                "name": "Magistrados de Circuito",
                "short_name": "MC"
            },
        ]
        # Body.objects.bulk_create([Body(**body) for body in bodies])
        for body in bodies:
            try:
                body_obj = Body.objects.get(short_name=body["short_name"])
                for key, value in body.items():
                    setattr(body_obj, key, value)
                body_obj.save()
            except Body.DoesNotExist:
                body_obj = Body.objects.create(**body)

        positions = [
            {
                "full_name": "Ministras y Ministros de la Suprema Corte de Justicia de la Nación",
                "name": "de la Suprema Corte de Justicia de la Nación",
                "short_name": "SCJN",
                "male_name": "Ministro",
                "female_name": "Ministra",
                "body": "SCJN",
                "is_national": True,
                "color": "#8681d3",
                "color_light": "#cac6eb",
            },
            {
                "full_name": "Magistraturas del Tribunal de Disciplina Judicial",
                "name": "del Tribunal de Disciplina Judicial",
                "short_name": "TDJ",
                "male_name": "Magistrado",
                "female_name": "Magistrada",
                "body": "TDJ",
                "is_national": True,
                "color": "#80c7bc",
                "color_light": "#dcefeb",
            },
            {
                "full_name": "Magistraturas de la Sala Superior del TEPJF*",
                "name": "del Tribunal Electoral del Poder Judicial de la Federación (TEPJF)",
                "short_name": "Sala Superior TEPJF",
                "male_name": "Magistrado",
                "female_name": "Magistrada",
                "body": "TEPJF",
                "sub_body": "Sala Superior",
                "is_national": True,
                "color": "#397c9a",
                "color_light": "#bbd5de",
            },
            {
                "full_name": "Magistraturas de las Salas Regionales del TEPJF*",
                "name": "del Tribunal Electoral del Poder Judicial de la Federación (TEPJF)",
                "short_name": "Sala Regional TEPJF",
                "male_name": "Magistrado",
                "female_name": "Magistrada",
                "body": "TEPJF",
                "sub_body": "Sala Regional",
                "by_circunscription": True,
                "color": "#f8c6b8",
                "color_light": "#feeae7",
            },
            {
                "full_name": "Magistraturas de Circuito",
                "name": "de Circuito",
                "short_name": "Magistraturas de Circuito",
                "male_name": "Magistrado",
                "female_name": "Magistrada",
                "body": "MC",
                "is_national": False,
                "by_circuit": True,
                "color": "#c08ba5",
                "color_light": "#eddee5",
            },
            {
                "full_name": "Juezas y Jueces de Distrito",
                "name": "de Distrito",
                "short_name": "Juezas y Jueces",
                "male_name": "Juez",
                "female_name": "Jueza",
                "body": "DJF",
                "is_national": False,
                "by_circuit": True,
                "color": "#ffe365",
                "color_light": "#fffae6",
            }
        ]
        for position in positions:
            body = Body.objects.get(short_name=position.pop("body"))
            position["body"] = body
            try:
                position_obj = Position.objects.get(short_name=position["short_name"])
                for key, value in position.items():
                    setattr(position_obj, key, value)
                position_obj.save()
            except Position.DoesNotExist:
                position_obj = Position.objects.create(**position)
            if not position.get("by_circunscription", False):
                Seat.objects.get_or_create(position=position_obj)
        for circ in range(1, 6):
            position = Position.objects.get(short_name="Sala Regional TEPJF")
            Seat.objects.get_or_create(
                position=position, circunscription_id=circ)

    # def reset_base_data(self):
    #     Power.objects.all().delete()
    #     Body.objects.all().delete()
    #     Position.objects.all().delete()
    #     Seat.objects.all().delete()

    # def reset_candidates(self):
    #     Candidate.objects.all().delete()

    def read_from_json(self, filename, position_short_name):
        self.position = Position.objects.get(short_name=position_short_name)
        try:
            print(f"Records loaded from {filename}.")
            with open(filename, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
                return self.data
        except IOError as e:
            print(f"Error loading records from {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error loading from {filename}: {e}")

    def save_candidates(self):
        from oej.cards.examples import get_find_names
        candidates = []
        for record in self.data:
            powers = record.get("Poder", "").strip()
            if not powers:
                print("No powers found")
                continue
            all_powers = powers.split(",")
            all_powers = [p.strip() for p in all_powers]
            powers_obj = Power.objects.filter(key_name__in=all_powers)
            sex = record.get("Sexo", "").strip()
            if sex in ["M", "H"]:
                final_sex = "Hombre" if sex == "H" else "Mujer"
            else:
                final_sex = None
                print(f"Sexo no reconocido {sex}")
            seats = Seat.objects.filter(position=self.position)
            if self.position.by_circunscription:
                seat = seats.get(circunscription=record["page"])
            else:
                seat = seats.first()
            first_name = record["Nombre(s)"]
            final_names = get_find_names(first_name)

            candidate = Candidate.objects.create(
                first_name=first_name,
                last_name_1=record["Apellido paterno"],
                last_name_2=record["Apellido materno"],
                find_names=final_names,
                sex=final_sex,
                seat=seat,
            )
            candidate.powers.set(powers_obj)

        # Candidate.objects.bulk_create(candidates)


# if __name__ == "__main__":
def main_load(collections=None):
    if collections is None:
        collections = [
            {
                "body_short_name": "SCJN",
                "json_file": "scjn.json"
            },
            {
                "body_short_name": "Sala Superior TEPJF",
                "json_file": "magis_te.json"
            },
            {
                "body_short_name": "Sala Regional TEPJF",
                "json_file": "magis_reg.json"
            }
        ]

    common_path = "G:\Mi unidad\YEEKO\Proyectos\oej\listas"
    for collection in collections:
        output_json = os.path.join(common_path, collection["json_file"])
        extractor = LoadCandidates()
        name = collection["body_short_name"]
        extractor.read_from_json(output_json, name)
        extractor.save_candidates()


def init_load():
    extractor = LoadCandidates()
    extractor.load_base_data()

