from os import path
from abs_task import BaseTask, ParseResult, ResultPackage, StorageUnit, TaskState, RequestPackageList
from Download import DownloadThread, CLIENT_SESSION_PARAMS
from mobileToken import TOKEN_MANAGER
from asyncio import Future
from threading import Lock
from typing import Union, Any


class Task(BaseTask):
    def __init__(self, storage: StorageUnit):
        super().__init__(storage)
        self._increment = True
        self._timeout_increment = True
        self.set_result_convert_rules(self.rules_of_convert_params)

    def _create_and_start_downloader(self, request_package_list: RequestPackageList, sync: bool) -> None:
        self._downloader = DownloadThread(
            self._parse_request_result,
            self._when_completing_a_round_of_requests,
            sync = sync
        )
        self._downloader.start(request_package_list)

    def _convert_request_result(self, result: Future, round_end: bool = False) -> Union[ResultPackage, int]:
        if round_end is False:
            return result.result()
        else:
            return result.result().result

    def _restart(self) -> None:
        global CLIENT_SESSION_PARAMS
        if self._timeout_increment:
            now_timeout = CLIENT_SESSION_PARAMS.total_timeout
            CLIENT_SESSION_PARAMS.set_total_timeout(now_timeout + 30)
        return super()._restart()

    def rules_of_convert_params(self, result: Any) -> None:
        if type(result) is list:
            self._data.extend(result)
        else:
            self._data.append(result)

    # This function was not supposed to be here, 
    # but to avoid adding too many intermediate layers, 
    # it's better to put it here.
    # If an intermediate layer is used, 
    # the hierarchy should look like this:
    # class Task:
    #     ...
    # class PixivTask(Task):
    #     def picture_parser(...):
    #         ...
    # class TokenTask(PixivTask):
    #     ...
    def picture_parser(self, result_package: ResultPackage) -> ParseResult:
        with open(path.join(self._abs_save_path, result_package.msg[0]), 'wb') as file_:
            file_.write(result_package.result)
        return ParseResult(result_package.msg[1], result_package.msg[0])


class TokenTask(Task):
    def __init__(self, storage: StorageUnit):
        super().__init__(storage)
        self._wait_token_fn = None
        self._wait_token_fn_args = ()
        self._wait_token_fn_kwargs = {}
        self._sync = False

        self._stopped = False
        self._lock = Lock()

    def get_token_callback(self, token: str) -> None:
        self._lock.acquire()
        if token == "Internet connection exception":
            self._stopped = True
            self._state = TaskState.Stopped

        if self._stopped:
            self._lock.release()
            return
        request_package_list = self._wait_token_fn(
            self,
            *(token, *self._wait_token_fn_args),
            **self._wait_token_fn_kwargs
        )
        self._downloader = DownloadThread(
            self._parse_request_result,
            self._when_completing_a_round_of_requests,
            sync = self._sync
        )
        self._downloader.start(request_package_list)
        self._state = TaskState.Downloading
        self._lock.release()
        # When you request pixiv api interface,
        # you must be use sync downloader.
        # Use async downloader will raise ConnectionResetError exception.
        # I don't know how to fixed it.

    def _start(self) -> None:
        self._lock.acquire()
        self._stopped = False
        self._lock.release()
        super()._start()

    def _stop(self) -> None:
        self._lock.acquire()
        self._stopped = True
        super()._stop()
        self._lock.release()

    def _safe_stop(self) -> None:
        self._lock.acquire()
        self._stopped = True
        super()._safe_stop()
        self._lock.release()


def certification_download(sync: bool = False):
    def wrapper(fn):
        def inner(self, *args, **kwargs):
            self._wait_token_fn = fn
            self._wait_token_fn_args = args
            self._wait_token_fn_kwargs = kwargs
            self._sync = sync
            token = TOKEN_MANAGER.get_token(self.get_token_callback)
            print('get toekn:', token)
            if token != "":
                self.get_token_callback(token)
        return inner
    return wrapper