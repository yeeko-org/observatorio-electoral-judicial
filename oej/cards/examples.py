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

load_pdf_content(2, 200)

