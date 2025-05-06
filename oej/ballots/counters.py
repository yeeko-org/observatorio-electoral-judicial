from oej.cards.load_from_ine import LoadData
import os


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


def generate_stats():
    from oej.models import Candidate
    from django.db.models import Sum, Count, Avg, F

    candidates = Candidate.objects.filter(seat__position_id__gt=4)
    total_candidates = candidates.count()
    print(f"Total candidates: {total_candidates}")

    simple_candidates = candidates\
        .values('sex', 'seat__position__short_name')\
        .annotate(count=Count('id'))
    for obj in simple_candidates:
        print(obj)
        print(f"%{obj['count'] / total_candidates * 100:.2f}%")

    simple_candidates_by_sex = candidates\
        .values('sex')\
        .annotate(count=Count('id'))
    for obj in simple_candidates_by_sex:
        print(obj)
        print(f"%{obj['count'] / total_candidates * 100:.2f}%")

    simple_candidates_total = candidates\
        .values('sex')\
        .annotate(count_hombres=Count('final_selected_hombres'),
                  count_mujeres=Count('final_selected_mujeres'))
    for obj in simple_candidates_total:
        print(obj)
        print(f"%{obj['count_hombres'] / total_candidates * 100:.2f}%")
        print(f"%{obj['count_mujeres'] / total_candidates * 100:.2f}%")

    ranges = [
        (0, 1.5),  # derrota asegurada
        (1.5, 15),  # más de 6 competidores
        (15, 22),  # entre 5 y 6 competidores
        (15, 18),  # +- 6 competidores
        (18, 22),  # +- 5 competidores
        (22, 30),  # +- 4 competidores
        (30, 45),  # +- 3 competidores
        (45, 55), # un competidor
        (55, 85), # más de la mitad de cargos respecto a competidores
        (85, 201), # victoria asegurada
    ]

    for prob_range in ranges:
        min_value, max_value = prob_range
        candidates_by_sex = candidates.filter(
                final_probability__gte=min_value,
                final_probability__lt=max_value,
            )\
            .values('sex', 'seat__position__short_name')\
            .annotate(count=Count('id'), prob=Sum('final_probability'))
        print(f"\nRange {min_value}-{max_value}:")
        suma = 0
        prob_sum = 0
        for obj in candidates_by_sex:
            print(obj)
            suma += obj['count']
            prob_sum += obj['prob']
        print(f"{suma} - %{suma / total_candidates * 100:.2f}%")
        print(f"Probabilidad suma: {prob_sum}")


def export_csv(file_path, data):
    import csv
    with open(file_path, 'w', newline='', encoding='latin-1') as csv_file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        writer.writerows(data)


def count_by_district():
    from oej.models import Candidate, Position
    from geo.models import JudicialElectoralDistrict, State
    all_jeds = []
    circuits = {state.circuit: state for state in State.objects.all()}
    positions = Position.objects.filter(id__in=[5, 6])
    for jed in JudicialElectoralDistrict.objects.all():
        for pos in positions:
            jed_data = {
                "jed": jed.id,
                "number": jed.number,
                "state": circuits[jed.circuit].short_name,
                "position": pos.short_name,
            }
            aggregations = jed.aggregations(pos)
            jed_data.update(aggregations)
            all_jeds.append(jed_data)

    # Export to fixture/districts.csv
    csv_file_path = 'fixture/districts2.csv'
    # csv_file_path = 'fixture/easy_districts.csv'
    export_csv(csv_file_path, all_jeds)


def count_by_seat():
    from oej.models import Seat
    from api.views.export.serializers import SeatExportSerializer

    seats = Seat.objects.filter(position_id__gt=4)\
        .select_related('judicial_district__state', 'topic', 'position',
                        'judicial_district')
    serializer = SeatExportSerializer(seats, many=True)
    export_csv('fixture/seats.csv', serializer.data)


def count_by_seat_easy():
    from geo.models import JudicialElectoralDistrict, State
    from oej.models import Seat, Position
    from api.views.export.serializers import SeatExportSerializer
    easy_seats = []
    for jed in JudicialElectoralDistrict.objects.all():
        for pos in Position.objects.filter(id__gt=4):
            seats = Seat.objects.filter(judicial_district=jed, position=pos)
            if seats.count() == 1:
                easy_seat = seats.first()
                easy_seats.append(easy_seat.id)

    seats = Seat.objects.filter(position_id__gt=4, id__in=easy_seats)\
        .select_related('judicial_district__state', 'topic', 'position',
                        'judicial_district')
    serializer = SeatExportSerializer(seats, many=True)
    export_csv('fixture/easy_seats.csv', serializer.data)


def explore_1():
    from django.db.models import Sum, Count, Avg, F
    from geo.models import JudicialElectoralDistrict, State
    from oej.models import Seat, Position, Candidate

    alone_candidates = Candidate.objects.filter(
        seat__total_offices=1,
        seat__real_hombres__gt=0,
        seat__real_mujeres__gt=0)
    alone_count = alone_candidates.count()
    print(f"Alone candidates: {alone_candidates.count()}")
    loosers = alone_candidates.filter(final_probability__lt=2)
    print(f"Loosers: {loosers.count()}")
    winners = alone_candidates.filter(final_probability__gt=98)
    print(f"Winners: {winners.count()}")
    others = alone_count - (loosers.count() + winners.count())
    print(f"Others: {others}")
    genders = ["Hombre", "Mujer"]

    for gender in genders:
        gender_count = alone_candidates.filter(sex=gender).count()
        print(f"Gender {gender}: {gender_count}")


def chaotic_explore():
    from geo.models import JudicialElectoralDistrict, State
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
                .filter(final_probability__gt=2, final_probability__lt=98)\
                .exclude(final_anomaly_id='double_tie')
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


def some_equal():
    from geo.models import JudicialElectoralDistrict, State
    from oej.models import Seat, Position, Candidate
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




