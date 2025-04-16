
def get_deep_research_data(seat_id=1, limit=20):
    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate
    candidates = Candidate.objects\
        .filter(seat_id=seat_id, gemini_text__isnull=True)\
        .order_by('id')
    sonar = SonarResearch(ai_company='sonar', engine='sonar-deep-research')
    for candidate in candidates[:limit]:
        start = timezone.now()
        print(f"Starting at {start}")
        sonar.build_prompt("oej/sonar/sonar_prompt.txt", candidate)
        sonar.send_prompt()
        finish = timezone.now()
        print(f"Finished at {finish}")
        duration = finish - start
        print(f"Duration: {duration}")
        # print(sonar.candidate.gemini_text)


# get_deep_research_data(2, 20)


def apply_structure(
        ai_company='deepseek', engine='deepseek-chat',
        pos_id=1, limit=200):
    # ai_company = 'openai'
    # engine = 'gpt-4o-2024-11-20'
    import re
    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate, StatusControl
    bio_title = "\n\nBIOGRAFÍA DEL CONSEJO DE LA JUDICATURA FEDERAL (CJF):\n\n"
    cv_title = "\n\nCURRICULUM COMPLETO INE:\n\n"
    academic_subtitle = "\nTrayectoria académica (resumen):\n"
    deepseek = SonarResearch(
        ai_company=ai_company, engine=engine, to_json=True)
    # candidates = Candidate.objects\
    #     .filter(gemini_text__isnull=False, seat__position_id=pos_id)
    candidates = Candidate.objects\
        .filter(gemini_text__isnull=False,
                academic_text__isnull=True, seat__position_id=pos_id)
    st_created = StatusControl.objects.get(name='created')
    for candidate in candidates[:limit]:
        start = timezone.now()
        print(f"Starting at {start}")
        # candidate = candidates.first()
        deepseek.build_prompt("oej/sonar/structure_prompt.txt")
        user_prompt = candidate.gemini_text
        if candidate.biography and candidate.biography.curriculum:
            user_prompt += f"{bio_title}{candidate.biography.curriculum}"
        if candidate.ine_cv_text:
            user_prompt += f"{cv_title}"
            ine_data = candidate.ine_data or {}
            academic_summary = ine_data.get('descripcionTP')
            user_prompt += f"{academic_subtitle}{academic_summary}\n\n"
            user_prompt += f"{candidate.ine_cv_text}"
        result = deepseek.send_prompt(user_prompt=user_prompt)
        if not result:
            print("No result")
            continue
        result.pop("name")
        for key, value in result.items():
            setattr(candidate, key, value)
        more_info_text = result.get('more_info_text')
        if more_info_text:
            candidate.more_info_ia = more_info_text
            more_info_text = re.sub(r"\[\d{1,2}\]", "", more_info_text)
            candidate.more_info_text = more_info_text
        candidate.status_register = st_created
        candidate.save()
        finish = timezone.now()
        print(f"Finished at {finish}")
        duration = finish - start
        print(f"Duration: {duration}")


# apply_structure('deepseek', 'deepseek-chat')
# apply_structure('openai', 'gpt-4o-2024-11-20', 2, 1000)

