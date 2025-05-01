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

    def update_candidates(self, is_create=False):
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
                # if candidate_obj.id_ine and candidate_obj.ine_cv:
                #     continue
            elif not is_create:
                print(f"Candidate {normalized_name} not found ({id_ine})")
                continue
            else:
                candidate_obj = Candidate()
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


# if __name__ == "__main__":
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

