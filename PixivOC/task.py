from os import listdir, mkdir, path
from asyncio import Future
from typing import Any
from threading import Lock
from mobileToken import TOKEN_MANAGER
from log import core_logger
from Download import (
    DownloadThread,
    CLIENT_SESSION_PARAMS,
    ExitState,
    ResultPackage
)


class ParseResult:
    def __init__(self, request_param: Any, result: Any = None):
        assert request_param is not None
        self.request_param = request_param
        self.result = result


class TaskState:
    WaitStart = 'WaitStart'
    WaitToken = 'WaitToken'
    Downloading = 'Downloading'
    Stopped = 'Stopped'
    Over = 'Over'
    Error = 'Error'


class StorageUnit:
    def __init__(self, tid: int, task_name: str, type_id: int, over: bool,
                 current_stage: int, params_list: list, data: list, save_path: str, total: int):
        self.TID = tid
        self.TaskName = task_name
        self.TypeID = type_id
        self.Over = over
        self.CurrentStage = current_stage
        if not data:  # if list of data is empty
            assert params_list is not None
        self.ParamsList = params_list
        self.Data = data
        self.SavePath = save_path
        self.Total = total

    def json(self):
        return [
            self.TID,
            self.TaskName,
            self.TypeID,
            self.Over,
            self.CurrentStage,
            self.ParamsList,
            self.Data,
            self.SavePath,
            self.Total
        ]


def stage_wrapper(fn):
    def wrapper(self, *args, **kwargs):
        request_package_list = fn(self, *args, **kwargs)
        self._DownloadThread = DownloadThread(self._parse_center)
        self._DownloadThread.start(self._downloader_loop_over, request_package_list)
        self._State = TaskState.Downloading
    return wrapper


class BaseTask:
    TypeID = 0
    TypeName = 'BaseTask'

    Increment = True

    def __init__(self, storage: StorageUnit):
        self._TID = storage.TID
        self._TaskName = storage.TaskName
        self._Over = storage.Over
        self._CurrentStage = storage.CurrentStage
        self._ParamsList = storage.ParamsList
        self._Data = storage.Data
        self._SavePath = storage.SavePath
        self._Total = storage.Total
        self._remain = len(self._ParamsList)

        self._TimeoutIncrement = self.Increment

        self._DownloadThread = None

        self._State = TaskState.WaitStart
        if self._CurrentStage == 0:
            self._StageName = "Init"
        elif self._Over:
            self._StageName = "Over"
            self._State = TaskState.Over
        else:
            self._StageName = self._get_stage_name()

        abs_path = path.abspath(self._SavePath)
        if path.exists(abs_path):
            self._AbsSavePath = path.join(abs_path, self._TaskName)
            if self._TaskName not in listdir(abs_path):
                mkdir(self._AbsSavePath)
        else:
            self._Over = True
            self._StageName = "Error"
            self._State = TaskState.Error

        core_logger.info(f'Create task {self._TaskName}.')

    @property
    def progress(self):
        return self._StageName, self._State, self._remain, self._Total

    @property
    def msg(self):
        return self._Over, self._TID, \
               self._TaskName, self.TypeName, self._SavePath,\
               self._StageName, self._State, self._remain, self._Total

    def export_storage(self) -> StorageUnit:
        core_logger.debug(f'Export task {self._TaskName}.')
        return StorageUnit(
            self._TID,
            self._TaskName,
            self.TypeID,
            self._Over,
            self._CurrentStage,
            self._ParamsList,
            self._Data,
            self._SavePath,
            self._Total
        )

    def start(self) -> None:
        if self._State == TaskState.WaitStart:
            return self._start()
        elif self._State == TaskState.WaitToken:
            pass
        elif self._State == TaskState.Downloading:
            pass
        elif self._State == TaskState.Stopped:
            return self._start()
        elif self._State == TaskState.Over:
            pass
        elif self._State == TaskState.Error:
            pass

    def _start(self) -> None:
        core_logger.info(f'Call task {self._TaskName} start function.')
        if self._CurrentStage == 0:
            self._CurrentStage += 1
            self._StageName = self._get_stage_name()
        self._start_stage()
        self._State = TaskState.Downloading

    def stop(self) -> None:
        if self._State == TaskState.WaitStart:
            pass
        elif self._State == TaskState.WaitToken:
            return self._stop()
        elif self._State == TaskState.Downloading:
            return self._stop()
        elif self._State == TaskState.Stopped:
            pass
        elif self._State == TaskState.Over:
            pass
        elif self._State == TaskState.Error:
            pass

    def _stop(self) -> None:
        core_logger.info(f'Call task {self._TaskName} stop function.')
        if self._DownloadThread is not None:
            if self._DownloadThread.is_alive():
                self._DownloadThread.close()
        self._State = TaskState.Stopped

    def safe_stop(self):
        if self._State == TaskState.WaitStart:
            pass
        elif self._State == TaskState.WaitToken:
            return self._safe_stop()
        elif self._State == TaskState.Downloading:
            return self._safe_stop()
        elif self._State == TaskState.Stopped:
            pass
        elif self._State == TaskState.Over:
            pass
        elif self._State == TaskState.Error:
            pass

    def _safe_stop(self):
        core_logger.info(f'Call task {self._TaskName} safe stop function.')
        if self._DownloadThread is not None:
            if self._DownloadThread.is_alive():
                self._DownloadThread.make_sure_close()
        self._State = TaskState.Stopped

    def _downloader_loop_over(self, future: Future):
        core_logger.debug(f'{self._TaskName} Downloader over.')
        self._State = TaskState.Stopped
        result_package = future.result()  # type: ResultPackage
        if result_package.result == ExitState.Normal:
            if self._ParamsList:
                self._State = TaskState.WaitStart
                return self._restart()
            else:
                return self._stage_complete(ExitState.Normal)
        elif result_package.result == ExitState.Cancel:
            return self._stage_complete(ExitState.Cancel)

    def _restart(self) -> None:
        core_logger.debug(f'{self._TaskName} re-start.')
        if self._TimeoutIncrement:
            now_timeout = CLIENT_SESSION_PARAMS.total_timeout
            CLIENT_SESSION_PARAMS.set_total_timeout(now_timeout+30)
        return self._start_stage()

    def _stage_complete(self, status_code: int) -> None:
        if status_code == ExitState.Normal:
            self._ParamsList = self._Data
            self._Data = []
            self._remain = len(self._ParamsList)
            self._Total = self._remain
            self._CurrentStage = self._set_stage()
            if self._CurrentStage == -1:
                self._Over = True
                self._StageName = 'Over'
                self._ParamsList = []
                self._remain = 0
                return
            self._StageName = self._get_stage_name()
            self._start_stage()
        elif status_code == ExitState.Cancel:
            pass

    def _parse_center(self, future: Future) -> None:
        result_package = future.result()  # type: ResultPackage
        if result_package.ok:
            parse_result = self._distribute_parser(result_package)  # type: ParseResult
            self._ParamsList.remove(parse_result.request_param)
            self._remain -= 1
            if type(parse_result.result) is list:
                self._Data.extend(parse_result.result)
            else:
                self._Data.append(parse_result.result)
        else:
            # log or print exception
            pass

    def picture_parser(self, result_package: ResultPackage):
        with open(path.join(self._AbsSavePath, result_package.msg[0]), 'wb') as file:
            file.write(result_package.result)
        return ParseResult(result_package.msg[1], result_package.msg[0])

    # ******************************************
    # you should override the following function
    # ******************************************

    def _get_stage_name(self) -> str:
        raise Exception('Please override this function.')

    def _set_stage(self) -> int:
        raise Exception('Please override this function.')

    def _start_stage(self):
        raise Exception('Please override this function.')

    def _distribute_parser(self, result_package: ResultPackage) -> ParseResult:
        raise Exception('Please override this function.')


def token_stage_wrapper(fn):
    def wrapper(self, *args, **kwargs):
        self._Lock.acquire()
        if self._stopped:
            return
        request_package_list = fn(self, *args, **kwargs)
        self._DownloadThread = DownloadThread(self._parse_center, sync=True)
        self._DownloadThread.start(self._downloader_loop_over, request_package_list)
        self._State = TaskState.Downloading
        self._Lock.release()
        # When you request pixiv api interface,
        # you must be use sync downloader.
        # Use async downloader will raise ConnectionResetError exception.
        # I don't know how to fixed it.
    return wrapper


class TokenTask(BaseTask):
    def __init__(self, storage: StorageUnit):
        super().__init__(storage)
        self._wait_token_fn = None
        self._wait_token_fn_args = ()
        self._wait_token_fn_kwargs = {}

        self._stopped = False
        self._Lock = Lock()

    def _get_token(self, fn, *args, **kwargs):
        token = TOKEN_MANAGER.get_token(self.get_token_callback)
        if token == "":
            self._wait_token_fn = fn
            self._wait_token_fn_args = args
            self._wait_token_fn_kwargs = kwargs
        else:
            fn(token, *args, **kwargs)

    def get_token_callback(self, token: str):
        self._wait_token_fn(
            *(token, *self._wait_token_fn_args),
            **self._wait_token_fn_kwargs
        )

    def _start(self) -> None:
        self._Lock.acquire()
        self._stopped = False
        super()._start()
        self._Lock.release()

    def _stop(self) -> None:
        self._Lock.acquire()
        self._stopped = True
        super()._stop()
        self._Lock.release()

    def _safe_stop(self) -> None:
        self._Lock.acquire()
        self._stopped = True
        super()._safe_stop()
        self._Lock.release()
