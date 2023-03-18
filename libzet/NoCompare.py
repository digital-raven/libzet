class NoCompare:
    """ Returns False when compared with anything
    """
    def __init__(self):
        None

    def __lt__(self, o):
        return False

    def __gt__(self, o):
        return False

    def __le__(self, o):
        return False

    def __ge__(self, o):
        return False

    def __eq__(self, o):
        return False

    def __ne__(self, o):
        return False

    def __contains__(self, o):
        return False
