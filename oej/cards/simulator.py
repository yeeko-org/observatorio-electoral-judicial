import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Patch


class ElectionSimulator:
    def __init__(self):
        # Definimos las variables globales para los tamaños de votantes y número de iteraciones
        self.iterations = 1000

    def simulate_elections(self, cases=None):
        """
        Función principal que coordina la simulación de los 4 casos de estudio
        """
        # Definir los 4 casos con sus parámetros específicos
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
                    "real_mujeres": 3, "real_hombres": 4,
                    "squares_mujeres": 1, "squares_hombres": 1,
                    "total_offices": 1
                },
            ]

        # Ejecutar cada caso
        for i, case in enumerate(cases):
            print(f"\nCaso {i + 1}: {case}")

            # Calcular asignación de cargos
            offices_hombres, offices_mujeres, shared_offices = self.calculate_office_allocation(
                case["real_mujeres"], case["real_hombres"],
                case["squares_mujeres"], case["squares_hombres"],
                case["total_offices"]
            )

            print(f"Espacios asegurados para mujeres: {offices_mujeres}")
            print(f"Espacios asegurados para hombres: {offices_hombres}")
            print(f"Espacios compartidos: {shared_offices}")

            # Realizar las simulaciones con diferentes tamaños y iteraciones
            self.run_simulations(
                case["real_mujeres"], case["real_hombres"],
                case["squares_mujeres"], case["squares_hombres"],
                offices_mujeres, offices_hombres, shared_offices,
                case["total_offices"], i
            )

    def calculate_office_allocation(self, real_mujeres, real_hombres, squares_mujeres, squares_hombres, total_offices):
        """
        Función 2: Calcula la asignación de espacios por género
        """
        # Calcular el total de espacios para votar
        squares_total = squares_mujeres + squares_hombres

        # Inicializar valores
        offices_mujeres = 0
        offices_hombres = 0
        shared_offices = 0

        # Caso 1: squares_total igual a total_offices
        if squares_total == total_offices:
            offices_mujeres = squares_mujeres
            offices_hombres = squares_hombres

        # Caso 2: Hay más cargos que espacios
        elif total_offices > squares_total:
            offices_mujeres = squares_mujeres
            offices_hombres = squares_hombres
            shared_offices = total_offices - squares_total

        # Caso 3: Solo un cargo y dos espacios
        elif total_offices == 1 and squares_total == 2:
            shared_offices = 1
            offices_mujeres = 0
            offices_hombres = 0

        # Otros casos (si hay más espacios que cargos)
        else:
            # Asignamos proporcionalmente
            ratio_mujeres = squares_mujeres / squares_total
            offices_mujeres = int(ratio_mujeres * total_offices)
            offices_hombres = total_offices - offices_mujeres

        return offices_hombres, offices_mujeres, shared_offices

    def run_simulations(
            self, real_mujeres, real_hombres, squares_mujeres, squares_hombres,
            offices_mujeres, offices_hombres, shared_offices, total_offices,
            idx
    ):
        """
        Función 3: Ejecuta las simulaciones con diferentes tamaños y números de iteraciones
        """
        # Crear IDs para candidatos (mujeres 1-n, hombres 101-n)
        candidates_women = list(range(1, real_mujeres + 1))
        candidates_men = list(range(101, real_hombres + 101))

        # Para cada tamaño de votantes
        small_size = max(5, total_offices + 3)
        voter_sizes = [small_size, 200]
        for voters_size in voter_sizes:
            # Inicializar contador de victorias
            winners_count = {}
            for candidate in candidates_women + candidates_men:
                winners_count[candidate] = 0

            # Ejecutar las iteraciones
            for _ in range(self.iterations):
                # Simular una votación
                votes_women = self.simulate_voting(
                    voters_size, candidates_women, squares_mujeres)
                votes_men = self.simulate_voting(
                    voters_size, candidates_men, squares_hombres)

                winners_women = self.determine_winners(votes_women, offices_mujeres)
                winners_men = self.determine_winners(votes_men, offices_hombres)
                all_winners = winners_men + winners_women
                # Asignar espacios compartidos si existen
                if shared_offices > 0:
                    all_votes = votes_women.copy()
                    all_votes.update(votes_men)

                    all_winners = self.assign_remaining_winners(
                        all_winners, shared_offices, all_votes
                    )

                for winner in all_winners:
                    winners_count[winner] += 1

            # Visualizar resultados
            self.visualize_results(
                winners_count, voters_size,
                squares_mujeres, squares_hombres, total_offices,
                candidates_women, candidates_men, idx
            )

    def simulate_voting(self, voters_size, candidates, squares):
        """
        Función 4: Simula la votación con un número específico de votantes
        """
        votes = { candidate: 0 for candidate in candidates }

        # Cada votante debe votar por el número exacto de candidatos
        # según los cuadros disponibles
        for _ in range(voters_size):
            if len(candidates) <= squares:
                selected = candidates
            else:
                selected = random.sample(candidates, squares)

            for candidate in selected:
                votes[candidate] += 1

        return votes

    def determine_winners(self, votes, offices):
        """
        Función 5: Determina los ganadores según los votos obtenidos
        """
        sorted_by_sex = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        # Ajustar si hay menos candidatos que espacios disponibles
        offices = min(offices, len(votes))
        # Asignar espacios reservados
        winners = [candidate for candidate, _ in sorted_by_sex[:offices]]

        return winners

    def assign_remaining_winners(self, all_winners, shared_offices, all_votes):

        final_votes_remaining = { }
        remaining_candidates = [c for c in all_votes if c not in all_winners]
        for c in remaining_candidates:
            final_votes_remaining[c] = all_votes[c]
        # Ordenar por votos (mayor a menor)
        sorted_remaining = sorted(
            final_votes_remaining.items(), key=lambda x: x[1], reverse=True)

        # Asignar cargos compartidos
        shared_offices = min(shared_offices, len(sorted_remaining))
        for candidate, _ in sorted_remaining[:shared_offices]:
            all_winners.append(candidate)

        return all_winners

    def visualize_results(
            self, winners_count, voters_size, squares_mujeres,
            squares_hombres, total_offices, candidates_women, candidates_men,
            idx
    ):
        """
        Función 6: Genera y visualiza gráficas de barras con los resultados
        """
        # Gráfica 1: Por candidato individual
        plt.figure(figsize=(14, 7))

        # Preparar datos
        candidates = sorted(winners_count.keys())
        wins = [winners_count[c] for c in candidates]
        percentages = [100 * w / self.iterations for w in wins]

        # Colores para cada sexo
        colors = ['pink' if c < 100 else 'lightblue' for c in candidates]

        # Graficar
        bars = plt.bar(range(len(candidates)), percentages, color=colors)
        plt.xticks(range(len(candidates)), candidates, rotation=90)
        shared_offices = max(0, total_offices - squares_mujeres - squares_hombres)
        plt.title(f'% Victoria por Candidato \n{voters_size} votantes - '
                  f'[{squares_mujeres}][{shared_offices}][{squares_hombres}] '
                  f' ({total_offices})')
        plt.ylabel('Porcentaje de Victoria (%)')
        plt.xlabel('ID Candidato')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        common_path = f"fixture/charts/case{idx}_v{voters_size}"

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

        # Calcular totales por género
        total_wins_women = sum(winners_count[c] for c in candidates_women)
        total_wins_men = sum(winners_count[c] for c in candidates_men)

        # Calcular porcentajes
        # denominator = iterations * total_offices
        avg_percent_women = (
                100 * total_wins_women /(self.iterations * len(candidates_women)))
        avg_percent_men = (
                100 * total_wins_men / (self.iterations * len(candidates_men)))

        # Graficar
        bars = plt.bar(['Mujeres', 'Hombres'], [avg_percent_women, avg_percent_men], color=['pink', 'lightblue'])
        plt.title(f'% Promedio de Victoria por Género \n{voters_size} votantes - '
                  f'[{squares_mujeres}][{shared_offices}][{squares_hombres}] '
                  f' ({total_offices})')
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


# Ejecutar la simulación
if __name__ == "__main__":
    simulator = ElectionSimulator()
    simulator.simulate_elections()