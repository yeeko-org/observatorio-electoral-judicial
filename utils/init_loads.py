
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


def assign_users(pos_id=2):
    from profile_auth.models import User
    from oej.models import Candidate
    users = User.objects.filter(organization__isnull=False)\
        .order_by('?')
    candidates = Candidate.objects.filter(
        seat__position_id=pos_id)\
        .order_by('?')
    users_count = users.count()
    for (idx, candidate) in enumerate(candidates):
        user_idx = idx % users_count
        candidate.user_register = users[user_idx]
        candidate.save()


def assign_validation(pos_id=2):
    from profile_auth.models import User
    from oej.models import Candidate
    organizations = ["Laboratorio", "Práctica", "México Evalúa"]
    # initials = ["Vi", "Au", "An", "AP"]
    for org in organizations:
        users = User.objects.filter(organization__isnull=False)\
            .exclude(organization=org)\
            .order_by('?')
        candidates = Candidate.objects\
            .filter(seat__position_id=pos_id, user_register__organization=org)\
            .order_by('?')
        for (idx, candidate) in enumerate(candidates):
            user_idx = idx % len(users)
            candidate.user_validation = users[user_idx]
            candidate.save()

