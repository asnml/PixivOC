from typing import List, Any
from copy import deepcopy
from .log import downloader_logger

MethodList = ['GET', 'POST']  # Case-insensitive


# use @property ?
class RequestPackage:
    def __init__(self, url: str, method: str,
                 headers: dict = None, params: dict = None, data: dict = None, msg: Any = None):
        assert method.upper() in MethodList
        self.url = url
        self.method = method.upper()
        self.headers = headers
        self.params = params
        self.data = data
        self.proxy = None
        self.msg = msg


class ResultPackage:
    def __init__(self, result: bytes or int, msg: Any, exception: Exception = None):
        self.result = result
        self.msg = msg
        self.exception = exception

    @property
    def ok(self):
        return True if self.exception is None else False


RequestPackageList = List[RequestPackage]
ResultPackageList = List[ResultPackage]


class ClientSessionParams:
    def __init__(self, headers: dict = None,
                 total_timeout: int = 60,
                 concurrency_number: int = 3,
                 interval: int = 3):
        """
        :param headers: header dict.
        :param total_timeout: please refer to
        https://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientTimeout
        :param concurrency_number: Single thread concurrency number.
        """
        self._Headers = headers
        self._TotalTimeout = total_timeout
        self._ConcurrencyNumber = concurrency_number
        self._Interval = interval
        downloader_logger.info('Create ClientSessionParams instance.')

    @property
    def headers(self):
        return deepcopy(self._Headers)

    @property
    def total_timeout(self):
        return self._TotalTimeout

    @property
    def concurrency_number(self):
        return self._ConcurrencyNumber

    @property
    def interval(self):
        return self._Interval

    def set_headers(self, headers: dict):
        self._Headers = headers

    def set_total_timeout(self, total_timeout: int) -> bool:
        try:
            assert type(total_timeout) is int
        except AssertionError:
            return False
        self._TotalTimeout = total_timeout
        return True

    def set_concurrency_number(self, concurrency_number: int) -> bool:
        try:
            assert type(concurrency_number) is int
        except AssertionError:
            return False
        self._ConcurrencyNumber = concurrency_number
        return True

    def set_interval(self, interval: int) -> bool:
        try:
            assert type(interval) is int
        except AssertionError:
            return False
        self._Interval = interval
        return True


class SyncSign:
    def __init__(self):
        self._sign = False

    def __bool__(self):
        return self._sign

    def make_true(self):
        self._sign = True

    def make_false(self):
        self._sign = False


class SyncFuture:
    def __init__(self, result_package: ResultPackage):
        self._ResultPackage = result_package

    def result(self):
        return self._ResultPackage


class ExitState:
    Cancel = 1  # return this value when call DownloadThread.close()
    Normal = 0  # return this value when normal exit.
