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
        candidate.save()


def update_all_biographies():
    from oej.models import Biography
    biographies = Biography.objects.all()
    for biography in biographies:
        biography.save()


def test_first_seat():
    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate
    candidates = Candidate.objects\
        .filter(seat_id=1, gemini_text__isnull=True)
    sonar = SonarResearch(ai_company='sonar', engine='sonar-deep-research')
    for candidate in candidates[:20]:
        start = timezone.now()
        print(f"Starting at {start}")
        sonar.build_prompt("oej/sonar/sonar_prompt.txt", candidate)
        sonar.send_prompt()
        finish = timezone.now()
        print(f"Finished at {finish}")
        duration = finish - start
        print(f"Duration: {duration}")
        # print(sonar.candidate.gemini_text)

def test_first_structure(ai_company='deepseek', engine='deepseek-chat'):
    ai_company = 'openai'
    engine = 'gpt-4o-2024-11-20'

    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate
    deepseek = SonarResearch(
        ai_company=ai_company, engine=engine, to_json=True)
    candidates = Candidate.objects\
        .filter(gemini_text__isnull=False, academic_text__isnull=True)
    for candidate in candidates:
        start = timezone.now()
        print(f"Starting at {start}")
        # candidate = candidates.first()
        deepseek.build_prompt("oej/sonar/structure_prompt.txt")
        user_prompt = candidate.gemini_text
        result = deepseek.send_prompt(user_prompt=user_prompt)
        if not result:
            print("No result")
            continue
        result.pop("name")
        for key, value in result.items():
            setattr(candidate, key, value)
        candidate.save()

        finish = timezone.now()
        print(f"Finished at {finish}")
        duration = finish - start
        print(f"Duration: {duration}")


# test_first_structure('deepseek', 'deepseek-chat')
# test_first_structure('openai', 'gpt-4o-2024-11-20')


def reset_status_candidates():
    from oej.models import Candidate
    candidates = Candidate.objects.filter(gemini_text__isnull=False)
    print(candidates.count())
    candidates.update(status_register_id='need_new_checking')
