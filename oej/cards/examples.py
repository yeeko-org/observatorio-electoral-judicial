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


def test_first_seat(seat_id=1):
    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate
    candidates = Candidate.objects\
        .filter(seat_id=seat_id, gemini_text__isnull=True)\
        .order_by('id')
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

# test_first_seat(3)

def apply_structure(ai_company='deepseek', engine='deepseek-chat'):
    # ai_company = 'openai'
    # engine = 'gpt-4o-2024-11-20'
    from django.utils import timezone
    from oej.sonar.sonar_research import SonarResearch
    from oej.models import Candidate, StatusControl
    bio_title = "\n\nBIOGRAFÍA DEL CONSEJO DE LA JUDICATURA FEDERAL (CJF)\n\n"
    deepseek = SonarResearch(
        ai_company=ai_company, engine=engine, to_json=True)
    candidates = Candidate.objects\
        .filter(gemini_text__isnull=False, academic_text__isnull=True)
    st_created = StatusControl.objects.get(name='created')
    for candidate in candidates:
        start = timezone.now()
        print(f"Starting at {start}")
        # candidate = candidates.first()
        deepseek.build_prompt("oej/sonar/structure_prompt.txt")
        user_prompt = candidate.gemini_text
        if candidate.biography and candidate.biography.curriculum:
            user_prompt += f"{bio_title}{candidate.biography.curriculum}"
        result = deepseek.send_prompt(user_prompt=user_prompt)
        if not result:
            print("No result")
            continue
        result.pop("name")
        for key, value in result.items():
            setattr(candidate, key, value)
        candidate.status_register = st_created
        candidate.save()
        finish = timezone.now()
        print(f"Finished at {finish}")
        duration = finish - start
        print(f"Duration: {duration}")


# apply_structure('deepseek', 'deepseek-chat')
# apply_structure('openai', 'gpt-4o-2024-11-20')


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
    for candidate in candidates[:4]:
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



def init_users(create=True):

    from profile_auth.models import User
    people = [
        {
            "name": "Aurelien",
            "initials": "Au",
            "color": "deep-purple-lighten-1",
            "organization": "Práctica",
        },
        {
            "name": "Ana Paola",
            "initials": "AP",
            "color": "purple-lighten-1",
            "organization": "Práctica",
        },
        {
            "name": "Víctor",
            "initials": "Vi",
            "color": "light-blue",
            "organization": "Laboratorio",
        },
        {
            "name": "Andrea Pablos",
            "initials": "An",
            "color": "cyan-darken-1",
            "organization": "Laboratorio",
        },
    ]
    for person in people:
        try:
            user = User.objects.get(first_name=person["name"])
            user.initials = person["initials"]
            user.color = person["color"]
            user.organization = person["organization"]
            user.save()
            print(f"User {user.username} updated")
        except User.DoesNotExist:
            if create:
                user = User(
                    username=person["name"],
                    first_name=person["name"],
                    last_name="",
                    initials=person["initials"],
                    color=person["color"],
                    organization=person["organization"],
                    email=f"{person['name'].lower()}@example.com",
                )
                user.set_password("password")
                user.save()
                print(f"User {user.username} created")
            else:
                print(f"User {person['name']} does not exist")


init_users(create=True)


def assign_users():
    from profile_auth.models import User
    initials = ["Vi", "AP", "Au", "An"]
    users = User.objects.filter(
        initials__in=initials).order_by('initials')
    from oej.models import Candidate
    candidates = Candidate.objects.filter(
        seat__position_id__in=[1, 3])\
        .order_by('?')
    for (idx, candidate) in enumerate(candidates):
        user_idx = idx % len(initials)
        candidate.user_validation = users[user_idx]
        candidate.save()



