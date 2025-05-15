import numpy as np
import random


def simulate_election_small_diffs(real_mujeres, real_hombres,
                                  squares_mujeres, squares_hombres,
                                  voters_size, diff_factor=0.15):
    """
    Simula una elección con pequeñas diferencias entre candidatos

    Args:
        real_mujeres: Número de candidatas mujeres
        real_hombres: Número de candidatos hombres
        squares_mujeres: Espacios para votar por mujeres
        squares_hombres: Espacios para votar por hombres
        voters_size: Número de votantes
        diff_factor: Factor de diferencia máxima (0-1)
    """
    # Crear lista de candidatos
    women_candidates = [f"Mujer_{i + 1}" for i in range(real_mujeres)]
    men_candidates = [f"Hombre_{i + 1}" for i in range(real_hombres)]

    # Probabilidad base igual para todos dentro de su grupo
    women_base_prob = 1.0 / real_mujeres
    men_base_prob = 1.0 / real_hombres

    # Preparar probabilidades con pequeñas diferencias aleatorias
    women_probs = np.array([women_base_prob] * real_mujeres)
    men_probs = np.array([men_base_prob] * real_hombres)

    # Generar pequeñas diferencias
    women_diffs = np.random.uniform(-diff_factor, diff_factor, real_mujeres) * women_base_prob
    men_diffs = np.random.uniform(-diff_factor, diff_factor, real_hombres) * men_base_prob

    # Aplicar diferencias
    women_probs += women_diffs
    men_probs += men_diffs

    # Asegurar valores no negativos
    women_probs = np.maximum(women_probs, 0.001)
    men_probs = np.maximum(men_probs, 0.001)

    # Normalizar para que sumen 1 en cada grupo
    women_probs = women_probs / women_probs.sum()
    men_probs = men_probs / men_probs.sum()

    # Simular votos
    votes = { }

    # Inicializar conteo de votos
    for candidate in women_candidates + men_candidates:
        votes[candidate] = 0

    # Simular votación
    for _ in range(voters_size):
        # Seleccionar mujeres
        selected_women = np.random.choice(
            women_candidates,
            size=squares_mujeres,
            replace=False,  # Sin reemplazo
            p=women_probs
        )

        # Seleccionar hombres
        selected_men = np.random.choice(
            men_candidates,
            size=squares_hombres,
            replace=False,  # Sin reemplazo
            p=men_probs
        )

        # Registrar votos
        for candidate in selected_women:
            votes[candidate] += 1
        for candidate in selected_men:
            votes[candidate] += 1

    return votes


def analyze_gender_imbalance(n_simulations=1000):
    """Analiza el impacto de la división de votos por género"""
    women_wins = 0
    max_women_votes = []
    max_men_votes = []

    for _ in range(n_simulations):
        # Simular con 4 mujeres, 2 hombres, 1 cuadro para cada género
        votes = simulate_election_small_diffs(
            real_mujeres=4,
            real_hombres=2,
            squares_mujeres=1,
            squares_hombres=1,
            voters_size=1000,
            diff_factor=0.15
        )

        # Separar por género
        women_votes = { k: v for k, v in votes.items() if k.startswith("Mujer") }
        men_votes = { k: v for k, v in votes.items() if k.startswith("Hombre") }

        # Encontrar máximos
        top_woman = max(women_votes.items(), key=lambda x: x[1])
        top_man = max(men_votes.items(), key=lambda x: x[1])

        max_women_votes.append(top_woman[1])
        max_men_votes.append(top_man[1])

        # Verificar victoria
        if top_woman[1] > top_man[1]:
            women_wins += 1

    # Calcular estadísticas
    win_percentage = (women_wins / n_simulations) * 100
    avg_top_woman = sum(max_women_votes) / len(max_women_votes)
    avg_top_man = sum(max_men_votes) / len(max_men_votes)
    std_top_woman = np.std(max_women_votes)
    std_top_man = np.std(max_men_votes)

    print(f"Probabilidad de victoria femenina: {win_percentage:.2f}%")
    print(f"Votación promedio mejor mujer: {avg_top_woman:.2f} ± {std_top_woman:.2f}")
    print(f"Votación promedio mejor hombre: {avg_top_man:.2f} ± {std_top_man:.2f}")

    return win_percentage, avg_top_woman, avg_top_man


def simple_dirichlet(real_mujeres, real_hombres):
    # Concentration mucho mayor (50-100) y valores uniformes
    alpha_women = np.array([50] * real_mujeres) / real_mujeres
    alpha_men = np.array([50] * real_hombres) / real_hombres

    women_probs = np.random.dirichlet(alpha_women)
    men_probs = np.random.dirichlet(alpha_men)

