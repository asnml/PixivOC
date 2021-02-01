from typing import List, Union, Any


MethodList = ['GET', 'POST']  # Case-insensitive


class RequestPackage:
    def __init__(self, url: str, method: str,
                 headers: dict = None, params: dict = None, data: dict = None,
                 msg: Any = None, none_header: bool = False):
        assert method.upper() in MethodList
        self.url = url
        self.method = method.upper()
        self.headers = headers
        self.params = params
        self.data = data
        self.proxy = None
        self.msg = msg
        self.none_header = none_header

        if self.none_header:
            self.headers = None


class ResultPackage:
    def __init__(self, result: Union[bytes, int], msg: Any, exception: Exception = None):
        self.result = result
        self.msg = msg
        self.exception = exception

    @property
    def ok(self):
        return True if self.exception is None else False


RequestPackageList = List[RequestPackage]
ResultPackageList = List[ResultPackage]


class ExitState:
    Cancel = 1  # return this value when call DownloadThread.close()
    Normal = 0  # return this value when normal exit.


class AbsDownloader:
    def is_alive(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def safe_stop(self):
        pass