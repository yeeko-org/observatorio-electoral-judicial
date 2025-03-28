from oej.cards.load_candidates import LoadCandidates, main


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

