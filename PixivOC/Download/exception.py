class KnownException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnknownException(Exception):
    def __init__(self, e: Exception):
        super().__init__(e.args)
