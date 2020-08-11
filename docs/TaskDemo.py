from time import sleep
from threading import Thread
from typing import List


RequestPackageList = List


class TokenManager:
    def __init__(self):
        self.cb = None
        self.io_thread = None

    def get_token(self, token_callback):
        self.cb = token_callback
        self.io_thread = Thread(target=self.net_io)
        self.io_thread.start()
        return ""

    def net_io(self):
        sleep(0.3)
        self.cb('token')


TOKEN_MANAGER = TokenManager()


def stage_wrapper(fn):
    def wrapper(self, *args, **kwargs):
        package_list = fn(self, *args, **kwargs)
        for x in package_list: print(x)

    return wrapper


class Task:
    @stage_wrapper
    def _stage_1(self, order: list):
        return [f'No token {x}' for x in order]


class TokenTask:
    def __init__(self):
        self._wait_token_fn = None
        self._wait_token_fn_args = None
        self._wait_token_fn_kwargs = None

    def _get_token(self, fn, *args, **kwargs):
        token = TOKEN_MANAGER.get_token(self.get_token_callback)
        if token == "":
            self._wait_token_fn = fn
            self._wait_token_fn_args = args
            self._wait_token_fn_kwargs = kwargs
        else:
            fn(token, *args, **kwargs)

    def _stage_1_token(self, order: list):
        return self._get_token(self._stage_1, order)

    @stage_wrapper
    def _stage_1(self, token: str, order: list) -> RequestPackageList:
        return [f'{number} - {token}' for number in order]

    def get_token_callback(self, token: str):
        self._wait_token_fn(
            *(token, *self._wait_token_fn_args),
            **self._wait_token_fn_kwargs
        )


my_task = Task()
my_task._stage_1([1, 2, 3])

my_token_task = TokenTask()
my_token_task._stage_1_token([4, 5, 6])
