import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Patch
from scipy.stats import zipf
from oej.models import Seat


class ElectionSimulator:

    def __init__(self, show_results=True):
        self.iterations = 1000
        # Nuevo parámetro para indicar el tipo de simulación
        self.simulation_type = "random"  # Opciones: "random", "strategic", "zipf_pareto"
        # Parámetro para distribución Zipf
        self.zipf_param = 1.3  # Controla qué tan pronunciada es la "cola larga"
        self.popularity_women = {}
        self.popularity_men = {}
        self.show_results = show_results
        self.case_results = {
            '0-2-0-1-1-1-0-0': (0, 50.0),
            '0-3-0-1-1-1-0-0': (0, 33.333333333333336),
            '0-4-0-1-1-1-0-0': (0, 25.0),
            '0-5-0-1-1-1-0-0': (0, 20.0),
            '0-6-0-1-1-1-0-0': (0, 16.666666666666668),
            '2-3-1-1-1-1-0-0': (49.3, 0.4666666666666667),
            '2-4-1-1-1-1-0-0': (50.0, 0.0),
            '2-5-1-1-1-1-0-0': (50.0, 0.0),
            '3-2-1-1-1-1-0-0': (0.7, 48.95),
            '3-4-1-1-1-1-0-0': (28.2, 3.85),
            '4-2-1-1-1-1-0-0': (0.025, 49.95),
            '4-3-1-1-1-1-0-0': (4.125, 27.833333333333332),
            '5-2-1-1-1-1-0-0': (0.0, 50.0),
            '5-3-1-1-1-1-0-0': (1.1, 31.5),
            '6-2-1-1-1-1-0-0': (0.0, 50.0)
        }

    def simulate_elections(
            self, cases=None, simulation_type="random", zipf_param=1.4):
        """
        Función principal que coordina la simulación
        """
        # Actualizar el tipo de simulación
        self.simulation_type = simulation_type
        self.zipf_param = zipf_param

        # Definir casos (mantiene tu código original)
        if not cases:
            cases = [
                {
                    "real_mujeres": 3, "real_hombres": 5,
                    "squares_mujeres": 1, "squares_hombres": 1,
                    "total_offices": 3
                },
                {
                    "real_mujeres": 3, "real_hombres": 4,
                    "squares_mujeres": 1, "squares_hombres": 1,
                    "total_offices": 3
                },
                {
                    "real_mujeres": 1, "real_hombres": 2,
                    "squares_mujeres": 1, "squares_hombres": 1,
                    "total_offices": 1
                },
            ]

        # Ejecutar cada caso
        for idx, case in enumerate(cases):
            case, shared_offices = self.calculate_office_allocation(case)
            self.run_simulation_case(case, shared_offices, idx)

    def calculate_seat(self, seat:Seat):
        self.show_results = False
        self.simulation_type = "zipf_pareto"
        self.zipf_param = 1.4
        case = {
            "real_mujeres": seat.real_mujeres,
            "real_hombres": seat.real_hombres,
            "squares_mujeres": seat.squares_mujeres,
            "squares_hombres": seat.squares_hombres,
            "total_offices": seat.total_offices,
            "shared_offices": seat.shared_offices,
            "offices_mujeres": seat.offices_mujeres,
            "offices_hombres": seat.offices_hombres,
        }
        return self.run_simulation_case(case, seat.shared_offices)

    def run_simulation_case(self, case, shared_offices, idx=0):
        # Calcular asignación de cargos (mantiene tu función original)

        if shared_offices:
            if case["real_mujeres"] == case["real_hombres"]:
                average = 1 / (case["real_mujeres"] + case["real_hombres"]) * 100
                return average, average

            values = case.values()
            # Generar una clave única para el caso con un join -
            key = "-".join([str(value) for value in values])
            if not self.show_results and key in self.case_results:
                return self.case_results[key]

            print(f"\nCaso {idx + 1}: {case}")
            print(f"Tipo de simulación: {self.simulation_type} (α={self.zipf_param})")

            # Realizar simulaciones
            result = self.run_simulations(case)
            winners_count, candidates_women, candidates_men = result

            if self.show_results:
                # Visualizar resultados
                self.visualize_results(
                    case, winners_count, candidates_women, candidates_men, idx
                )
            else:
                avg_percent_women, avg_percent_men = self.get_averages_by_sex(
                    winners_count, candidates_women, candidates_men
                )
                self.case_results[key] = (avg_percent_women, avg_percent_men)
                return avg_percent_women, avg_percent_men
        avg_percent_women = 0
        avg_percent_men = 0
        if case["real_mujeres"] > 0:
            avg_percent_women = case["offices_mujeres"] / case["real_mujeres"] * 100
        if case["real_hombres"] > 0:
            avg_percent_men = case["offices_hombres"] / case["real_hombres"] * 100
        return avg_percent_women, avg_percent_men

    def calculate_office_allocation(self, case):
        """
        Función 2: Calcula la asignación de espacios por género
        """
        import math
        total_offices = case["total_offices"]
        real_mujeres = case["real_mujeres"]
        real_hombres = case["real_hombres"]
        offices_mujeres = 0
        offices_hombres = 0

        # Inicializar valores
        shared_offices = 0

        if real_hombres == 0:
            offices_mujeres = total_offices
        elif total_offices == 1:
            shared_offices = 1
        else:
            min_women = math.ceil(total_offices / 2)
            offices_mujeres = min(min_women, real_mujeres)
            offices_hombres = total_offices - offices_mujeres

        case["shared_offices"] = shared_offices
        case["offices_mujeres"] = offices_mujeres
        case["offices_hombres"] = offices_hombres
        return case, shared_offices

    def run_simulations(self, case):
        """
        Ejecuta las simulaciones con diferentes modelos
        """

        # Crear IDs para candidatos (mujeres 1-n, hombres 101-n)
        candidates_women = list(range(1, case["real_mujeres"] + 1))
        candidates_men = list(range(101, case["real_hombres"] + 101))

        # Para cada tamaño de votantes
        # small_size = max(5, case["total_offices"] + 3)
        voters_size = 200
        # Inicializar contador de victorias
        winners_count = {}
        for candidate in candidates_women + candidates_men:
            winners_count[candidate] = 0

        # Ejecutar las iteraciones
        for iteration in range(self.iterations):

            # Inicializar popularidades según modelo de votación
            if self.simulation_type == "zipf_pareto":
                # Generar popularidades para mujeres y hombres siguiendo Zipf
                self.popularity_women = self.generate_zipf_popularity(
                    candidates_women)
                self.popularity_men = self.generate_zipf_popularity(
                    candidates_men)

            # Simular votación según el modelo seleccionado
            votes_women = self.simulate_voting(
                voters_size, candidates_women, case["squares_mujeres"], "women")
            votes_men = self.simulate_voting(
                voters_size, candidates_men, case["squares_hombres"], "men")

            # [Resto del código de asignación de ganadores sin cambios]
            winners_women = self.determine_winners(
                votes_women, case["offices_mujeres"])
            winners_men = self.determine_winners(
                votes_men, case["offices_hombres"])
            all_winners = winners_men + winners_women

            shared_offices = case["shared_offices"]
            if shared_offices > 0:
                all_votes = votes_women.copy()
                all_votes.update(votes_men)
                all_winners = self.assign_remaining_winners(
                    all_winners, shared_offices, all_votes
                )

            for winner in all_winners:
                winners_count[winner] += 1
        return winners_count, candidates_women, candidates_men


    def generate_zipf_popularity(self, candidates):
        """
        NUEVA FUNCIÓN: Genera distribución de popularidad siguiendo Zipf
        """
        # Generar valores Zipf para cada candidato
        n = len(candidates)
        zipf_values = zipf.pmf(range(1, n + 1), self.zipf_param)

        # Normalizar para asegurar que sumen 1
        zipf_values = zipf_values / np.sum(zipf_values)

        # Asignar valores a candidatos (orden aleatorio para no favorecer por ID)
        shuffled_candidates = random.sample(candidates, n)
        popularity = { }
        for i, candidate in enumerate(shuffled_candidates):
            popularity[candidate] = zipf_values[i]

        return popularity

    def simulate_voting(self, voters_size, candidates, squares, gender):
        """
        MODIFICADA: Simula votación según el modelo seleccionado
        """
        votes = { candidate: 0 for candidate in candidates }

        # Selección según el tipo de simulación
        if self.simulation_type == "random":
            # Método original: selección aleatoria uniforme
            for _ in range(voters_size):
                if len(candidates) <= squares:
                    selected = candidates
                else:
                    selected = random.sample(candidates, squares)

                for candidate in selected:
                    votes[candidate] += 1

        elif self.simulation_type == "zipf_pareto":
            # Selección basada en popularidad Zipf/Pareto
            popularity = self.popularity_women if gender == "women" \
                else self.popularity_men
            for _ in range(voters_size):
                if len(candidates) <= squares:
                    selected = candidates
                else:
                    # Selección ponderada según popularidad
                    selected = np.random.choice(
                        candidates,
                        size=squares,
                        replace=False,
                        p=[popularity[c] for c in candidates]
                    )

                for candidate in selected:
                    votes[candidate] += 1

        return votes

    def determine_winners(self, votes, offices):
        """Mantiene tu implementación original"""
        # [Código existente sin cambios]
        sorted_by_sex = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        offices = min(offices, len(votes))
        winners = [candidate for candidate, _ in sorted_by_sex[:offices]]
        return winners

    def assign_remaining_winners(self, all_winners, shared_offices, all_votes):
        """Mantiene tu implementación original"""
        # [Código existente sin cambios]
        final_votes_remaining = { }
        remaining_candidates = [c for c in all_votes if c not in all_winners]
        for c in remaining_candidates:
            final_votes_remaining[c] = all_votes[c]
        sorted_remaining = sorted(
            final_votes_remaining.items(), key=lambda x: x[1], reverse=True)
        shared_offices = min(shared_offices, len(sorted_remaining))
        for candidate, _ in sorted_remaining[:shared_offices]:
            all_winners.append(candidate)
        return all_winners

    def visualize_results(
            self, case, winners_count, candidates_women, candidates_men, idx
    ):
        """MODIFICADA: Incluye tipo de simulación en el título"""
        # [Código similar al original con adición del tipo de simulación]
        # Gráfica 1: Por candidato individual
        squares_mujeres = case["squares_mujeres"]
        squares_hombres = case["squares_hombres"]
        total_offices = case["total_offices"]
        plt.figure(figsize=(14, 7))
        candidates = sorted(winners_count.keys())
        wins = [winners_count[c] for c in candidates]
        percentages = [100 * w / self.iterations for w in wins]
        colors = ['pink' if c < 100 else 'lightblue' for c in candidates]

        bars = plt.bar(range(len(candidates)), percentages, color=colors)
        plt.xticks(range(len(candidates)), candidates, rotation=90)
        shared_offices = case["shared_offices"]

        # Añadir tipo de simulación al título
        common_title = f' ({self.simulation_type}) '
        if self.simulation_type == "zipf_pareto":
            common_title += f' (α={self.zipf_param}) '
        common_title += (
            f'\n[{squares_mujeres}][{shared_offices}][{squares_hombres}] '
            f' ({total_offices})')
        plt.title(f'% Victoria por Candidato {common_title}')

        plt.ylabel('Porcentaje de Victoria (%)')
        plt.xlabel('ID Candidato')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        common_path = f"fixture/charts/case{idx+1}_{self.simulation_type}"
        if self.simulation_type == "zipf_pareto":
            common_path += f"_zipf_{self.zipf_param}"

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

        avg_percent_women , avg_percent_men = self.get_averages_by_sex(
            winners_count, candidates_women, candidates_men
        )

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

    def get_averages_by_sex(
            self, winners_count, candidates_women, candidates_men):

        avg_percent_women = 0
        avg_percent_men = 0
        if candidates_women:
            total_wins_women = sum(winners_count[c] for c in candidates_women)
            avg_percent_women = (
                    100 * total_wins_women /(self.iterations * len(candidates_women)))

        if candidates_men:
            total_wins_men = sum(winners_count[c] for c in candidates_men)
            avg_percent_men = (
                    100 * total_wins_men / (self.iterations * len(candidates_men)))
        return avg_percent_women, avg_percent_men

