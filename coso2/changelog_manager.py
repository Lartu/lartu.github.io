import pickle
from config import *
from message_functions import *


old_changelogs = []


def load_changelog():
    '''Loads the changelog from previous builds of the website.
    '''
    global old_changelogs
    try:
        old_changelogs = pickle.load(open(get_base_dir() + "/oldchangelogs.p", "rb"))
        show("Loaded old changelogs.")
    except:
        old_changelogs = []
