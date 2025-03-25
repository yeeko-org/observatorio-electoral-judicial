
from geo.models import State
from geo.states_data import states

from django.core.management.base import BaseCommand

from utils.common import text_normalizer


class Command(BaseCommand):
    help = 'Load states'

    def handle(self, *args, **options):

        states = LoadStates()


class LoadStates:
    def __init__(self):

        for state in states:

            alternative_names = [
                text_normalizer(st) for st in state["other_names"].split(",")]

            alternative_names = list(set([
                alt_name for alt_name in alternative_names if alt_name
            ]))

            State.objects.create(
                inegi_code=state["inegi_code"],
                name=state["name"],
                short_name=state["short_name"],
                code_name=state["code_name"],
                alternative_names=alternative_names
            )
