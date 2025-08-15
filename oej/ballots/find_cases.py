import json

from lxml.html.diff import tag_token
from matplotlib.style.core import available

from oej.ballots.simulator import ElectionSimulator
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
                "name": "Misma cantidad de cargos y personas candidatas",
            },
            {
                "key_name": "same_quantity_men",
                "name": "Victoria porque hombres = cargos para hombres",
                "description": "Misma cantidad de personas candidatas y de cargos "
                        "asignados a hombres",
            },
            {
                "key_name": "same_quantity_women",
                "name": "Victoria porque mujeres = cargos para mujeres",
                "description": "Misma cantidad de personas candidatas y de cargos "
                        "asignados a mujeres",
            },
            {
                "key_name": "winner_all_votes_men",
                "name": "Victoria porque el hombre no divide los votos",
                "description": "Hay 1 vacante, pero solo hay "
                               "un candidato hombre y varias candidatas mujeres",
            },
            {
                "key_name": "winner_all_votes_women",
                "name": "Victoria porque la mujer no divide los votos",
                "description": "Hay 1 vacante, pero solo hay "
                               "una candidata mujer y varios candidatos hombres",
            },
            {
                "key_name": "looser_divided_women",
                "name": "Derrota de mujeres por dividir el voto",
                "description": "Las mujeres pierden porque dividen en voto,"
                               "mientras el único hombre tiene todos los votos"
            },
            {
                "key_name": "looser_divided_men",
                "name": "Derrota de hombres por dividir el voto",
                "description": "Los hombres pierden porque dividen en voto,"
                               "mientras la única mujer tiene todos los votos"
            },
            {
                "key_name": "double_tie",
                "name": "Doble empate",
                "description": "1 vacantes disponible, pero "
                               "una candidata mujer y un candidato hombre",
            },
            {
                "key_name": "hard_victory_man",
                "name": "Derrota muy probable por gran división del voto de hombres",
                "description": "Hay 1 vacante disponible, más candidatos "
                               "hombres que candidatas mujeres "
                               "los hombres se dividen mucho más el voto que "
                               "las mujeres y es muy probable la derrota de "
                               "los hombres "
            },
            {
                "key_name": "hard_victory_women",
                "name": "Derrota muy probable por gran división del voto de mujeres",
                "description": "Hay 1 vacante disponible, más candidatas "
                               "mujeres que candidatos hombres "
                               "las mujeres se dividen mucho más el voto que "
                               "los hombres y es muy probable la derrota de "
                               "las mujeres "
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

    def assign_anomalies(self):
        base_seats = Seat.objects.filter(
            position__by_circuit=True, )
        for seat in base_seats:
            if seat.total_offices == seat.real_hombres + seat.real_mujeres:
                seat.candidates.all().update(
                    anomaly='same_quantity')
            elif seat.offices_hombres and seat.offices_hombres == seat.real_hombres:
                seat.candidates.all().update(
                    anomaly='same_quantity_men')
            elif seat.offices_mujeres and seat.offices_mujeres == seat.real_mujeres:
                seat.candidates.all().update(
                    anomaly='same_quantity_women')

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
        self.add_empty_specialities()

    def add_empty_specialities(self):
        from geo.models import Topic, State
        specialties = [
            {"state": "Nuevo León", "speciality": "MIXTO", "dej": 3,
             "position": "mmtcca"},
            {"state": "Coahuila", "speciality": "MERCANTIL", "dej": 2,
             "position": "jjd"},
        ]
        for speciality in specialties:
            position = Position.objects.get(acronym=speciality["position"])
            topic, _ = Topic.objects.get_or_create(
                name=speciality["speciality"],
            )
            state = State.objects.get(short_name=speciality["state"])
            jed = JudicialElectoralDistrict.objects.get(
                number=speciality["dej"], state=state
            )
            seat, _ = Seat.objects.get_or_create(
                position=position,
                topic=topic,
                judicial_district=jed,
            )

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
        all_seats.update(has_simulations=False)
        Candidate.objects.all().update(
            anomaly=None, probability=None, final_probability=0,
            simulations=None, final_anomaly=None, circuit_probability=None)
        for seat in all_seats:
            # seat.save()
            total_real = seat.real_hombres + seat.real_mujeres
            ready = { "hombres": False, "mujeres": False }
            if total_real <= seat.total_offices:
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
                            anomaly_id="looser", probability=0)
                        setattr(seat, f"probability_{opposite['plural']}", 0)
                        ready[opposite["plural"]] = True
                if ready.get("hombres") and ready.get("mujeres"):
                    seat.save()
                    continue
            avg_percent_women, avg_percent_men = self.simulator\
                .simulate_seat(seat)
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

    def calc_real_votes(self):
        import math
        self.simulator.set_real()
        Candidate.objects.all().update(
            real_winner=None,
            real_winner_final=None, real_winner_circuit=None,
        )
        districts = JudicialElectoralDistrict.objects.all()\
            .prefetch_related("seats")
        for jed in districts:
            for position in self.positions:
                pos = position["pos"]
                counts = jed.aggregations(pos)
                offices_mujeres = counts["offices_mujeres"]
                min_offices_women = math.floor(counts["total_offices"] / 2)
                self.simulator.calculate_pos_district(
                    pos, min_offices_women, jed, offices_mujeres
                )

    def calc_real_dis_votes(self):
        import math
        from django.db.models import Sum
        from geo.models import State, Topic
        states = State.objects.all()
        target_states = []

        for state in states:
            circuit = state.circuit
            judicial_districts = state.judicial_electoral_districts.all()
            if judicial_districts.count() < 2:
                continue
            for position in self.positions:
                pos = position["pos"]
                seats = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)
                all_topics = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)\
                    .values_list("topic_id", flat=True).distinct()
                unique_topics = set(all_topics)
                for topic in unique_topics:
                    topic_obj = Topic.objects.get(id=topic)
                    topic_seats = seats.filter(topic=topic_obj)
                    max_shared_men = topic_seats\
                        .filter(shared_offices=1, real_hombres__gte=1)
                    fields = [
                        'total_offices', 'offices_hombres', 'offices_mujeres']

                    query = { aggr: Sum(aggr) for aggr in fields }
                    counts = topic_seats.aggregate(**query)
                    offices_hombres = counts["offices_hombres"]
                    max_offices_men = math.ceil(counts["total_offices"] / 2)
                    min_offices_women = math.floor(counts["total_offices"] / 2)
                    max_simple_men = offices_hombres + max_shared_men.count()
                    # if max_simple_men > max_offices_men:
                    target_states.append((state, pos, topic_obj, min_offices_women))
        print(f"Target districts: {len(target_states)}")

        for (state, pos, topic_obj, min_offices_women) in target_states:
            print(f"\n{pos.short_name} - {state.short_name} - "
                  f"{topic_obj.name}")
            self.simulator.calculate_topic_circuit(
                pos, min_offices_women, state, topic_obj)

    def post_gender_equity(self, jed_id=None):
        import math
        target_districts = []
        if not jed_id:
            Seat.objects.all().update(
                forced_probability_hombres=0, forced_probability_mujeres=0,
                circuit_forced_probability_hombres=0,
                circuit_forced_probability_mujeres=0,
                final_selected_hombres=None, final_selected_mujeres=None,
                final_probability_hombres=None, final_probability_mujeres=None,
                circuit_probability_hombres=None, circuit_probability_mujeres=None,
            )
            Candidate.objects.filter(final_anomaly__isnull=False)\
                .update(final_anomaly=None)
            Candidate.objects.all().update(final_probability=None)
        districts = JudicialElectoralDistrict.objects.all()\
            .prefetch_related("seats")
        if jed_id:
            districts = districts.filter(id=jed_id)
        for jed in districts:
            for position in self.positions:
                pos = position["pos"]
                # print(f"\n{position['short_name']} - {jed.id} - "
                #       f"{jed.state.short_name} [{jed.number}]")
                max_shared_men = jed.seats\
                    .filter(
                        position=pos, shared_offices=1, real_hombres__gte=1,
                        probability_hombres__gt=0)
                if not max_shared_men.exists():
                    continue
                counts = jed.aggregations(pos)
                offices_hombres = counts["offices_hombres"]
                offices_mujeres = counts["offices_mujeres"]
                max_offices_men = math.ceil(counts["total_offices"] / 2)
                min_offices_women = math.floor(counts["total_offices"] / 2)
                max_simple_men = offices_hombres + max_shared_men.count()
                if max_simple_men > max_offices_men:
                    target_districts.append(
                        (jed, pos, min_offices_women, offices_mujeres))

        print(f"Target districts: {len(target_districts)}")

        for jed, pos, min_offices_women, offices_mujeres in target_districts:
            self.simulator.calculate_pos_district(
                pos, min_offices_women, jed, offices_mujeres
            )

        if not jed_id:
            self.save_final_data()

    def post_gender_by_circuit(self, ciruit_id=None):
        import math
        from django.db.models import Sum, Count
        from geo.models import State, Topic
        target_states = []

        states = State.objects.all()
        for state in states:
            circuit = state.circuit
            judicial_districts = state.judicial_electoral_districts.all()
            if judicial_districts.count() < 2:
                continue
            for position in self.positions:
                pos = position["pos"]
                seats = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)
                all_topics = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)\
                    .values_list("topic_id", flat=True).distinct()
                unique_topics = set(all_topics)
                for topic in unique_topics:
                    topic_obj = Topic.objects.get(id=topic)
                    topic_seats = seats.filter(topic=topic_obj)
                    max_shared_men = topic_seats\
                        .filter(
                            shared_offices=1, real_hombres__gte=1,
                            final_probability_hombres__gt=0.1)
                    # if not max_shared_men.exists():
                    #     # print("Not hay shared offices")
                    #     continue
                    fields = ['total_offices', 'real_hombres', 'real_mujeres',
                              'offices_hombres', 'offices_mujeres']
                    # print(f"\n{position['short_name']} - {state.short_name} - "
                    #       f"{topic_obj.name}")
                    # print("Topic seats: ", topic_seats.count())

                    query = { aggr: Sum(aggr) for aggr in fields }
                    counts = topic_seats.aggregate(**query)
                    offices_hombres = counts["offices_hombres"]
                    max_offices_men = math.ceil(counts["total_offices"] / 2)
                    min_offices_women = math.floor(counts["total_offices"] / 2)
                    max_simple_men = offices_hombres + max_shared_men.count()
                    if max_simple_men > max_offices_men:
                        target_states.append((state, pos, topic_obj, min_offices_women))

        print(f"Target districts: {len(target_states)}")

        for (state, pos, topic_obj, min_offices_women) in target_states:
            print(f"\n{pos.short_name} - {state.short_name} - "
                  f"{topic_obj.name}")
            self.simulator.calculate_topic_circuit(
                pos, min_offices_women, state, topic_obj)

        self.save_circuit_data()
            # print("Topic seats: ", topic_seats.count())

        # for jed, pos, min_offices_women in target_districts:
        #     self.simulator.calculate_pos_district(
        #         pos, jed, min_offices_women
        #     )
        #
        # if not jed_id:
        #     self.save_final_data()

    def save_final_data(self):

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.final_probability_hombres is None:
                seat.final_probability_hombres = seat.probability_hombres
            if seat.final_probability_mujeres is None:
                seat.final_probability_mujeres = seat.probability_mujeres
            seat.final_selected_hombres = (
                seat.final_probability_hombres * seat.real_hombres / 100)
            seat.final_selected_mujeres = (
                seat.final_probability_mujeres * seat.real_mujeres / 100)
            seat.save()

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.final_selected_hombres is None:
                seat.final_selected_hombres = seat.selected_hombres
            if seat.final_selected_mujeres is None:
                seat.final_selected_mujeres = seat.selected_mujeres
            seat.save()

        pending_candidates = Candidate.objects.filter(
            seat__position__by_circuit=True)
        for sex in ["Hombre", "Mujer"]:
            sex_candidates = pending_candidates.filter(sex=sex)
            for candidate in sex_candidates:
                if sex == "Hombre":
                    candidate.final_probability = candidate.seat.final_probability_hombres
                else:
                    candidate.final_probability = candidate.seat.final_probability_mujeres
                candidate.save()
        # pending_candidates = Candidate.objects.filter(
        #     anomaly__isnull=False, final_anomaly__isnull=True)
        # for candidate in pending_candidates:
        #     candidate.final_anomaly = candidate.anomaly
        #     candidate.save()
        #
        # easy_victory = Candidate.objects.filter(
        #     final_anomaly__isnull=True,
        #     final_probability__gte=90).update(
        #     final_anomaly_id="easy_victory")
        # hard_victory = Candidate.objects.filter(
        #     final_anomaly__isnull=True,
        #     final_probability__lte=2).update(
        #     final_anomaly_id="hard_victory")

    def save_circuit_data(self):

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.circuit_probability_hombres is None:
                seat.circuit_probability_hombres = seat.final_probability_hombres
            if seat.circuit_probability_mujeres is None:
                seat.circuit_probability_mujeres = seat.final_probability_mujeres
            seat.circuit_selected_hombres = (
                seat.circuit_probability_hombres * seat.real_hombres / 100)
            seat.circuit_selected_mujeres = (
                seat.circuit_probability_mujeres * seat.real_mujeres / 100)
            seat.save()

        for seat in Seat.objects.filter(position__by_circuit=True):
            if seat.circuit_selected_hombres is None:
                seat.circuit_selected_hombres = seat.final_selected_hombres
            if seat.circuit_selected_mujeres is None:
                seat.circuit_selected_mujeres = seat.final_selected_mujeres
            seat.save()

        pending_candidates = Candidate.objects.filter(
            seat__position__by_circuit=True)
        for sex in ["Hombre", "Mujer"]:
            sex_candidates = pending_candidates.filter(sex=sex)
            for candidate in sex_candidates:
                if sex == "Hombre":
                    candidate.circuit_probability = candidate.seat.circuit_probability_hombres
                else:
                    candidate.circuit_probability = candidate.seat.circuit_probability_mujeres
                candidate.save()


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


def count_by_circ_dist():
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

