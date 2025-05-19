from oej.cards.load_from_ine import LoadData
import os


def show_as_table(data):
    from prettytable import PrettyTable
    try:
        table = PrettyTable()
        table.field_names = data[0].keys()
        for row in data:
            table.add_row(row.values())
        print(table)
    except Exception as e:
        print(f"Error printing table: {e}")


def print_to_copy_to_xls(data):
    """
    Imprime los datos en un formato que se puede copiar a Excel.
    """
    for key in data[0].keys():
        print(key, end="\t")
    print()
    for row in data:
        print("\t".join(str(value) for value in row.values()))


def calc_simulated_range(
        probabilities, nivel_confianza=0.95, n_simulaciones=10000):
    from collections import Counter
    import numpy as np
    """
    Calcula el rango mediante simulación Monte Carlo (más preciso).
    Altamente optimizado para valores repetidos.
    """
    conteo_probs = Counter(probabilities)

    # Calcular victorias esperadas
    victorias_esperadas = sum(
        p * conteo for p, conteo in conteo_probs.items())

    # Simular de manera eficiente
    results = np.zeros(n_simulaciones)
    for p, conteo in conteo_probs.items():
        # Simular 'conteo' eventos con probabilidad 'p' de una vez
        try:
            results += np.random.binomial(n=conteo, p=p, size=n_simulaciones)
        except Exception as e:
            print(p, conteo)
            raise Exception(e)

    # Calcular percentiles para el intervalo del 95%
    limit_percent = (1 - nivel_confianza) / 2 * 100  # Convertir a porcentaje
    limite_inferior = np.percentile(results, limit_percent)
    limite_superior = np.percentile(results, 100 - limit_percent)
    print(victorias_esperadas)
    print(f"{limite_inferior} - {limite_superior}")
    return victorias_esperadas, limite_inferior, limite_superior


def generate_ranges(candidates=None, show_prints=True):
    from oej.models import Candidate
    from django.db.models import Sum, Count

    if not candidates:
        candidates = Candidate.objects.filter(seat__position__by_circuit=True)

    ranges = [
        [(0, 0.0001), {"idx": 0, "add": "below_left"}],  # derrota asegurada
        [(0.0001, 1), {"idx": 2, "add": "below_right"}],  # derrota asegurada
        [(1, 7), {"idx": 3}],  # competición artificial (probabilidades menores a las aparentes)
        [(7, 15), {"idx": 6}],  # más de 6 competidores
        [(15, 18), {"idx": 7}],  # +- 6 competidores
        [(18, 22), {"idx": 8}],  # +- 5 competidores
        [(22, 30), {"idx": 9}],  # +- 4 competidores
        [(30, 45), {"idx": 10}],  # +- 3 competidores
        [(45, 55), {"idx": 11}], # un competidor
        [(55, 99), {"idx": 12}], # más de la mitad de cargos respecto a competidores
        [(99, 201), {"idx": 15, "add": "above_right"}], # victoria asegurada
    ]
    all_ranges = []
    for prob_range, extra_data in ranges:
        min_value, max_value = prob_range
        range_data = {
            "title": f"De {min_value} a {max_value}",
            "hombres": 0,
            "mujeres": 0,
            "personas_electas": 0,
        }
        range_data.update(extra_data)
        candidates_by_sex = candidates.filter(
                circuit_probability__gte=min_value,
                circuit_probability__lt=max_value,
            )\
            .values('sex', 'seat__position__short_name')\
            .annotate(count=Count('id'), prob=Sum('circuit_probability'))
        suma = 0
        prob_sum = 0
        for obj in candidates_by_sex:
            suma += obj['count']
            prob_sum += obj['prob']
            if obj["sex"] == "Hombre":
                range_data["hombres"] += obj['count']
            else:
                range_data["mujeres"] += obj['count']
        range_data["personas_electas"] += prob_sum
        range_data["suma"] = suma
        all_ranges.append(range_data)
    return all_ranges


def count_candidatures(collections=None):
    import math
    if collections is None:
        collections = [
            {
                "body_short_name": "Juezas y Jueces",
                "name": "jueces",
                "json_file": "jueces_distrito.json"
            },
            {
                "body_short_name": "Magistraturas de Circuito",
                "name": "magistrados",
                "json_file": "magistraturas.json"
            },
        ]

    common_path = "G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine"
    all_dej = {}
    by_power = {
        "jueces": {1: 0, 2: 0, 3: 0, 4: 0},
        "magistrados": {1: 0, 2: 0, 3: 0, 4: 0}
    }
    for collection in collections:
        output_json = os.path.join(common_path, collection["json_file"])
        extractor = LoadData()
        name = collection["body_short_name"]
        coll_count = collection["name"]
        data = extractor.read_from_json(output_json, name)
        candidates = data.get("candidatos", [])
        for cand in candidates:
            dej = f"{cand['idCircuito']}-{cand['idDistritoJudicial']}"
            # print(f"Candidate {cand['nombreCandidato']} ({dej})")
            powers = cand.get("poderPostula", [])
            all_dej.setdefault(dej, {
                "jueces": 0,
                "magistrados": 0,
                "jueces_count": 0,
                "magistrados_count": 0,
                "jueces_pos": 0,
                "jueces_pos_real": 0,
                "magistrados_pos": 0,
                "magistrados_pos_real": 0,
                "jueces_1": 0,
                "jueces_2": 0,
                "jueces_3": 0,
                "magistrados_1": 0,
                "magistrados_2": 0,
                "magistrados_3": 0,
            })
            powers = [p for p in powers if p != 4]
            for power in powers:
                by_power[coll_count][power] += 1
                all_dej[dej][f"{coll_count}_{power}"] += 1
            all_dej[dej][coll_count] += 1
            all_dej[dej][f"{coll_count}_count"] += len(powers)

    print("Total candidatures by DEJ:")
    for dej, value in all_dej.items():
        jueces_count = max(value["jueces_1"], value["jueces_2"],
                           value["jueces_3"])
        value["jueces_pos_real"] = jueces_count / 2
        value["jueces_pos"] = math.ceil(jueces_count / 2)
        magistrados_count = max(value["magistrados_1"],
                                value["magistrados_2"],
                                value["magistrados_3"])
        value["magistrados_pos_real"] = magistrados_count / 2
        value["magistrados_pos"] = math.ceil(magistrados_count / 2)
        print(f"{dej}: {value}")
        # print(
        # f"Jueces: {value['jueces']}, Magistrados: {value['magistrados']}")

    print("Total candidatures by power:")
    for power, value in by_power.items():
        print(f"{power}: {value}")
        # print(
        # f"Jueces: {value['jueces']}, Magistrados: {value['magistrados']}")

def ballot_problems_count():
    from oej.models import Candidate, Position
    from geo.models import JudicialElectoralDistrict, State
    all_jeds = []
    circuits = {state.circuit: state for state in State.objects.all()}
    positions = Position.objects.filter(id__in=[5, 6])
    total_problems = 0
    total_districts = 0
    for jed in JudicialElectoralDistrict.objects.all():
        some_has_problems = False
        for pos in positions:
            base_candidates = Candidate.objects \
                .filter(seat__judicial_district=jed,
                        seat__position=pos)
            full = base_candidates \
                .filter(circuit_probability__gt=98).exists()
            zero = base_candidates \
                .filter(circuit_probability__lt=1).exists()
            if full or zero:
                total_problems += 1
                some_has_problems = True
        if some_has_problems:
            total_districts += 1

    print(f"total_problems", total_problems)
    print(f"total_districts", total_districts)


def explore_1():
    from oej.models import Candidate

    alone_candidates = Candidate.objects.filter(
        seat__total_offices=1,
        seat__real_hombres__gt=0,
        seat__real_mujeres__gt=0)
    alone_count = alone_candidates.count()
    print(f"Alone candidates: {alone_candidates.count()}")
    loosers = alone_candidates.filter(circuit_probability__lt=2)
    print(f"Loosers: {loosers.count()}")
    winners = alone_candidates.filter(circuit_probability__gt=98)
    print(f"Winners: {winners.count()}")
    others = alone_count - (loosers.count() + winners.count())
    print(f"Others: {others}")
    genders = ["Hombre", "Mujer"]

    for gender in genders:
        gender_count = alone_candidates.filter(sex=gender).count()
        print(f"Gender {gender}: {gender_count}")

def some_equal():
    from geo.models import JudicialElectoralDistrict
    from oej.models import Seat, Position
    full_seats = []
    all_districts = JudicialElectoralDistrict.objects.all()\
        .select_related('state')\
        .prefetch_related('seats')
    count = 0
    for jed in all_districts:
        for pos in Position.objects.filter(by_circuit=True):
            seats = Seat.objects.filter(judicial_district=jed, position=pos)
            for seat in seats:
                if not seat.real_hombres or not seat.real_mujeres:
                    continue
                if seat.total_offices == 1:
                    continue
                if seat.total_offices >= seat.real_hombres + seat.real_mujeres:
                    continue
                is_full = False
                if seat.offices_hombres == seat.real_hombres:
                    is_full = True
                    count += 1
                if seat.offices_mujeres == seat.real_mujeres:
                    is_full = True
                    count += 1
                if is_full:
                    full_seats.append(seat)

    print(f"Full seats: {len(full_seats)}")
    print(f"Count: {count}")


def total_candidates():
    range_data = generate_ranges(show_prints=True)
    show_as_table(range_data)
    print_to_copy_to_xls(range_data)


def candidates_by_sex():
    from oej.models import Candidate, Seat
    from django.db.models import Sum
    sexes = ["Mujer", "Hombre"]
    all_sexes = []
    for sex in sexes:
        print(sex)
        plural = 'mujeres' if sex == 'Mujer' else 'hombres'
        field_offices = f'offices_{plural}'
        base_candidates = Candidate.objects\
            .filter(seat__position__by_circuit=True, sex=sex)
        sex_sure_candidates = Seat.objects\
            .filter(shared_offices=0, position__by_circuit=True)\
            .aggregate(sum=Sum(field_offices))
        sure_total = sex_sure_candidates['sum']
        sex_shared_candidates = base_candidates\
            .filter(seat__shared_offices=1)\
            .values_list('circuit_probability', flat=True)
        probabilities = [
            min((cand / 100), 1) for cand in list(sex_shared_candidates)]
        victories, inf, sup = calc_simulated_range(list(probabilities))
        sex_data = {
            "sex": sex,
            "total": base_candidates.count(),
            "sure_total": sure_total,
            "victories": sure_total + victories,
            "inferior": sure_total + inf,
            "superior": sure_total + sup,
        }
        range_data = generate_ranges(sex_shared_candidates, False)
        sex_data["victory"] = range_data[-1]["suma"]
        sex_data["looser"] = range_data[0]["suma"]
        all_sexes.append(sex_data)
    show_as_table(all_sexes)
    print_to_copy_to_xls(all_sexes)


def candidates_by_power():
    from oej.models import Candidate
    from geo.models import Power
    powers = Power.objects.all()
    all_powers = []
    for power in powers:
        print(f"{power}:")
        candidates = Candidate.objects\
            .filter(seat__position__by_circuit=True, powers=power)\
            .values_list('circuit_probability', flat=True)
        probabilities = [
            min((cand / 100), 1) for cand in list(candidates)]
        victories, inf, sup = calc_simulated_range(list(probabilities))
        power_data = {
            "poder": power.name,
            "total": candidates.count(),
            "victories": victories,
            "inferior": inf,
            "superior": sup,
        }
        range_data = generate_ranges(candidates, False)
        power_data["victory"] = range_data[-1]["suma"]
        power_data["looser"] = range_data[0]["suma"]
        all_powers.append(power_data)
    show_as_table(all_powers)
    print_to_copy_to_xls(all_powers)


def candidates_by_pe_and_pl():
    from oej.models import Candidate
    from geo.models import Power
    powers = Power.objects.filter(key_name__in=["PE", "PL"])
    other_powers = Power.objects.exclude(key_name__in=["PE", "PL"])
    all_powers = []
    candidates = Candidate.objects\
        .exclude(powers__in=other_powers)\
        .filter(seat__position__by_circuit=True, powers__in=powers)
    unique_ids = set()
    probabilities = []
    for candidate in candidates:
        if candidate.id not in unique_ids:
            unique_ids.add(candidate.id)
            prob = min((candidate.circuit_probability / 100), 1)
            probabilities.append(prob)

    print(f"Unique candidates: {len(unique_ids)}")

    victories, inf, sup = calc_simulated_range(list(probabilities))
    power_data = {
        "total": len(unique_ids),
        "victories": victories,
        "inferior": inf,
        "superior": sup,
    }
    print("unique_counts", candidates.distinct().count())
    range_data = generate_ranges(candidates.distinct(), False)
    power_data["victory"] = range_data[-1]["suma"]
    power_data["looser"] = range_data[0]["suma"]
    all_powers.append(power_data)
    show_as_table(all_powers)
    print_to_copy_to_xls(all_powers)


def candidates_by_power_and_sex():
    from oej.models import Candidate
    from geo.models import Power
    powers = Power.objects.all()
    all_powers = []
    for power in powers:
        candidates = Candidate.objects\
            .filter(seat__position__by_circuit=True, powers=power)\
            .values_list('circuit_probability', flat=True)
        probabilities = [
            min((cand / 100), 1) for cand in list(candidates)]
        victories, inf, sup = calc_simulated_range(list(probabilities))
        power_data = {
            "sex": "total",
            "poder": power.name,
            "total": candidates.count(),
            "victories": victories,
        }
        range_data = generate_ranges(candidates, False)
        power_data["victory"] = range_data[-1]["suma"]
        power_data["looser"] = range_data[0]["suma"]
        all_powers.append(power_data)
        for sex in ["Hombre", "Mujer"]:
            sex_candidates = Candidate.objects\
                .filter(seat__position__by_circuit=True,
                        powers=power, sex=sex)\
                .values_list('circuit_probability', flat=True)
            probabilities = [
                min((cand / 100), 1) for cand in list(sex_candidates)]
            victories, inf, sup = calc_simulated_range(list(probabilities))
            sex_power_data = {
                "sex": sex,
                "poder": power.name,
                "total": sex_candidates.count(),
                "victories": victories,
            }
            range_data = generate_ranges(sex_candidates, False)
            sex_power_data["victory"] = range_data[-1]["suma"]
            sex_power_data["looser"] = range_data[0]["suma"]
            all_powers.append(sex_power_data)

    show_as_table(all_powers)
    print_to_copy_to_xls(all_powers)


def chaotic_explore():
    """
    Un candidato caótico es cuando tienen casi 0 o caso 100% de probabilidads
    """
    from geo.models import JudicialElectoralDistrict
    from oej.models import Seat, Position, Candidate
    chaotic_seats = []
    all_districts = JudicialElectoralDistrict.objects.all()\
        .select_related('state')\
        .prefetch_related('seats')
    for jed in JudicialElectoralDistrict.objects.all():
        for pos in Position.objects.filter(by_circuit=True):
            seats = Seat.objects.filter(judicial_district=jed, position=pos)
            all_candidates = Candidate.objects.filter(seat__in=seats)
            normal_candidates = all_candidates\
                .filter(circuit_probability__gt=2, circuit_probability__lt=98)\
                .exclude(circuit_anomaly_id='double_tie')
            cand_count = all_candidates.count()
            chaotic_count = cand_count - normal_candidates.count()
            chaotic_seats.append({
                "judicial_district": jed.id,
                "district": jed.number,
                "state": jed.state.short_name,
                "position": pos.short_name,
                "chaotic_count": chaotic_count,
                "chaotic_candidates": chaotic_count / cand_count * 100,
                "cand_count": cand_count,
                "normal_candidates": normal_candidates.count(),
            })

    sort_chaotic_seats = sorted(
        chaotic_seats, key=lambda x: x['chaotic_candidates'], reverse=True)
    for seat in sort_chaotic_seats[:30]:
        print(seat)
