import json
import os
import re
from oej.models import Position, Seat, Candidate
from utils.common import text_normalizer
from django.conf import settings
from oej.cards.load_candidates import LoadCandidates


class LoadData(LoadCandidates):

    def __init__(self):
        self.ine_path = 'https://candidaturaspoderjudicial.ine.mx/cycc'
        super().__init__()

    def update_candidates(self):
        saved_candidates = {
            c.full_name_normalized: c for c in Candidate.objects.all()}

        candidates = self.data.get("candidatos", [])
        social_networks = self.data.get("redesSociales", [])
        social_networks_by_candidate = {}
        for social_network in social_networks:
            id_ine = social_network.pop("idCandidato")
            social_networks_by_candidate.setdefault(id_ine, [])
            social_networks_by_candidate[id_ine].append(social_network)
        success_count = 0
        for candidate in candidates:
            name = candidate.get("nombreCandidato")
            normalized_name = text_normalizer(name)
            id_ine = candidate.get("idCandidato")
            if normalized_name in saved_candidates:
                candidate_obj = saved_candidates[normalized_name]
                if candidate_obj.id_ine and candidate_obj.ine_cv:
                    continue
            else:
                print(f"Candidate {normalized_name} not found ({id_ine})")
                continue
            social_networks = social_networks_by_candidate.get(id_ine, [])
            candidate["redesSociales"] = social_networks
            num_list = candidate.get("numListaBoleta")
            if img_name := candidate.get("urlFoto"):
                img_url = img_name.replace("/media/cycc", self.ine_path)
                candidate_obj.ine_photo = img_url
            if pdf_name := candidate.get("descripcionHLC"):
                pdf_url = f"{self.ine_path}/documentos/cv/{pdf_name}"
                candidate_obj.ine_cv = pdf_url
            candidate_obj.id_ine = id_ine
            candidate_obj.num_list = num_list
            candidate_obj.ine_data = candidate
            candidate_obj.save()
            success_count += 1
            # example: "/media/cycc/img/fotocandidato/4106.jpg"
        print(f"Success count: {success_count}/{len(candidates)}")
        # https://candidaturaspoderjudicial.ine.mx/cycc/documentos/cv/CV_4106.pdf
        # https://candidaturaspoderjudicial.ine.mx/cycc/img/fotocandidato/4106.jpg


# if __name__ == "__main__":
def main_load(collections=None):
    if collections is None:
        collections = [
            {
                "body_short_name": "SCJN",
                "json_file": "scjn.json"
            },
            {
                "body_short_name": "Sala Superior TEPJF",
                "json_file": "sala_superior.json"
            },
            {
                "body_short_name": "Sala Regional TEPJF",
                "json_file": "salas_regionales.json"
            },
            {
                "body_short_name": "TDJ",
                "json_file": "tdj.json"
            }
        ]

    if settings.IS_LOCAL:
        common_path = "G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine"
    else:
        common_path = "fixture/conoceles_ine"
    for collection in collections:
        output_json = os.path.join(common_path, collection["json_file"])
        extractor = LoadData()
        name = collection["body_short_name"]
        extractor.read_from_json(output_json, name)
        extractor.update_candidates()

