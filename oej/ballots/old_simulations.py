import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm  # For progress bar (pip install tqdm if needed)
import random
from scipy.stats import zipf


def generate_varied_zipf_popularity(candidates, zipf_param=1.4, concentration_factor=10):
    """
    Genera probabilidades siguiendo una distribución similar a Zipf-Pareto pero con
    variación controlada usando la distribución Dirichlet.

    Parameters:
    - candidates: Lista de candidatos
    - zipf_param: Parámetro para la distribución Zipf (mayor = más sesgada)
    - concentration_factor: Controla la variación (menor = más variación)
    """
    # Obtener la distribución Zipf base
    n = len(candidates)
    zipf_values = zipf.pmf(range(1, n + 1), zipf_param)

    # Usar valores Zipf como parámetros de concentración para Dirichlet
    # Mayor concentration_factor significa menos variación de la distribución base
    alpha = zipf_values * concentration_factor

    # Generar probabilidades aleatorias de Dirichlet
    random_probs = np.random.dirichlet(alpha)
    # random_probs = np.random.dirichlet(zipf_values, size=1)[0]
    print(random_probs)

    # Asignar a candidatos (opcionalmente mezclar)
    shuffled_candidates = random.sample(candidates, n)
    popularity = { }
    for i, candidate in enumerate(shuffled_candidates):
        popularity[candidate] = random_probs[i]

    return popularity


def test_zipf(zipf_param=1.4, count=2, concentration_factor=10):
    candidates = list(range(1, count + 1))
    popularity = generate_varied_zipf_popularity(candidates, zipf_param, concentration_factor)
    return candidates, popularity


def chart_simulation(candidates, votes, zipf_param=1.4, iteration=None,
                     concentration_factor=None):
    # Visualizar la distribución
    plt.bar(candidates, votes.values())
    plt.xlabel(f'{len(candidates)} candidatos')
    plt.ylabel('Votos')
    title = f'Distrubución de Votos (Zipf, α={zipf_param})'
    if iteration is not None:
        title += f' - Iteración {iteration}'
    if concentration_factor is not None:
        title += f' - Factor {concentration_factor}'
    plt.title(title)
    plt.ylim(0, 1000)
    plt.show()


def chart_all_simulations(all_votes, zipf_param=1.4, concentration_factor=None):
    """
    Muestra todas las iteraciones de simulación en una sola gráfica.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    candidates = list(all_votes[0].keys())
    n_candidates = len(candidates)
    n_iterations = len(all_votes)

    # Definir ancho y posiciones para las barras
    width = 0.8 / n_iterations

    # Crear una lista de colores para cada iteración
    colors = plt.cm.viridis(np.linspace(0, 0.9, n_iterations))

    # Graficar barras para cada iteración
    for i, votes in enumerate(all_votes):
        x_pos = np.array(range(n_candidates)) + (i - n_iterations / 2 + 0.5) * width
        bars = ax.bar(x_pos, list(votes.values()), width, label=f'Iteración {i + 1}',
                      color=colors[i], alpha=0.8)

    ax.set_xlabel('Candidatos')
    ax.set_ylabel('Votos')
    ax.set_title(
        f'Distribución de Votos en Todas las Iteraciones\n(Zipf, α={zipf_param}, Factor={concentration_factor})')
    ax.set_xticks(range(n_candidates))
    ax.set_xticklabels(candidates)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.show()

def simulate_voting(popularity, voters_size, candidates, squares):
    """
    MODIFICADA: Simula votación según el modelo seleccionado
    """
    votes = { candidate: 0 for candidate in candidates }

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


def send_simulation(
        num=4, iterations=8, zipf_param=1.4, concentration_factor=10):
    """
    Parameters:
    - num: Número de candidatos
    - iterations: Número de simulaciones
    - zipf_param: Parámetro de la distribución Zipf-Pareto
    - concentration_factor: Controla cuánta variación hay en las probabilidades
                            (valores bajos = más variación)
    """
    # Mostrar la distribución Zipf base para referencia
    base_zipf = zipf.pmf(range(1, num + 1), zipf_param)
    base_zipf = base_zipf / np.sum(base_zipf)
    print("Distribución Zipf base:")
    for i, prob in enumerate(base_zipf):
        print(f"Candidato {i + 1}: {prob:.4f}")
    print()

    # Almacenar los resultados de todas las iteraciones
    all_votes = []

    for i in range(iterations):
        # Generar nuevas probabilidades para cada iteración
        cands, popularity = test_zipf(zipf_param=zipf_param, count=num,
                                      concentration_factor=concentration_factor)

        # Opcionalmente mostrar las probabilidades generadas
        print(f"Iteración {i + 1} probabilidades:")
        sorted_items = sorted(popularity.items(), key=lambda x: x[1], reverse=True)
        for candidate, prob in sorted_items:
            print(f"Candidato {candidate}: {prob:.4f}")
        print()

        votes = simulate_voting(popularity, 1000, cands, 1)
        all_votes.append(votes)

    # Mostrar una única gráfica con todas las iteraciones
    chart_all_simulations(all_votes, zipf_param=zipf_param,
                          concentration_factor=concentration_factor)

def main_old():
    # Definir los parámetros de la simulación
    num_candidates = 4
    iterations = 10
    zipf_param = 1.4
    # concentration_factors = [2, 3, 4, 5, 10, 15, 30]  # Diferentes factores de concentración para probar
    concentration_factors = [12, 15, 18, 22, 26, 30]

    # Ejecutar la simulación
    for concentration_factor in concentration_factors:
        send_simulation(
            num=num_candidates,
            iterations=iterations,
            zipf_param=zipf_param,
            concentration_factor=concentration_factor
        )

