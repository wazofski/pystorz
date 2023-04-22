class _Schema:
    def __init__(self, objects):
        self.objects = objects

    def object_for_kind(self, kind):
        return None

    def types(self):
        return self.objects


def schema():
    objects = []

    return _Schema(objects)
