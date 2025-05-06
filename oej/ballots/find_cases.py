import json

from matplotlib.style.core import available

from oej.cards.load_candidates import LoadCandidates
from django.conf import settings
from oej.models import Seat, Position, Candidate
from geo.models import JudicialElectoralDistrict


class ResearchCases(LoadCandidates):
    ine_path = 'https://candidaturaspoderjudicial.ine.mx/cycc'
    positions = [
        {
            "acronym": "mmtcca",
            "body": "MC",
            "short_name": "Magistraturas de Circuito",
            "pos": None,
            "json_file": "magistraturas.json"
        },
        {
            "acronym": "jjd",
            "body": "DJF",
            "short_name": "Juezas y Jueces",
            "pos": None,
            "json_file": "jueces_distrito.json",
        }
    ]
    sexs = [
        {
            "gender": "m",
            "plural": "hombres",
            "name": "Hombre",
        },
        {
            "gender": "f",
            "plural": "mujeres",
            "name": "Mujer",
        }
    ]

    def __init__(self):
        from oej.ballots.simulator import ElectionSimulator
        super().__init__()
        self.base_path = "fixture/all_distritos.json"
        self.data = {}
        self.candidates_dict = {}
        self.all_districts = []
        self.pos_dict = { }
        self.district = None
        self.saved_candidates = {}
        self.positions_obj = Position.objects.filter(by_circuit=True)
        self.simulator = ElectionSimulator(False)


    def save_candidates(self):
        import requests
        # "https://practicatuvotopj.ine.mx/entities/4.json"
        base_url = "https://practicatuvotopj.ine.mx/entities"
        for i in range(1, 33):
            url = f"{base_url}/{i}.json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                distrites = data.get("distritos", [])
                self.all_districts.extend(distrites)
            else:
                print(f"Error: {response.status_code}")

        with open(self.base_path, "w", encoding="utf-8") as file:
            json.dump(self.all_districts, file, ensure_ascii=False, indent=4)

    def pre_load(self):
        from geo.models import Anomaly
        from oej.models import Body
        for position in self.positions:
            body = Body.objects.get(short_name=position["body"])
            pos = Position.objects.get(body=body)
            pos.acronym = position["acronym"]
            pos.save()
            position["pos"] = pos
        anomalies = [
            {
                "key_name": "same_quantity",
                "name": "Misma cantidad de cargos y candidaturas",
            },
            {
                "key_name": "double_tie",
                "name": "Doble empate",
                "description": "1 cargo, pero 1 casilla y 1 candidato por cada sexo",
            },
            {
                "key_name": "winner",
                "name": "Victoria asegurada",
                "description": "Hay 1, 2 o 3 cargos, 1 candidato y una casilla "
                               "de un sexo y más de 1 del otro sexo.",
            },
            {
                "key_name": "looser",
                "name": "Derrota asegurada",
                "description": (
                    "El escenario anterior con solo 1 cargo disponible y "
                    "varios competidores de un sexo y solo uno del otro."),
            },
            {
                "key_name": "easy_victory",
                "name": "Victoria por cantidad",
                "description": "Ganará porque hay pocas personas de su sexo"
                               " y muchos del otro sexo",
            },
            {
                "key_name": "hard_victory",
                "name": "Derrota por cantidad",
                "description": "Perderá porque hay muchas personas de su sexo "
                               "y pocas del otro sexo",
            },
            {
                "key_name": "forced_looser",
                "name": "Derrota forzada",
                "description": "Perderá por reglas de paridad de género",
            }
        ]
        for anomaly in anomalies:
            try:
                anomaly_ob = Anomaly.objects.get(key_name=anomaly["key_name"])
            except Anomaly.DoesNotExist:
                anomaly_ob = Anomaly(key_name=anomaly["key_name"])
            anomaly_ob.name = anomaly["name"]
            anomaly_ob.description = anomaly.get("description", "")
            anomaly_ob.save()



    def load_districts(self):
        import json
        with open(self.base_path, "r", encoding="utf-8") as file:
            self.all_districts = json.load(file)

    def process_all_districts(self):
        by_circ_dist = set()
        for distrito in self.all_districts:
            circ_dist = f"{distrito['circuito']}-{distrito['distrito']}"
            if circ_dist not in by_circ_dist:
                by_circ_dist.add(circ_dist)
                print("-" * 20)
                print(f"{circ_dist}: {distrito['entidad']}")
                self.district = distrito
                self.process_district()

    def load_candidates(self):
        import os

        if settings.IS_LOCAL:
            common_path = "G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine"
        else:
            common_path = "fixture/oej/listas"

        for position in self.positions:
            output_json = os.path.join(common_path, position["json_file"])
            data = self.read_from_json(
                output_json, position["short_name"])
            candidates = data.get("candidatos", [])
            for candidate in candidates:
                id_ine = candidate.get("idCandidato")
                self.candidates_dict[id_ine] = candidate
        self.saved_candidates = {
            c.id_ine: c for c in Candidate.objects.all()}

    def process_district(self):

        # colores_plural_acronym
        # cargos_plural_acronym
        # total_cargos_acronym
        # especialidades_acronym (list) --> "nombre", "cargos"
        circuit = self.district["circuito"]
        district = self.district["distrito"]
        jed, _ = JudicialElectoralDistrict.objects.get_or_create(
            circuit=circuit, number=district)
        self.district["jed"] = jed
        for position in self.positions:
            self.position = position
            print(f"Processing {position['acronym']}")
            acronym = position["acronym"]
            specialties = self.district.get(f"especialidades_{acronym}", [])
            for (idx, specialty) in enumerate(specialties):
                self.process_specialty(specialty, idx)

    def process_specialty(self, specialty, idx):
        from geo.models import Topic

        acronym = self.position["acronym"]
        speciality_name = clean_name(specialty["nombre"])
        topic, _ = Topic.objects.get_or_create(name=speciality_name)
        seat, _ = Seat.objects.get_or_create(
            position=self.position["pos"],
            topic=topic,
            judicial_district=self.district["jed"],
        )
        candidates_data = []
        seat.topic_index = idx
        available_seats = int(specialty["cargos"])
        seat.total_offices = available_seats
        pos_squares = 0
        for sex in self.sexs:
            plural = sex["plural"]
            colors = self.district.get(f"colores_{plural}_{acronym}", [])
            squares = colors[idx]
            setattr(seat, f"squares_{plural}", squares)
            pos_squares += squares
            candidates = self.district.get(f"{acronym}_{sex['gender']}", [])
            current_candidates = []
            for cand in candidates:
                cand_speciality_name = clean_name(cand.get("especialidad"))
                if speciality_name == cand_speciality_name:
                    current_candidates.append(cand)
                    cand_obj = self.build_candidate(cand, seat)
            candidates_data.extend(current_candidates)
            setattr(seat, f"real_{plural}", len(current_candidates))
        seat.plus_squares = pos_squares - available_seats
        seat.candidates_data = candidates_data
        seat.save()

    def build_candidate(self, candidate_simple, seat):
        speciality_name = candidate_simple.get("especialidad")
        speciality_name = clean_name(speciality_name)
        url = candidate_simple.get("url")
        # "https://candidaturaspoderjudicial.ine.mx/detalleCandidato/54854/11"
        if url:
            id_ine = url.split("/")[-2]
            id_ine = int(id_ine)
            candidate = self.candidates_dict.get(id_ine)
        else:
            print(f"Invalid URL {url}")
            print(f"Candidate data: {candidate_simple}")
            full_name = f"{candidate_simple['nombre']} {candidate_simple['apaterno']} {candidate_simple['amaterno']}"
            full_name = full_name.strip()
            full_name = full_name.replace("  ", " ")
            candidate = None
            for cand in self.candidates_dict.values():
                if cand["nombreCandidato"] == full_name:
                    candidate = cand
                    break
            if not candidate:
                print(f"Candidate not found {full_name}, {candidate_simple}")
                raise Exception(
                    f"Candidate not found {full_name}, {candidate_simple}")

        candidate_data = candidate_simple.copy()
        candidate_data.update(candidate)
        candidate_data["especialidad"] = speciality_name
        return self.save_candidate(candidate_data, seat)

    def save_candidate(self, candidate_data, seat):
        from oej.models import Power
        powers = candidate_data.get("propuesta", [])
        powers_obj = Power.objects.filter(key_name__in=powers)
        sex = candidate_data.get("sexo", "").strip()
        if sex in ["M", "H"]:
            final_sex = "Hombre" if sex == "H" else "Mujer"
        else:
            final_sex = None
            print(f"Sexo no reconocido {sex}")

        candidate, _ = Candidate.objects.get_or_create(
            first_name=candidate_data["nombre"],
            last_name_1=candidate_data["apaterno"],
            last_name_2=candidate_data["amaterno"],
            sex=final_sex,
            seat=seat,
        )
        if img_name := candidate_data.get("urlFoto"):
            img_url = img_name.replace("/media/cycc", self.ine_path)
            candidate.ine_photo = img_url
        if pdf_name := candidate_data.get("descripcionHLC"):
            pdf_url = f"{self.ine_path}/documentos/cv/{pdf_name}"
            candidate.ine_cv = pdf_url
        candidate.id_ine = candidate_data.get("idCandidato")
        candidate.num_list = candidate_data.get("numListaBoleta")
        candidate.ine_data = candidate_data
        candidate.save()

        for power in powers_obj:
            candidate.powers.add(power)
        return candidate

    def analyze_seats(self):

        all_seats = Seat.objects.filter(judicial_district__isnull=False)
        Candidate.objects.filter(anomaly__isnull=False).update(
            anomaly=None, probability=0)
        for seat in all_seats:
            # seat.save()
            total_real = seat.real_hombres + seat.real_mujeres
            ready = { "hombres": False, "mujeres": False }
            if total_real == seat.total_offices:
                seat.candidates.all().update(
                    anomaly_id="same_quantity", probability=100)
                if seat.real_mujeres == 0:
                    seat.probability_hombres = 100
                    seat.probability_mujeres = 0
                elif seat.real_hombres == 0:
                    seat.probability_mujeres = 100
                    seat.probability_hombres = 0
                else:
                    seat.probability_hombres = 100
                    seat.probability_mujeres = 100
                seat.save()
                continue
            if seat.total_offices == 1:
                if seat.real_mujeres == 1 and seat.real_hombres == 1:
                    seat.candidates.all().update(
                        anomaly_id="double_tie", probability=50)
                    seat.probability_hombres = 50
                    seat.probability_mujeres = 50
                    seat.save()
                    continue
                for (idx, sex) in enumerate(self.sexs):
                    if ready.get(sex["plural"]):
                        continue
                    real = getattr(seat, f"real_{sex['plural']}")
                    opposite_idx = 1 - idx
                    opposite = self.sexs[opposite_idx]
                    if real == 1:
                        seat.candidates.filter(sex=sex["name"]).update(
                            anomaly_id="winner", probability=100)
                        setattr(seat, f"probability_{sex['plural']}", 100)
                        ready[sex["plural"]] = True
                        seat.candidates.exclude(sex=sex["name"]).update(
                            anomaly_id="looser", probability=1)
                        setattr(seat, f"probability_{opposite['plural']}", 1)
                        ready[opposite["plural"]] = True
                if ready.get("hombres") and ready.get("mujeres"):
                    seat.save()
                    continue
            avg_percent_women, avg_percent_men = self.simulator.calculate_seat(seat)
            seat.probability_hombres = avg_percent_men
            seat.probability_mujeres = avg_percent_women
            seat.candidates.filter(sex="Hombre").update(
                probability=avg_percent_men)
            seat.candidates.filter(sex="Mujer").update(
                probability=avg_percent_women)
            seat.save()

    def calc_selected(self):
        for seat in Seat.objects.all():
            seat.selected_hombres = (
                seat.probability_hombres * seat.real_hombres / 100)
            seat.selected_mujeres = (
                seat.probability_mujeres * seat.real_mujeres / 100)
            seat.save()

    def post_gender_equity(self):
        import math
        from django.db.models import Sum, Count
        target_districts = []
        Seat.objects.all().update(
            final_selected_hombres=None, final_selected_mujeres=None)
        Candidate.objects.filter(final_anomaly__isnull=False)\
            .update(final_anomaly=None)
        districts = JudicialElectoralDistrict.objects.all()\
            .prefetch_related("seats")
        for jed in districts:
            for position in self.positions:
                pos = position["pos"]
                counts = jed.aggregations(pos)
                offices_hombres = counts["offices_hombres"]
                max_men = math.ceil(counts["total_offices"] / 2)
                max_shared_men = jed.seats\
                    .filter(
                        position=pos, shared_offices=1, real_hombres__gte=1,
                        probability_hombres__gte=0)
                diff = counts["selected_hombres"] - counts["selected_mujeres"]
                if diff > 1.2:
                    target_districts.append((jed, pos))
                elif diff > 0.2 and counts["total_offices"] % 2 == 1:
                    target_districts.append((jed, pos))

        for jed, pos in target_districts:
            counts = jed.aggregations(pos)
            offices_mujeres = counts["offices_mujeres"]
            min_women = math.floor(counts["total_offices"] / 2)
            min_forced = min_women - offices_mujeres
            shared_seats = jed.seats\
                .filter(
                position=pos, shared_offices__gte=1, real_mujeres__gte=1)\
                .order_by("real_mujeres")
            ready_seats = 0
            for seat_1 in shared_seats:
                same_quantity = shared_seats.filter(
                    real_mujeres=seat_1.real_mujeres)
                same_quantity_count = same_quantity.count()
                for seat in same_quantity:

                    seat.candidates\
                        .filter(sex="Hombre")\
                        .update(final_probability=0,
                                final_anomaly_id="forced_looser")
                    seat.probability_hombres = 0
                    prob_mujeres = 100 / seat.real_mujeres
                    seat.probability_mujeres = prob_mujeres
                    seat.gender_forced = 1
                    seat.final_selected_hombres = 0
                    seat.final_selected_mujeres = 1
                    seat.save()
                    seat.candidates\
                        .filter(sex="Mujer")\
                        .update(
                            final_probability=prob_mujeres,
                            final_anomaly_id=None)

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.final_selected_hombres is None:
                seat.final_selected_hombres = seat.selected_hombres
            if seat.final_selected_mujeres is None:
                seat.final_selected_mujeres = seat.selected_mujeres
            seat.save()

        pending_candidates = Candidate.objects.filter(
            anomaly__isnull=False, final_anomaly__isnull=True)
        for candidate in pending_candidates:
            candidate.final_anomaly = candidate.anomaly
            candidate.save()

        pending_candidates2 = Candidate.objects.filter(
            final_probability__isnull=True)
        for candidate in pending_candidates2:
            candidate.final_probability = candidate.probability
            candidate.save()

        easy_victory = Candidate.objects.filter(
            final_anomaly__isnull=True,
            final_probability__gte=90).update(
            final_anomaly_id="easy_victory")
        hard_victory = Candidate.objects.filter(
            final_anomaly__isnull=True,
            final_probability__lte=2).update(
            final_anomaly_id="hard_victory")

    def post_gender_equity_old(self):
        import math
        from django.db.models import Sum, Count
        from oej.models import Candidate
        target_districts = []
        Seat.objects.all().update(
            final_selected_hombres=None, final_selected_mujeres=None)
        Candidate.objects.filter(final_anomaly__isnull=False)\
            .update(final_anomaly=None)
        districts = JudicialElectoralDistrict.objects.all()\
            .prefetch_related("seats")
        for jed in districts:
            for position in self.positions:
                pos = position["pos"]
                counts = jed.aggregations(pos)
                diff = counts["selected_hombres"] - counts["selected_mujeres"]
                if diff > 1.2:
                    target_districts.append((jed, pos))
                elif diff > 0.2 and counts["total_offices"] % 2 == 1:
                    target_districts.append((jed, pos))

        for jed, pos in target_districts:
            counts = jed.aggregations(pos)
            offices_mujeres = counts["offices_mujeres"]
            min_women = math.floor(counts["total_offices"] / 2)
            min_forced = min_women - offices_mujeres
            shared_seats = jed.seats\
                .filter(
                position=pos, shared_offices__gte=1, real_mujeres__gte=1)\
                .order_by("real_mujeres")
            ready_seats = 0
            for seat_1 in shared_seats:
                same_quantity = shared_seats.filter(
                    real_mujeres=seat_1.real_mujeres)
                same_quantity_count = same_quantity.count()
                for seat in same_quantity:

                    seat.candidates\
                        .filter(sex="Hombre")\
                        .update(final_probability=0,
                                final_anomaly_id="forced_looser")
                    seat.probability_hombres = 0
                    prob_mujeres = 100 / seat.real_mujeres
                    seat.probability_mujeres = prob_mujeres
                    seat.gender_forced = 1
                    seat.final_selected_hombres = 0
                    seat.final_selected_mujeres = 1
                    seat.save()
                    seat.candidates\
                        .filter(sex="Mujer")\
                        .update(
                            final_probability=prob_mujeres,
                            final_anomaly_id=None)

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.final_selected_hombres is None:
                seat.final_selected_hombres = seat.selected_hombres
            if seat.final_selected_mujeres is None:
                seat.final_selected_mujeres = seat.selected_mujeres
            seat.save()

        pending_candidates = Candidate.objects.filter(
            anomaly__isnull=False, final_anomaly__isnull=True)
        for candidate in pending_candidates:
            candidate.final_anomaly = candidate.anomaly
            candidate.save()

        pending_candidates2 = Candidate.objects.filter(
            final_probability__isnull=True)
        for candidate in pending_candidates2:
            candidate.final_probability = candidate.probability
            candidate.save()

        easy_victory = Candidate.objects.filter(
            final_anomaly__isnull=True,
            final_probability__gte=90).update(
            final_anomaly_id="easy_victory")
        hard_victory = Candidate.objects.filter(
            final_anomaly__isnull=True,
            final_probability__lte=2).update(
            final_anomaly_id="hard_victory")

    def count_by_circ_dist(self):
        distritos = [
            {
                "circuito": 30,
                "distrito": 1,
                "entidad": 1,
            },
            {
                "circuito": 15,
                "distrito": 1,
                "entidad": 2,
            },
            {
                "circuito": 15,
                "distrito": 2,
                "entidad": 2,
            },
            {
                "circuito": 26,
                "distrito": 1,
                "entidad": 3,
            },
            {
                "circuito": 31,
                "distrito": 1,
                "entidad": 4,
            },
            {
                "circuito": 8,
                "distrito": 1,
                "entidad": 5,
            },
            {
                "circuito": 8,
                "distrito": 2,
                "entidad": 5,
            },
            {
                "circuito": 32,
                "distrito": 1,
                "entidad": 6,
            },
            {
                "circuito": 20,
                "distrito": 1,
                "entidad": 7,
            },
            {
                "circuito": 17,
                "distrito": 1,
                "entidad": 8,
            },
            {
                "circuito": 17,
                "distrito": 2,
                "entidad": 8,
            },
            {
                "circuito": 1,
                "distrito": 6,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 9,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 5,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 7,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 11,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 10,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 1,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 2,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 8,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 3,
                "entidad": 9,
            },
            {
                "circuito": 1,
                "distrito": 4,
                "entidad": 9,
            },
            {
                "circuito": 25,
                "distrito": 1,
                "entidad": 10,
            },
            {
                "circuito": 8,
                "distrito": 2,
                "entidad": 10,
            },
            {
                "circuito": 8,
                "distrito": 1,
                "entidad": 10,
            },
            {
                "circuito": 16,
                "distrito": 2,
                "entidad": 11,
            },
            {
                "circuito": 16,
                "distrito": 1,
                "entidad": 11,
            },
            {
                "circuito": 21,
                "distrito": 1,
                "entidad": 12,
            },
            {
                "circuito": 29,
                "distrito": 1,
                "entidad": 13,
            },
            {
                "circuito": 3,
                "distrito": 2,
                "entidad": 14,
            },
            {
                "circuito": 3,
                "distrito": 1,
                "entidad": 14,
            },
            {
                "circuito": 3,
                "distrito": 4,
                "entidad": 14,
            },
            {
                "circuito": 3,
                "distrito": 3,
                "entidad": 14,
            },
            {
                "circuito": 2,
                "distrito": 3,
                "entidad": 15,
            },
            {
                "circuito": 2,
                "distrito": 1,
                "entidad": 15,
            },
            {
                "circuito": 2,
                "distrito": 2,
                "entidad": 15,
            },
            {
                "circuito": 11,
                "distrito": 1,
                "entidad": 16,
            },
            {
                "circuito": 18,
                "distrito": 2,
                "entidad": 17,
            },
            {
                "circuito": 18,
                "distrito": 1,
                "entidad": 17,
            },
            {
                "circuito": 24,
                "distrito": 1,
                "entidad": 18,
            },
            {
                "circuito": 4,
                "distrito": 3,
                "entidad": 19,
            },
            {
                "circuito": 4,
                "distrito": 2,
                "entidad": 19,
            },
            {
                "circuito": 4,
                "distrito": 1,
                "entidad": 19,
            },
            {
                "circuito": 13,
                "distrito": 1,
                "entidad": 20,
            },
            {
                "circuito": 6,
                "distrito": 1,
                "entidad": 21,
            },
            {
                "circuito": 6,
                "distrito": 2,
                "entidad": 21,
            },
            {
                "circuito": 22,
                "distrito": 1,
                "entidad": 22,
            },
            {
                "circuito": 27,
                "distrito": 1,
                "entidad": 23,
            },
            {
                "circuito": 9,
                "distrito": 1,
                "entidad": 24,
            },
            {
                "circuito": 12,
                "distrito": 1,
                "entidad": 25,
            },
            {
                "circuito": 12,
                "distrito": 2,
                "entidad": 25,
            },
            {
                "circuito": 5,
                "distrito": 2,
                "entidad": 26,
            },
            {
                "circuito": 5,
                "distrito": 1,
                "entidad": 26,
            },
            {
                "circuito": 15,
                "distrito": 1,
                "entidad": 26,
            },
            {
                "circuito": 10,
                "distrito": 2,
                "entidad": 27,
            },
            {
                "circuito": 10,
                "distrito": 1,
                "entidad": 27,
            },
            {
                "circuito": 19,
                "distrito": 1,
                "entidad": 28,
            },
            {
                "circuito": 19,
                "distrito": 2,
                "entidad": 28,
            },
            {
                "circuito": 28,
                "distrito": 1,
                "entidad": 29,
            },
            {
                "circuito": 7,
                "distrito": 1,
                "entidad": 30,
            },
            {
                "circuito": 10,
                "distrito": 1,
                "entidad": 30,
            },
            {
                "circuito": 7,
                "distrito": 2,
                "entidad": 30,
            },
            {
                "circuito": 14,
                "distrito": 1,
                "entidad": 31,
            },
            {
                "circuito": 23,
                "distrito": 1,
                "entidad": 32,
            },
        ]
        by_circ_dist = { }
        for distrito in distritos:
            circ_dist = f"{distrito['circuito']}-{distrito['distrito']}"
            by_circ_dist.setdefault(circ_dist, [])
            by_circ_dist[circ_dist].append(distrito)

        for circ_dist, values in by_circ_dist.items():
            print(f"{circ_dist}: {values}")


def clean_name(name):
    import re
    name = name.replace("\n", " ")
    name = re.sub(r'\s+', ' ', name)
    return name.strip()
