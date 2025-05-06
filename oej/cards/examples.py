# main()

def get_find_names(first_name):
    import re
    find_names = first_name.split(" ")
    final_names = []
    for name in find_names:
        clean_name = re.sub(r"[^a-zA-Z]", "", name)
        if clean_name in ["MA", "M"]:
            clean_name = "MARIA"
        elif len(clean_name) <= 2:
            continue
        elif clean_name in ["DEL", "LOS"]:
            continue
        final_names.append(clean_name)
    return final_names


def update_all_candidates():
    from oej.models import Candidate
    candidates = Candidate.objects.all()
    for candidate in candidates:
        candidate.save_image_from_url()
        candidate.save()


def update_num_list(position_id=2, circunscription_id=None):
    from oej.models import Candidate
    candidates = Candidate.objects\
        .filter(seat__position_id=position_id)\
        .order_by('-sex', 'last_name_1', 'last_name_2', 'first_name')
    if circunscription_id:
        candidates = candidates\
            .filter(seat__circunscription_id=circunscription_id)
    for (num, candidate) in enumerate(candidates, start=1):
        num_list = str(num).zfill(2)
        candidate.num_list = num_list
        candidate.save()

# update_num_list(2)
def update_by_circunscription():
    from oej.models import Circunscription
    for circunscription in Circunscription.objects.all():
        update_num_list(position_id=4, circunscription_id=circunscription.id)

def update_all_biographies():
    from oej.models import Biography
    biographies = Biography.objects.all()
    for biography in biographies:
        biography.save()


def reset_status_candidates():
    from oej.models import Candidate
    candidates = Candidate.objects.filter(status_register_id='need_new_checking')
    print(candidates.count())
    candidates.update(
        first_year=None,
        gemini_text=None,
        price=None,
        price_details=None,
        academic_ia=None,
        academic_text=None,
        professional_ia=None,
        professional_text=None,
        more_info_ia=None,
        more_info_text=None,
        judgments=None,
        comments=None,
        sources=None,
        status_register=None,
    )


def explore_cedules():
    from oej.cards.cedule_sep import (
        search_special_candidates, explore_new_cedules)
    search_special_candidates()
    explore_new_cedules(2)
    explore_new_cedules(4)


def recover_references():
    from oej.models import Candidate
    from oej.sonar.sonar_research import SonarResearch
    sonar = SonarResearch(ai_company='openai', engine='gpt-4o-2024-11-20')
    candidates = Candidate.objects.filter(
        more_info_text__isnull=False, more_info_ia__isnull=True)
    print("Total candidates:", candidates.count())
    for candidate in candidates:
        sonar.build_prompt("oej/sonar/recover_references.txt")
        user_prompt = (f"REPORTE COMPLETO:\n\n{candidate.gemini_text}\n\n"
                       f"HALLAZGOS:\n\n{candidate.more_info_text}")
        result = sonar.send_prompt(user_prompt)
        if not result:
            print(f"No result for candidate {candidate}")
            continue
        candidate.more_info_ia = result
        candidate.save()
        print(f"Candidate {candidate} updated")


def load_pdf_content(pos_id=2, limit=10):
    import fitz  # PyMuPDF
    import requests
    import io
    from oej.models import Candidate
    candidates = Candidate.objects.filter(
        seat__position_id=pos_id, ine_cv__isnull=False,
        ine_cv_text__isnull=True)
    for candidate in candidates[:limit]:
        print(f"Processing candidate {candidate}")
        file_path = candidate.ine_cv
        response = requests.get(file_path)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            continue
        pdf_file = io.BytesIO(response.content)
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text", flags=fitz.TEXT_INHIBIT_SPACES)
            all_text += f"\n\n{page_text}"
        candidate.ine_cv_text = all_text
        candidate.save()

# load_pdf_content(4, 200)



def build_candidate_json_report():
    import json
    import csv
    from oej.models import Candidate

    final_data = []
    candidates = Candidate.objects.all().order_by("id")
    for candidate in candidates:
        social_accounts = candidate.social_accounts.all()
        facebook = social_accounts.filter(
            social_network__name="Facebook").first()
        twitter = social_accounts.filter(
            social_network__name="Twitter").first()
        instagram = social_accounts.filter(
            social_network__name="Instagram").first()
        candidate_data = {
            "id": candidate.id,
            "position": candidate.seat.position.full_name,
            "first_name": candidate.first_name,
            "last_name_1": candidate.last_name_1,
            "last_name_2": candidate.last_name_2,
            "full_name": candidate.full_name,
            "sex": candidate.sex,
            "twitter": twitter.url if twitter else None,
            "facebook": facebook.url if facebook else None,
            "instagram": instagram.url if instagram else None,
        }
        final_data.append(candidate_data)

    # EXPORT DATA TO CSV
    csv_file_path = 'fixture/candidates.csv'
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        if final_data:
            fieldnames = final_data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for candidate in final_data:
                writer.writerow(candidate)

    # EXPORT DATA TO JSON
    json_file_path = 'fixture/candidates.json'
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_data, json_file, ensure_ascii=False, indent=4)


def exports():
    from oej.ballots.counters import count_by_district, count_by_seat
    count_by_district()
    count_by_seat()


def main():
    from oej.ballots.find_cases import ResearchCases
    research = ResearchCases()
    research.pre_load()
    research.load_districts()
    research.analyze_seats()
    research.calc_selected()
    research.post_gender_equity()


def exec_chaotic():
    from oej.ballots.counters import chaotic_explore
    chaotic_explore()


def prev_main():
    from oej.ballots.find_cases import ResearchCases
    research = ResearchCases()
    research.pre_load()
    research.load_districts()
    research.load_candidates()
    research.process_all_districts()


def start_simulator():
    from oej.ballots.simulator import ElectionSimulator
    simulator = ElectionSimulator()

    cases = [
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 1, "real_mujeres": 1 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 1, "real_mujeres": 2 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 1, "real_mujeres": 3 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 2, "real_mujeres": 2 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 2, "real_mujeres": 3 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 2, "real_mujeres": 4 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 2, "real_mujeres": 5 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 3, "real_mujeres": 3 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 3, "real_mujeres": 4 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 3, "real_mujeres": 5 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 3, "real_mujeres": 6 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 4, "real_mujeres": 4 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 4, "real_mujeres": 5 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 4, "real_mujeres": 6 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 4, "real_mujeres": 7 },
        { "total_offices": 1, "squares_hombres": 1, "squares_mujeres": 1, "real_hombres": 4, "real_mujeres": 8 },
    ]

    # Ejecutar con distribución aleatoria (original)
    simulator.simulate_elections(cases, simulation_type="random")

    # Ejecutar con voto estratégico
    # simulator.simulate_elections(simulation_type="strategic")

    # Ejecutar con distribución Zipf/Pareto
    # simulator.simulate_elections(
    #     simulation_type="zipf_pareto", zipf_param=1.3)
    simulator.simulate_elections(
        cases, simulation_type="zipf_pareto", zipf_param=1.5)
    # simulator.simulate_elections(
    #     simulation_type="zipf_pareto", zipf_param=1.6)


def read_from_txt():
    import os

    common_path = "fixture\social_listening"

    file_path = os.path.join(common_path, "all_keywords.txt")
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    keywords_count = {}

    for line in lines:
        keywords = line.split(";")
        for keyword in keywords:
            if keyword.startswith("@"):
                continue
            keyword = keyword.strip()
            keyword = keyword.lower()
            keywords_count.setdefault(keyword, 0)
            keywords_count[keyword] += 1

    sorted_keywords = sorted(
        keywords_count.items(), key=lambda x: x[1], reverse=True)

    for keyword, count in sorted_keywords[:30]:
        print(f"{keyword}: {count}")


def load_site_url():
    import requests
    page_url = ("https://developers.facebook.com/micro_site/url/?click_from_context_menu=true&country=MX&destination"
              "=https%3A%22Fwww.facebook.com%2Fads%2Farchive%2Frender_ad%2F%3Fid%3D1782512702619403%26access_token%3DEAALD2TdxHesBOZClNUmyV4e4qUp1Eb5ZBPZAM3dKeecpTdLFjfbxCniZAWzDpmR9IKZCvnkDmKmSHUYLbjJZAgEHOfmvksFBH0jDo3wrLwY11LxQbvrCuzK67rM1mQLQ0Ev5zr1RkjZBV9gFmNVFUGKoIVkUDbxK8HWZA3aKrZCLStefzM6BcgwTyhnkQSyYfi3cC16ExNHYlAppCRtK1gfFT6I3IA1vuJmkZD&event_type=click&last_nav_impression_id=0oDxvWdCVeHS9l0hJ&max_percent_page_viewed=68&max_viewport_height_px=1132&max_viewport_width_px=1316&orig_http_referrer=https%3A%2F%2Fdevelopers.facebook.com%2Ftools%2Fexplorer%2F778287658900971%2F%3Fmethod%3DGET%26path%3Dads_archive%253Fad_reached_countries%253DMX%2526ad_type%253DPOLITICAL_AND_ISSUE_ADS%2526pretty%253D0%2526search_terms%253Djudicial%2526limit%253D5000%2526ad_delivery_date_min%253D2025-03-01%26version%3Dv21.0&orig_request_uri=https%3A%2F%2Fdevelopers.facebook.com%2Ftools%2Fexplorer%2Fv2%2Fpreferences%2F%3Fads_manager_write_regions%3Dtrue&region=latam&scrolled=false&session_id=1OtL22wGMsy5KOmAW&site=developers")

    response = requests.get(page_url)

    page_url2 = "https://www.facebook.com/ads/archive/render_ad/?id=1042382157852000&access_token=EAALD2TdxHesBOZClNUmyV4e4qUp1Eb5ZBPZAM3dKeecpTdLFjfbxCniZAWzDpmR9IKZCvnkDmKmSHUYLbjJZAgEHOfmvksFBH0jDo3wrLwY11LxQbvrCuzK67rM1mQLQ0Ev5zr1RkjZBV9gFmNVFUGKoIVkUDbxK8HWZA3aKrZCLStefzM6BcgwTyhnkQSyYfi3cC16ExNHYlAppCRtK1gfFT6I3IA1vuJmkZD"
    response2 = requests.get(page_url2)

    # props
    # placeholderElement




