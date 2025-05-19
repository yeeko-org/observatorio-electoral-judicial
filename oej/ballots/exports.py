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
    csv_file_path = 'fixture/districts.csv'
    # csv_file_path = 'fixture/easy_districts.csv'
    export_csv(csv_file_path, all_jeds)


def export_seats():
    from oej.models import Seat
    from api.views.export.serializers import SeatExportSerializer

    seats = Seat.objects.filter(position_id__gt=4)\
        .select_related('judicial_district__state', 'topic', 'position',
                        'judicial_district')\
        .order_by('id')
    serializer = SeatExportSerializer(seats, many=True)
    export_csv('fixture/seats.csv', serializer.data)


def export_candidates():
    from oej.models import Candidate
    from api.views.export.serializers import CandidateExportSerializer

    candidates = Candidate.objects.filter(seat__position_id__gt=4)\
        .select_related('seat__judicial_district__state',
                        'seat__topic', 'seat__position',
                        'seat__judicial_district')\
        .order_by('seat_id', 'sex', 'id')
    serializer = CandidateExportSerializer(candidates, many=True)
    data = serializer.data
    new_data = []
    for candidate in data:
        seat = candidate.pop('seat')
        new_item = {
            'seat_id': seat.pop('seat_id'),
            'state': seat.pop('state'),
            'numero_jed': seat.pop('numero_jed'),
            'position_name': seat.pop('position_name')
        }
        seat.pop('probability_mujeres')
        seat.pop('probability_hombres')
        seat.pop('final_probability_mujeres')
        seat.pop('final_probability_hombres')
        seat.pop('circuit_probability_mujeres')
        seat.pop('circuit_probability_hombres')
        new_item.update(candidate)
        new_item.update(seat)
        new_data.append(new_item)
    export_csv('fixture/candidates.csv', new_data)


def count_by_candidate():
    from oej.models import Seat, Candidate
    from api.views.export.serializers import SeatExportSerializer

    seats = Seat.objects.filter(position_id__gt=4)\
        .select_related('judicial_district__state', 'topic', 'position',
                        'judicial_district')\
        .order_by('id')
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
