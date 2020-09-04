from time import sleep
from threading import Thread
from typing import List


RequestPackageList = List


class TokenManager:
    def __init__(self):
        self.cb = None
        self.io_thread = None
        self.times = 0

    def get_token(self, token_callback):
        self.times += 1
        if self.times == 3:
            return "token"
        self.cb = token_callback
        self.io_thread = Thread(target=self.net_io)
        self.io_thread.start()
        return ""

    def net_io(self):
        sleep(0.3)
        self.cb('token')


TOKEN_MANAGER = TokenManager()


def async_downloader(fn):
    def wrapper(self, *args, **kwargs):
        package_list = fn(self, *args, **kwargs)
        for x in package_list: print(x)
    return wrapper

def async_token_downloader(fn):
    def wrapper(self, *args, **kwargs):
        # fn is a function that create request package list
        # args and kwargs is parameters that need at create request package
        def inner_wrapper(self, *args, **kwargs):
            package_list = fn(self, *args, **kwargs)
            for x in package_list: print(x)

        token = TOKEN_MANAGER.get_token(self.get_token_callback)
        if token == "":
            self._wait_token_fn = inner_wrapper
            self._wait_token_fn_args = args
            self._wait_token_fn_kwargs = kwargs
        else:
            inner_wrapper(self, token, *args, **kwargs)
    return wrapper


class Task:
    @async_downloader
    def _stage_1(self, order: list):
        return [f'No token {x}' for x in order]


class TokenTask:
    def __init__(self):
        self._wait_token_fn = None
        self._wait_token_fn_args = None
        self._wait_token_fn_kwargs = None

    def get_token_callback(self, token: str):
        self._wait_token_fn(
            self,
            *(token, *self._wait_token_fn_args),
            **self._wait_token_fn_kwargs
        )

    @async_token_downloader
    def _stage_1(self, token: str, order: list) -> RequestPackageList:
        return [f'{number} - {token}' for number in order]


my_task = Task()
my_task._stage_1([1, 2, 3])

my_token_task = TokenTask()
my_token_task._stage_1([4, 5, 6])
sleep(1)
my_token_task._stage_1([7, 8, 9])
