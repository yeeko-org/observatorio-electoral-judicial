import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Patch
from scipy.stats import zipf
from oej.models import Seat, Position
from geo.models import JudicialElectoralDistrict, Topic, State
from tqdm import tqdm
# import Any to type Seat | SeatCase
from typing import Any, Union


class SeatCase:
    def __init__(self, **kwargs):
        self.real_mujeres = kwargs.get("real_mujeres", 0)
        self.real_hombres = kwargs.get("real_hombres", 0)
        self.squares_mujeres = kwargs.get("squares_mujeres", 0)
        self.squares_hombres = kwargs.get("squares_hombres", 0)
        self.total_offices = kwargs.get("total_offices", 0)
        self.shared_offices = kwargs.get("shared_offices", 0)
        self.offices_mujeres = kwargs.get("offices_mujeres", 0)
        self.offices_hombres = kwargs.get("offices_hombres", 0)
        self.id = 0
        self.__dict__.update(kwargs)

    def __str__(self):
        return (f"{self.real_mujeres}-{self.real_hombres} -"
                f" ({self.squares_mujeres}-({self.total_offices})")


class ElectionSimulator:

    case_fields = [
        'real_mujeres', 'real_hombres', 'squares_mujeres',
        'squares_hombres', 'total_offices', 'shared_offices',
        'offices_mujeres', 'offices_hombres']
    simulation_by_real = {}

    def __init__(self, show_results=True):
        self.iterations = 1000
        # Nuevo parámetro para indicar el tipo de simulación
        self.simulation_type = "dirichlet"  # Opciones: "random", "strategic", "zipf_pareto"
        # Parámetro para distribución Zipf
        self.zipf_param = 1.4  # Controla qué tan pronunciada es la "cola larga"
        self.show_results = show_results
        self.winners_count = {}
        self.candidates_women = []
        self.candidates_men = []
        self.by_district = False
        self.case_results = {}
        self.simulation_data = {}
        self.by_circuit = False
        self.topic:Topic | None = None
        self.concentration_factor = 20
        self.zipf_dict = {}
        self.voters_size = 1000
        self.base_factor = 50
        self.forced_simulation = False
        self.iteration_idx:int = 0

    def simulate_fake_elections(
            self, simulation_type, cases, zipf_param=1.4,
            concentration_factor=20):
        """
        Función principal que coordina la simulación
        """
        # Actualizar el tipo de simulación
        self.simulation_type = simulation_type
        self.zipf_param = zipf_param
        self.concentration_factor = concentration_factor

        # Definir casos (mantiene tu código original)
        # Ejecutar cada caso
        for idx, case in enumerate(cases):
            seat = SeatCase(**case)
            candidates_women = list(range(1, seat.real_mujeres + 1))
            candidates_men = list(range(101, seat.real_hombres + 101))
            all_candidates = candidates_women + candidates_men
            for cand_id in all_candidates:
                self.build_candidate_data(seat, fake_id=cand_id)
            self.run_simulation_seat(seat=seat, idx=idx)

    def simulate_seat(self, seat:Seat | SeatCase):
        self.show_results = False
        self.simulation_type = "dirichlet"
        # self.simulation_type = "zipf_pareto"
        self.zipf_param = 1.3
        self.concentration_factor = 20
        self.winners_count = {}
        self.simulation_data = {}
        candidates = seat.candidates.all()
        for candidate in candidates:
            self.build_candidate_data(seat, candidate)

        return self.run_simulation_seat(seat=seat)

    def calculate_pos_district(
            self, position:Position, min_offices_women:int,
            jed: JudicialElectoralDistrict = None,
            offices_mujeres=None
    ):
        self.show_results = False
        self.simulation_type = "dirichlet"
        self.zipf_param = 1.4
        self.winners_count = {}
        self.by_district = True
        self.candidates_men = []
        self.simulation_data = {}

        print(f"Starting {position} of jed {jed}")
        shared_seats = jed.seats \
            .filter(
            position=position, shared_offices=1, real_hombres__gte=1)

        for seat in shared_seats:
            candidates = seat.candidates.all()
            self.build_candidates_data(seat, candidates)
            for iteration_idx in range(self.iterations):
                self.calculate_seat_winners(seat, iteration_idx)
            # for candidate in candidates:
            #     self.build_candidate_data(seat, candidate)
        if not offices_mujeres:
            counts = jed.aggregations(position)
            offices_mujeres = counts["offices_mujeres"]
        for iteration_idx in range(self.iterations):
            self.iteration_idx = iteration_idx
            self.assign_by_equity_rules(
                min_offices_women, offices_mujeres, iteration_idx)

        self.assign_avg_by_seat(shared_seats)
        self.save_simulations(shared_seats)

    def calculate_topic_circuit(
            self, position:Position, min_offices_women:int,
            state:State = None, topic:Topic = None,
    ):
        self.show_results = False
        self.simulation_type = "zipf_pareto"
        self.zipf_param = 1.4
        self.winners_count = {}
        self.by_district = True
        self.candidates_men = []
        self.simulation_data = {}
        self.topic = topic
        self.by_district = False
        shared_seats = Seat.objects.filter(
            position=position, topic=topic,
            judicial_district__state=state)

        for seat in shared_seats:
            candidates = seat.candidates.all()
            self.build_candidates_data(seat, candidates)

        # counts = jed.aggregations(position)
        # offices_mujeres = counts["offices_mujeres"]
        for seat in shared_seats:
            if seat.has_simulations:
                continue
            for iteration_idx in range(self.iterations):
                self.calculate_seat_winners(seat, iteration_idx)

        self.save_simulations(shared_seats)

        for iteration_idx in range(self.iterations):
            self.iteration_idx = iteration_idx
            # self.assign_by_equity_rules(min_offices_women, offices_mujeres)
            self.assign_topic_district_equity_rules(
                shared_seats, iteration_idx=iteration_idx, topic=topic,
                min_offices_women=min_offices_women)

        self.assign_avg_by_seat(shared_seats, only_circuit=True)
        self.save_simulations(shared_seats)

    def build_candidates_data(self, seat:Seat | SeatCase, candidates):
        if seat.has_simulations:
            for candidate in candidates:
                self.build_candidate_data(seat, candidate)
        else:
            sexes = [('Mujer', 'mujeres'), ('Hombre', 'hombres')]
            for sex, plural in sexes:
                sex_candidates = candidates.filter(sex=sex)
                self.generate_full_simulation(
                    seat, sex_candidates, getattr(seat, f"squares_{plural}"))

    def build_candidate_data(
            self, seat:Seat | SeatCase, candidate=None,
            fake_id=None, votes=None):

        if candidate:
            is_man = candidate.sex == 'Hombre'
            id_ine = candidate.id_ine
            sex = candidate.sex
            if votes:
                simulate = [
                    {
                        "votes": votes_count,
                        "init_winner": False,
                        "final_winner": False,
                        "circuit_winner": False,
                    } for votes_count in votes]
            else:
                simulate = candidate.simulations or []

            init_winner = sum(
                [sim["init_winner"] for sim in simulate])
            final_winner = sum(
                [sim["final_winner"] for sim in simulate])
            circuit_winner = sum(
                [sim["circuit_winner"] for sim in simulate])
            topic = seat.topic.id
        else:
            is_man = fake_id > 100
            sex = "Hombre" if is_man else "Mujer"
            id_ine = fake_id
            simulate = []
            init_winner, final_winner, circuit_winner = 0, 0, 0
            topic = None
        self.simulation_data[id_ine] = {
            "init_winner": init_winner,
            "final_winner": final_winner, "circuit_winner": circuit_winner,
            "sex": sex, "is_man": is_man,
            "seat": seat.id,
            "topic": topic,
            "id": id_ine,
            "obj": candidate,
            "forced": 0,
            "circuit_forced": 0,
            # "simulations": simulations,
            "simulate": simulate,
        }

    def calculate_seat_winners(self, seat:Seat | SeatCase, iteration_idx=None):
        seat_candidates = {
            cand_id: candidate for cand_id, candidate in self.simulation_data.items()
            if candidate["seat"] == seat.id}
        if seat.shared_offices == 1:
            all_candidates_votes = {
                cand_id: candidate["simulate"][iteration_idx]["votes"]
                for cand_id, candidate in seat_candidates.items()
            }
            winners = self.get_simple_winners(all_candidates_votes)
            self.assign_simulate_winners(
                all_candidates_votes, winners, iteration_idx)
        else:
            for sex, plural in [("Hombre", "hombres"), ("Mujer", "mujeres")]:
                sex_candidates_votes = {
                    cand_id: candidate["simulate"][iteration_idx]["votes"]
                    for cand_id, candidate in seat_candidates.items()
                    if candidate["sex"] == sex
                }
                winners = self.get_simple_winners(
                    sex_candidates_votes, getattr(seat, f"offices_{plural}"))
                self.assign_simulate_winners(
                    sex_candidates_votes, winners, iteration_idx)

    def assign_simulate_winners(
            self, candidates_votes, winners, iteration_idx):
        for winner in winners:
            self.simulation_data[winner]["init_winner"] += 1
            self.simulation_data[winner]["final_winner"] += 1
            self.simulation_data[winner]["circuit_winner"] += 1

        for cand_id, votes in candidates_votes.items():
            # self.simulation_data[cand_id]["last_votes"] += votes
            is_winner = cand_id in winners
            self.simulation_data[cand_id]["simulate"][iteration_idx].update({
                "init_winner": is_winner,
                "final_winner": is_winner,
                "circuit_winner": is_winner
            })

    def assign_by_equity_rules(
            self, min_offices_women, offices_mujeres, iteration_idx):
        women_winners = [
            candidate for candidate in self.simulation_data.values()
            if not candidate["is_man"] and
               candidate["simulate"][iteration_idx]["init_winner"]]
        women_winners_seat_ids = {
            candidate["seat"] for candidate in women_winners}
        men_winners = [
            candidate for candidate in self.simulation_data.values()
            if candidate["is_man"]
               and candidate["simulate"][iteration_idx]["init_winner"]]
        pending_women = min_offices_women - offices_mujeres - len(women_winners)

        if pending_women > 0:
            last_women_loosers = [
                candidate for candidate in self.simulation_data.values()
                if not candidate["is_man"]
                   and not candidate["simulate"][iteration_idx]["init_winner"]
                   and not candidate["seat"] in women_winners_seat_ids
            ]
            if not last_women_loosers:
                # print("!!No hay ningún last_women_loosers")
                return
            sorted_loosers = sorted(
                last_women_loosers,
                key=lambda x: x["simulate"][iteration_idx]["votes"],
                reverse=True
            )
            new_seat_ids = set()
            for candidate in sorted_loosers:
                seat_id = candidate["seat"]
                cand_id = candidate["id"]
                if seat_id not in new_seat_ids:
                    new_seat_ids.add(seat_id)
                    self.simulation_data[cand_id]["final_winner"] += 1
                    self.simulation_data[cand_id]["circuit_winner"] += 1
                    self.simulation_data[cand_id]["forced"] += 1
                    self.simulation_data[cand_id]["simulate"][iteration_idx]["final_winner"] = True
                    self.simulation_data[cand_id]["simulate"][iteration_idx]["circuit_winner"] = True
                    if pending_women >= len(new_seat_ids):
                        break
            new_men_no_winners = [
                candidate for candidate in men_winners
                if candidate["seat"] in new_seat_ids
            ]
            for candidate in new_men_no_winners:
                cand_id = candidate["id"]
                self.simulation_data[cand_id]["final_winner"] -= 1
                self.simulation_data[cand_id]["circuit_winner"] -= 1
                self.simulation_data[cand_id]["forced"] -= 1
                self.simulation_data[cand_id]["simulate"][iteration_idx]["final_winner"] = False
                self.simulation_data[cand_id]["simulate"][iteration_idx]["circuit_winner"] = False

    def assign_topic_district_equity_rules(
            self, topic_seats, iteration_idx, topic:Topic, min_offices_women):

        current_candidates = [
            candidate for candidate in self.simulation_data.values()
            if candidate["topic"] == topic.id]
        women_candidates = [
            candidate for candidate in current_candidates
            if not candidate["is_man"]]
        men_candidates = [
            candidate for candidate in current_candidates
            if candidate["is_man"]]

        women_winners = [
            candidate for candidate in women_candidates
            if candidate["simulate"][iteration_idx]["final_winner"]]
        men_winners = [
            candidate for candidate in men_candidates
            if candidate["simulate"][iteration_idx]["final_winner"]]

        pending_women = min_offices_women - len(women_winners)

        if pending_women > 0:
            last_women_loosers = [
                candidate for candidate in women_candidates
                if not candidate["simulate"][iteration_idx]["final_winner"]
            ]
            if not last_women_loosers:
                return
            sorted_women_loosers = sorted(
                last_women_loosers,
                key=lambda x: x["simulate"][iteration_idx]["votes"],
                reverse=True
            )
            # new_seat_ids = set()
            moved = 0
            for candidate in sorted_women_loosers[:pending_women]:
                # seat_id = candidate["seat"]
                # if seat_id not in new_seat_ids:
                # new_seat_ids.add(seat_id)
                cand_id = candidate["id"]
                self.simulation_data[cand_id]["circuit_winner"] += 1
                self.simulation_data[cand_id]["circuit_forced"] += 1
                self.simulation_data[cand_id]["simulate"][iteration_idx]["circuit_winner"] = False
                moved += 1
                # if pending_women >= len(new_seat_ids):
                #     break
            sorted_men_winners = sorted(
                men_winners,
                key=lambda x: x["simulate"][iteration_idx]["votes"],
                reverse=False
            )
            for candidate in sorted_men_winners[:moved]:
                cand_id = candidate["id"]
                self.simulation_data[cand_id]["circuit_winner"] -= 1
                self.simulation_data[cand_id]["circuit_forced"] -= 1
                self.simulation_data[cand_id]["simulate"][iteration_idx]["circuit_winner"] = False

    def assign_avg_by_seat(self, shared_seats, only_circuit=False):
        for seat in shared_seats:
            seat = self.get_averages(seat, "mujeres", only_circuit)
            seat = self.get_averages(seat, "hombres", only_circuit)
            seat.save()

    def save_simulations(self, shared_seats):
        for seat in shared_seats:
            seat.has_simulations = True
            seat.save()
        for cand in self.simulation_data.values():
            candidate = cand["obj"]
            # candidate.simulations = cand["simulations"]
            candidate.simulations = cand["simulate"]
            candidate.save()

    def run_simulation_seat(
            self, seat:Seat | SeatCase | None, idx=0):
        if self.forced_simulation:
            return self.run_simulations(seat)
        # Calcular asignación de cargos (mantiene tu función original)
        # case = self.build_case(seat)
        if seat.shared_offices:
            values = [
                getattr(seat, field) for field in self.case_fields]
            # Generar una clave única para el caso con un join -
            key = "-".join([str(value) for value in values])
            if seat.real_mujeres == seat.real_hombres:
                sum_real = seat.real_mujeres + seat.real_hombres
                average = 1 / sum_real * 100
                return average, average

            # values = case.values()
            if not self.show_results and key in self.case_results:
                return self.case_results[key]

            print(f"\nCaso {idx + 1}: {seat}")
            # print(f"Tipo de simulación: {self.simulation_type} (α={self.zipf_param})")

            # Realizar simulaciones
            self.run_simulations(seat)

            if self.show_results:
                # Visualizar resultados
                self.visualize_results(seat, idx)
            else:
                avg_percent_women, avg_percent_men = self.get_averages_by_sex()
                self.case_results[key] = (avg_percent_women, avg_percent_men)
                return avg_percent_women, avg_percent_men
        avg_percent_women = 0
        avg_percent_men = 0
        if seat.real_mujeres > 0:
            avg_percent_women = seat.offices_mujeres / seat.real_mujeres * 100
        if seat.real_hombres > 0:
            avg_percent_men = seat.offices_hombres / seat.real_hombres * 100
        return avg_percent_women, avg_percent_men

    def run_simulations(self, seat:Seat | SeatCase):
        """
        Ejecuta las simulaciones con diferentes modelos
        """
        if seat.shared_offices == 0:
            raise Exception("No deberían llegar si no tienen shared_offices")

        # for iteration in range(self.iterations):
        desc = "Running simulations"
        all_votes = []
        for iteration_idx in tqdm(range(self.iterations), desc=desc):
            self.iteration_idx = iteration_idx
            winner, votes = self.run_simulation_by_sex(
                seat, self.simulation_data)
            all_votes.append(len(votes))
            # self.winners_count[winner] += 1
            self.simulation_data[winner]["init_winner"] += 1
            self.simulation_data[winner]["final_winner"] += 1
            self.simulation_data[winner]["circuit_winner"] += 1

    def run_simulation_by_sex(
            self, seat:Seat | SeatCase, current_candidates):
        all_votes = {}
        sexes = [('mujeres', False), ('hombres', True)]
        for plural, is_man in sexes:
            candidates = [
                cand_id for cand_id, candidate in current_candidates.items()
                if candidate["is_man"] == is_man]
            # votes = self.simulate_voting(
            #     candidates, case[f"squares_{plural}"])
            votes = self.simulate_voting(
                candidates, getattr(seat, f"squares_{plural}"))
            all_votes.update(votes)
        winner = self.get_simple_winners(all_votes)[0]
        return winner, all_votes

    def run_simulation(
            self, seat:Seat | SeatCase,
            current_candidates, sex="Mujer"):
        sex_name = "woman" if sex == "Mujer" else "men"

        # all_votes = self.simulate_voting(
        #     current_candidates, case[f"squares_{sex_name}"])
        all_votes = self.simulate_voting(
            current_candidates, getattr(seat, f"squares_{sex_name}"))
        # winners = self.get_winners(all_votes, case[f"offices_{sex_name}"])
        winners = self.get_simple_winners(
            all_votes, getattr(seat, f"offices_{sex_name}"))
        return winners, all_votes

    def generate_popularity(self, candidates):
        """
        Genera distribución de popularidad siguiendo Zipf
        """
        # Generar valores Zipf para cada candidato
        n = len(candidates)
        if n in self.zipf_dict:
            zipf_values = self.zipf_dict[n]
        else:
            zipf_values = zipf.pmf(range(1, n + 1), self.zipf_param)
            self.zipf_dict[n] = zipf_values

        # Use Zipf values as concentration parameters for Dirichlet
        alpha = zipf_values * self.concentration_factor

        # Generate random probabilities from Dirichlet
        random_probs = np.random.dirichlet(alpha)
        shuffled_candidates = random.sample(candidates, len(candidates))
        # Assign to candidates
        popularity = {}
        for i, candidate in enumerate(shuffled_candidates):
            popularity[candidate] = random_probs[i]
        return popularity

    def generate_simple_popularity(self, candidates):
        """
        Genera distribución de popularidad siguiendo Zipf
        """
        # Generar valores Zipf para cada candidato
        n = len(candidates)
        # Use Zipf values as concentration parameters for Dirichlet
        alpha = np.array([self.base_factor] * n) / n

        # Generate random probabilities from Dirichlet
        random_probs = np.random.dirichlet(alpha)
        # Assign to candidates
        popularity = {
            candidate: random_probs[i]
            for i, candidate in enumerate(candidates)
        }
        return popularity

    def simulate_voting(self, candidates, squares):
        if self.forced_simulation:
            pass

        if self.simulation_type == "zipf_pareto":
            popularity = self.generate_popularity(candidates)
        else:
            popularity = self.generate_simple_popularity(candidates)

        """Simulate voting with the given parameters."""
        votes = { candidate: 0 for candidate in candidates }

        # Convert to arrays for faster processing
        candidates_array = np.array(list(candidates))
        probs = np.array([popularity[c] for c in candidates])

        if len(candidates) <= squares:
            for candidate in candidates:
                votes[candidate] = self.voters_size
            return votes

        # Run the simulation for each voter
        for _ in range(self.voters_size):
            # Weighted selection based on popularity
            selected = np.random.choice(
                candidates_array,
                size=squares,
                replace=False,
                p=probs
            )

            for candidate in selected:
                votes[candidate] += 1

        return votes

    def generate_full_simulation(self, seat, candidates, squares):
        candidates_count = len(candidates)
        key = f"{candidates_count}-in-{squares}"
        if key in self.simulation_by_real:
            saved_votes = self.simulation_by_real[key]
            final_votes = random.sample(saved_votes, len(saved_votes))
        else:
            final_votes = []
            candidates_ids = list(candidates.values_list("id_ine", flat=True))
            for iteration_idx in range(self.iterations):
                self.iteration_idx = iteration_idx
                candidates_votes = self.simulate_voting(
                    candidates_ids, squares)
                votes = candidates_votes.values()
                final_votes.append(votes)
            self.simulation_by_real[key] = final_votes

        # print("final_votes", final_votes)
        for i, candidate in enumerate(candidates):
            # cand_votes[candidate] = final_votes[i]
            cand_votes = []
            for iteration_idx in range(self.iterations):
                iteration_votes = final_votes[iteration_idx]
                # iteration_votes is a dict_values
                # convert iteration_votes to a list
                iteration_votes = list(iteration_votes)
                cand_votes.append(iteration_votes[i])
            self.build_candidate_data(seat, candidate, votes=cand_votes)

    def determine_winners(self, votes, offices):
        """Mantiene tu implementación original"""
        # [Código existente sin cambios]
        sorted_by_sex = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        offices = min(offices, len(votes))
        winners = [candidate for candidate, _ in sorted_by_sex[:offices]]
        return winners

    def get_simple_winners(self, all_votes, winners_count=1):
        sorted_remaining = sorted(
            all_votes.items(), key=lambda x: x[1], reverse=True)
        return [
            candidate for candidate, _ in sorted_remaining[:winners_count]
        ]

    def get_winners(self, all_votes, winners_count=1):
        sorted_remaining = sorted(
            all_votes.items(), key=lambda x: x[1], reverse=True)
        return [
            candidate for candidate, _ in sorted_remaining[:winners_count]
        ]

    def visualize_results(self, seat:Seat | SeatCase, idx):
        """MODIFICADA: Incluye tipo de simulación en el título"""
        # [Código similar al original con adición del tipo de simulación]
        # Gráfica 1: Por candidato individual
        squares_mujeres = seat.squares_mujeres
        squares_hombres = seat.squares_hombres
        total_offices = seat.total_offices
        plt.figure(figsize=(14, 7))
        candidates = sorted(self.simulation_data.keys())
        wins = [self.simulation_data[c]["init_winner"] for c in candidates]
        percentages = [100 * w / self.iterations for w in wins]
        colors = ['pink' if c < 100 else 'lightblue' for c in candidates]

        bars = plt.bar(range(len(candidates)), percentages, color=colors)
        plt.xticks(range(len(candidates)), candidates, rotation=90)

        # Añadir tipo de simulación al título
        common_title = f' ({self.simulation_type}) '
        if self.simulation_type == "zipf_pareto":
            common_title += f' (α={self.zipf_param}) '
        else:
            common_title += f' (Base={self.base_factor}) '
        common_title += (
            f'\n[{squares_mujeres}][{seat.shared_offices}][{squares_hombres}] '
            f' ({total_offices})')
        plt.title(f'% Victoria por Candidato {common_title}')

        plt.ylabel('Porcentaje de Victoria (%)')
        plt.xlabel('ID Candidato')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        common_path = f"fixture/charts/02case{idx+1}_{self.simulation_type}"
        if self.simulation_type == "zipf_pareto":
            common_path += f"_zipf_{self.zipf_param}"
        else:
            common_path += f"_dirichlet_{self.base_factor}"

        # Añadir etiquetas con total de votos y porcentaje
        for i, bar in enumerate(bars):
            wins_value = wins[i]
            percentage = percentages[i]
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f'{wins_value}\n({percentage:.1f}%)',
                     ha='center', va='bottom', rotation=0, fontsize=8,
                     bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.2'))

        # Añadir leyenda
        legend_elements = [
            Patch(facecolor='pink', label='Mujeres'),
            Patch(facecolor='lightblue', label='Hombres')
        ]
        plt.legend(handles=legend_elements)

        plt.tight_layout()
        plt.savefig(f'{common_path}_victoria_por_candidato.png')
        plt.close()

        # Gráfica 2: Por género
        plt.figure(figsize=(10, 7))

        avg_percent_women , avg_percent_men = self.get_averages_by_sex()

        # Graficar
        bars = plt.bar(
            ['Mujeres', 'Hombres'],
            [avg_percent_women, avg_percent_men],
            color=['pink', 'lightblue'])
        plt.title(f'% Promedio de Victoria por Género {common_title}')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Añadir etiquetas con valores
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height + 1,
                     f'{height:.1f}%',
                     ha='center', va='bottom',
                     bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.2'))

        plt.tight_layout()
        plt.savefig(f'{common_path}_victoria_por_genero.png')
        plt.close()

    def get_averages_by_sex(self):

        result = tuple()
        sexes = [('mujeres', False), ('hombres', True)]
        for plural, is_man in sexes:
            candidates = {
                cand_id: candidate for cand_id, candidate
                in self.simulation_data.items()
                if candidate["is_man"] == is_man
            }
            total_wins = sum(
                self.simulation_data[cand_id]["final_winner"]
                for cand_id in candidates.keys())
            denominator = self.iterations * len(candidates)
            avg_percent = 100 * total_wins / denominator if candidates else 0
            result += (avg_percent, )
        return result

    def get_averages(
            self, seat:Seat | SeatCase, sex="mujeres", only_circuit=False):
        # fields = ["init_winner", "final_winner", "forced"]
        base_fields = [
            ("forced", "forced_probability", False),
            ("init_winner", "probability", False),
            ("final_winner", "final_probability", True),
        ]
        circuit_fields = [
            ("circuit_forced", "circuit_forced_probability", False),
            ("circuit_winner", "circuit_probability", True),
        ]
        if only_circuit:
            fields = circuit_fields
        else:
            fields = base_fields
            fields += circuit_fields
        seat_id = seat.id
        is_man = True
        if sex == 'mujeres':
            is_man = False
        sex_singular = "Hombre" if is_man else "Mujer"
        candidates = [
            cand for cand in self.simulation_data.values()
            if cand["seat"] == seat_id and cand["is_man"] == is_man
        ]
        # print(f"\nSEAT: {seat.id} - {sex} ({len(candidates)}")
        for attr, field_base, update_candidates in fields:
            total = sum([data[attr] for data in candidates])
            avg = 0
            denominator = self.iterations * len(candidates)
            if candidates:
                avg = 100 * total / denominator
            # print(f"{attr}: {avg} ({total} / {len(candidates)})")
            field = f"{field_base}_{sex}"
            if attr == 'init_winner':
                value = getattr(seat, field)
                if value != avg:
                    print(f"Seat {seat.position}-{sex} ({seat_id}) "
                          f"con un resultado distinto:  {value} --> {avg}")
            else:
                setattr(seat, field, avg)
            if update_candidates:
                seat.candidates\
                    .filter(sex=sex_singular)\
                    .update(**{field_base: avg})
        seat.save()
        return seat
