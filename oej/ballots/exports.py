from oej.models import Candidate, Position, Seat


class ExportCandidates:

    def __init__(self):
        self.exported = False
        self.measures = {}

    def export_csv(self, file_path, data):
        import csv
        try:
            with open(file_path, 'w', newline='', encoding='latin-1') as csv_file:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            print(f"Error exporting to {file_path}: {e}")
            print("Data to export:", data)
            raise e

    def count_by_district(self):
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
        csv_file_path = 'fixture/districts.csv'
        # csv_file_path = 'fixture/easy_districts.csv'
        self.export_csv(csv_file_path, all_jeds)


    def export_seats(self):
        from api.views.export.serializers import SeatExportSerializer

        seats = Seat.objects.filter(position_id__gt=4)\
            .select_related('judicial_district__state', 'topic', 'position',
                            'judicial_district')\
            .order_by('id')
        serializer = SeatExportSerializer(seats, many=True)
        self.export_csv('fixture/seats.csv', serializer.data)


    def measures_by_circuit(self):
        from geo.models import State, Topic
        if self.measures:
            return
        states = State.objects.all()
        for state in states:
            circuit = state.circuit
            for pos in Position.objects.filter(by_circuit=True):
                seats = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)
                all_topics = Seat.objects.filter(
                    position=pos, judicial_district__circuit=circuit)\
                    .values_list("topic_id", flat=True).distinct()
                unique_topics = set(all_topics)
                for topic in unique_topics:
                    topic_obj = Topic.objects.get(id=topic)
                    topic_seats = seats.filter(topic=topic_obj)
                    for sex in ["Mujer", "Hombre"]:
                        key = (f"{state.short_name}_{pos.short_name}"
                               f"_{topic_obj.name}_{sex}")
                        self.add_measure(key, sex, topic_seats)

    def add_measure(self, key, sex, topic_seats):
        from django.db.models import Min, Max, Sum
        import math
        from oej.ballots.counters import find_range

        candidates = Candidate.objects\
            .filter(seat__in=topic_seats, sex=sex)\
            .aggregate(
                min=Min('circuit_probability'),
                max=Max('circuit_probability')
            )
        fields = ['total_offices', 'real_hombres', 'real_mujeres',
                  'offices_hombres', 'offices_mujeres']
        query = { aggr: Sum(aggr) for aggr in fields }
        counts = topic_seats.aggregate(**query)
        max_offices_men = math.ceil(counts["total_offices"] / 2)
        min_offices_women = math.floor(counts["total_offices"] / 2)
        minimum = candidates["min"]
        maximum = candidates["max"]
        try:
            min_range = find_range(minimum)
            max_range = find_range(maximum)
        except Exception as e:
            print("key", key)
            min_range = 0
            max_range = 0
        self.measures[key] = {
            "min": minimum,
            "max": maximum,
            "min_range": min_range,
            "max_range": max_range,
            "max_offices_men": max_offices_men,
            "min_offices_women": min_offices_women,
        }

    def export_candidates(self):
        from api.views.export.serializers import CandidateExportSerializer
        from oej.ballots.counters import find_range

        self.measures_by_circuit()
        candidates = Candidate.objects.filter(seat__position__by_circuit=True)\
            .select_related('seat__judicial_district__state',
                            'seat__topic', 'seat__position',
                            'seat__judicial_district')\
            .order_by('seat_id', 'sex', 'id')
        serializer = CandidateExportSerializer(candidates, many=True)
        data = serializer.data
        new_data = []
        for candidate in data:
            seat = candidate.pop('seat')
            position_name = seat.pop('position_name')
            state = seat.pop('state')
            new_item = {
                'seat_id': seat.pop('seat_id'),
                'state': state,
                'numero_jed': seat.pop('numero_jed'),
                'position_name': position_name,
            }
            seat.pop('probability_mujeres')
            seat.pop('probability_hombres')
            seat.pop('selected_mujeres')
            seat.pop('selected_hombres')
            seat.pop('final_selected_mujeres')
            seat.pop('final_selected_hombres')
            seat.pop('circuit_selected_mujeres')
            seat.pop('circuit_selected_hombres')
            seat.pop('final_probability_mujeres')
            seat.pop('final_probability_hombres')
            seat.pop('circuit_probability_mujeres')
            seat.pop('circuit_probability_hombres')
            candidate['real_winner'] = 1 if candidate['real_winner'] else 0
            candidate['real_winner_final'] = 1 if candidate['real_winner_final'] else 0
            candidate['real_winner_circuit'] = 1 if candidate['real_winner_circuit'] else 0
            new_item.update(candidate)
            new_item.update(seat)
            cand_prob = candidate['circuit_probability']
            cand_prob = float(cand_prob)
            new_item["cand_range"] = find_range(cand_prob)
            key = (f"{state}_{position_name}"
                   f"_{seat['materia_name']}_{candidate['sex']}")
            if key in self.measures:
                new_item.update(self.measures[key])
            else:
                print(f"Key not found: {key}")
            new_data.append(new_item)
        self.export_csv('fixture/candidates.csv', new_data)

    def export_nal_candidates(self):
        from api.views.export.serializers import CandidateNalExportSerializer
        from oej.ballots.counters import find_range

        self.measures_by_circuit()
        candidates = Candidate.objects.filter(seat__position__by_circuit=False)\
            .select_related('seat__position')\
            .order_by('seat_id', 'num_list')
        serializer = CandidateNalExportSerializer(candidates, many=True)
        data = serializer.data
        new_data = []
        for candidate in data:
            seat = candidate.pop('seat')
            position_name = seat.pop('position_name')
            circunscription = seat.pop('circunscription')
            new_item = {
                'seat_id': seat.pop('seat_id'),
                'circunscription': circunscription,
                'position_name': position_name,
            }
            new_item.update(candidate)
            new_item.update(seat)
            new_data.append(new_item)
        self.export_csv('fixture/nal_candidates.csv', new_data)


    def count_by_candidate(self):
        from api.views.export.serializers import SeatExportSerializer

        seats = Seat.objects.filter(position_id__gt=4)\
            .select_related('judicial_district__state', 'topic', 'position',
                            'judicial_district')\
            .order_by('id')
        serializer = SeatExportSerializer(seats, many=True)
        self.export_csv('fixture/seats.csv', serializer.data)


    def count_by_seat_easy(self):
        from geo.models import JudicialElectoralDistrict
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
        self.export_csv('fixture/easy_seats.csv', serializer.data)


def test_combos():
    import math
    for i in range(1, 8):
        print(f"{i} - {math.comb(8, i)}")


def suma_consecutivos(n):
    return n * (n + 1) // 2

def sum_again(comb, n, total=0, loop=None, real_n=None):
    if loop is None:
        pass
    real_comb = comb - 3
    current_range = real_comb
    if not real_n:
        real_n = n + 1 - comb
    else:
        current_range = real_n - comb + 1
    for j in range(1, current_range + 1):
        total += sum_again(comb - j, n, total, loop=loop, real_n=real_n)
        # for i in range(1, real_n + 1):
        #     count = suma_consecutivos(i)
        #     total += count
    return total

def test_sum_again():
    total = sum_again(4, 40)
    print(f"Total sum of consecutive numbers: {total}")

    total = sum_again(5, 40)
    print(f"Total sum of consecutive numbers: {total}")



def contar_combinaciones_formula(n, x):
    """
    Versión optimizada usando fórmula matemática.
    Equivale a calcular C(x-n-1, n-1) usando el teorema de stars and bars.
    """
    from math import comb

    # Verificar si es posible
    if x < n * 2:
        return 0

    # Transformamos el problema: si cada número debe ser ≥ 2,
    # podemos restar 2 de cada posición y buscar combinaciones ≥ 0
    # que sumen x - 2n
    return comb(x - n, n - 1)



# Ejemplos de uso y verificación
if __name__ == "__main__":
    # Casos de prueba
    casos = [
        (3, 40),
        (4, 40),
        (5, 40),
        (6, 40),
        (7, 40),
        (8, 40),
        (8, 50),
        (10, 50),
        (12, 50),
        (8, 100),
        (10, 100),
        (12, 100),
    ]

    print("n\tx\tRecursivo\tFórmula")
    print("-" * 40)

    for n, x in casos:
        resultado_rec = contar_combinaciones_formula(n, x)
        print(f"{n}\t{x}\t{resultado_rec}")
