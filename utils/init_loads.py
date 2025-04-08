
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


# init_users(create=True)


def assign_users():
    from profile_auth.models import User
    initials = ["AP", "Au", "An", "Vi"]
    users = User.objects.filter(
        initials__in=initials).order_by('initials')
    from oej.models import Candidate
    candidates = Candidate.objects.filter(
        seat__position_id=2)\
        .order_by('?')
    for (idx, candidate) in enumerate(candidates[:4]):
        user_idx = idx % len(initials)
        candidate.user_validation = users[user_idx]
        candidate.save()

