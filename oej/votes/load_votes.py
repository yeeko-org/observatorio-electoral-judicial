
import pandas as pd


class VoteLoader:

    type_positions = {
        "simple": {"group_by": []},
        "by_circunscription": {"group_by": ["CIRCUNSCRIPCION"]},
        "by_circuit": {
            "group_by": ["DISTRITO_JUDICIAL_ELECTORAL", "CIRCUITO_JUDICIAL"]
        }
    }

    positions = [
        {
            "short_name": "SCJN",
            "file_name": "MIN_2025.csv",
            "max_candidates": 64,
            "pos": None,
        },
        {
            "short_name": "TDJ",
            "file_name": "MAG_TDJ_2025.csv",
            "max_candidates": 38,
            "pos": None,
        },
        {
            "short_name": "Sala Superior TEPJF",
            "file_name": "MAG_SS_2025.csv",
            "max_candidates": 15,
            "pos": None,
        },
        {
            "short_name": "Sala Regional TEPJF",
            "file_name": "MAG_SR_2025.csv",
            "type_position": "by_circunscription",
            "max_candidates": 20,
            "pos": None,
        },
        {
            "short_name": "Juezas y Jueces",
            "file_name": "JUZ_2025.csv",
            "type_position": "by_circuit",
            "max_candidates": 50,
            "pos": None,
        },
        {
            "short_name": "Magistraturas de Circuito",
            "file_name": "MAG_TC_2025.csv",
            "type_position": "by_circuit",
            "max_candidates": 50,
            "pos": None,
        },
    ]

    def __init__(self):
        pass

    def load_positions(self):
        from django.db.models import Sum
        from oej.models import Position, Seat, Candidate
        from geo.models import State, JudicialElectoralDistrict

        for position in self.positions:
            # Create or update the position
            pos = Position.objects.get(
                short_name=position["short_name"])
            position["pos"] = pos
            file_path = f"fixture/results/{position['file_name']}"
            summary = self.get_summary(file_path, position)
            max_candidates = position.get('max_candidates', 50)
            for row in summary:
                # Create or update the position data
                seat_fields = {}
                cand_fields = {}
                seat_fields["position"] = pos
                cand_fields["seat__position"] = pos
                if "CIRCUNSCRIPCION" in row:
                    circunscription = row.pop("CIRCUNSCRIPCION")
                    seat_fields["circunscription"] = circunscription
                    cand_fields["seat__circunscription"] = circunscription
                if "DISTRITO_JUDICIAL_ELECTORAL" in row:
                    jed_number = row.pop("DISTRITO_JUDICIAL_ELECTORAL")
                    circuit = row.pop("CIRCUITO_JUDICIAL", None)
                    jed = JudicialElectoralDistrict.objects.filter(
                        number=jed_number, circuit=circuit).first()
                    seat_fields["judicial_district"] = jed
                    cand_fields["seat__judicial_district"] = jed
                candidates = Candidate.objects.filter(**cand_fields)

                for number_candidate in range(1, max_candidates + 1):
                    number = f"{number_candidate:02d}"
                    candidate_key = f'CAND{number}'
                    candidate_value = row.get(candidate_key, None)
                    if candidate_value:
                        # Create or update the candidate
                        candidate = candidates.filter(num_list=number).first()
                        if not candidate:
                            print(f"Not candidate {candidate_key} for "
                                  f"{pos.short_name} ({number}) \ {row}")
                        candidate.final_votes = int(candidate_value)
                        candidate.save()
                # candidates = Candidate.objects.filter(**cand_fields)
                voted_people = row.pop("NUMERO_PERSONAS_VOTARON", 0)
                nominal_list = row.pop("LISTA_NOMINAL_CASILLA", 0)
                seats = Seat.objects.filter(**seat_fields)
                for seat in seats:
                    votes_mujeres = seat.squares_mujeres * voted_people
                    votes_candidates_mujeres = seat.candidates.filter(
                        sex="Mujer").aggregate(
                        total_votes=Sum('final_votes'))['total_votes'] or 0
                    votes_hombres = seat.squares_hombres * voted_people
                    votes_candidates_hombres = seat.candidates.filter(
                        sex="Hombre").aggregate(
                        total_votes=Sum('final_votes'))['total_votes'] or 0
                    seat.voted_people = voted_people
                    seat.null_votes_mujeres = votes_mujeres - votes_candidates_mujeres
                    seat.null_votes_hombres = votes_hombres - votes_candidates_hombres
                    seat.nominal_list = nominal_list
                    seat.save()

    def get_summary(self, archivo_csv, position):
        """Versión simplificada"""
        df = pd.read_csv(archivo_csv)
        type_position = position.get("type_position", "simple")
        group_by = self.type_positions[type_position]["group_by"]

        # Columnas a sumar
        max_candidates = position.get('max_candidates', 50)
        candidate_cols = [
            f'CAND{i:02d}' for i in range(1, max_candidates + 1)]
        cols_sumar = (
            candidate_cols +
            ['VOTOS_NULOS', 'RECUADROS_NO_UTILIZADOS', 'TOTAL_VOTOS_CASILLA',
             'NUMERO_PERSONAS_VOTARON', 'LISTA_NOMINAL_CASILLA']
        )

        for col in cols_sumar:
            df[col] = pd.to_numeric(
                df[col], errors='coerce', downcast="integer").fillna(0)

        # Group by both SECCION and MUNICIPIO - Fixed syntax
        cols_to_sum = [col for col in cols_sumar if col in df.columns]  # Only sum existing columns
        if group_by:
            df = df.groupby(group_by, as_index=False)[cols_to_sum].sum()
        else:
            totals = df[cols_to_sum].sum().to_dict()
            df = pd.DataFrame([totals])

        result = df.to_dict(orient='records')
        return result
