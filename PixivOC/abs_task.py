from os import path, listdir, mkdir
from Download import(
    ResultPackage,
    RequestPackageList,
    AbsDownloader,
    ExitState
)
from typing import Callable, Union, Optional, Tuple, Any
from log import logging, core_logger


logging.getLogger('werkzeug').setLevel(logging.WARNING)

_SUBCLASS_NAME_SET = set()
_SUBCLASS_ORDER = 0
SUBCLASS_DICT = {}


class StorageUnit:
    def __init__(self, tid: int, task_name: str, type_id: int, over: bool,
                 current_stage: int, params_list: list, data: list, save_path: str):
        self.Tid = tid
        self.TaskName = task_name
        self.TypeID = type_id
        self.Over = over
        self.CurrentStage = current_stage
        if not data:  # if list of data is empty
            assert params_list is not None
        self.ParamsList = params_list
        self.Data = data
        self.SavePath = save_path

    def json(self) -> list:
        return [
            self.Tid,
            self.TaskName,
            self.TypeID,
            self.Over,
            self.CurrentStage,
            self.ParamsList,
            self.Data,
            self.SavePath,
        ]


class TaskState:
    WaitStart = 'WaitStart'
    WaitToken = 'WaitToken'
    Downloading = 'Downloading'
    Stopped = 'Stopped'
    Over = 'Over'
    Error = 'Error'


class ParseResult:
    def __init__(self, request_param: Any, result: Any = None):
        assert request_param is not None
        self.request_param = request_param
        self.result = result


def automatic_numbering(cls):
    global _SUBCLASS_NAME_SET, _SUBCLASS_ORDER, SUBCLASS_DICT
    class_name = cls.__name__
    if class_name not in _SUBCLASS_NAME_SET:
        _SUBCLASS_ORDER += 1
        SUBCLASS_DICT[_SUBCLASS_ORDER] = cls
        cls.TypeID = _SUBCLASS_ORDER

    return cls


class BaseTask:
    TypeID = 0

    def __init__(self, storage: StorageUnit):
        if self.__class__.__name__ != 'BaseTask':
            assert self.TypeID != 0, 'Please add decorator to sub class'

        # Addition interface and replacement rules of stage
        self._request_fn_mapping = dict()
        self._parse_fn_mapping = dict()
        self._stage_name_mapping = dict()
        self._stage_order = 0

        self._current_stage = storage.CurrentStage
        self._over = storage.Over
        self._replace_rules = None
        self._rules_of_result_to_params = None

        # Store
        self._tid = storage.Tid
        self._task_name = storage.TaskName
        self._params_list = storage.ParamsList
        self._data = storage.Data
        self._save_path = storage.SavePath

        # Initialize running flag and create root folder of task
        self._type_name = 'Default Name'
        self._downloader = AbsDownloader()
        self._remain = len(self._params_list)
        self._total = len(self._params_list) + len(self._data)
        self._state = TaskState.WaitStart
        if self._over:
            self._state = TaskState.Over
        self._error = False
        abs_path = path.abspath(self._save_path)
        if path.exists(abs_path):
            self._abs_save_path = path.join(abs_path, self._task_name)
            if self._task_name not in listdir(abs_path):
                mkdir(self._abs_save_path)
        else:
            self._over = True
            self._error = True
            self._state = TaskState.Error

        core_logger.info(f'Create task {self._task_name}.')

    '''
    Addition interface and replacement rules of stage
    '''
    def add_stage(
        self,
        # TODO: [Optional[str]] -> [Optional[...]]
        request_fn: Callable[[Optional[str]], RequestPackageList],
        parse_fn: Callable[[ResultPackage], ParseResult],
        stage_name: str = 'Default'
    ) -> None:

        self._stage_order += 1

        self._request_fn_mapping[self._stage_order] = request_fn
        self._parse_fn_mapping[self._stage_order] = parse_fn
        self._stage_name_mapping[self._stage_order] = stage_name

    def _replace_stage(self) -> None:
        if self._replace_rules is None:
            temp_stage = self._current_stage + 1
        else:
            temp_stage = self._replace_rules()
            assert temp_stage is not None, 'Must return a number'

        self._over = False if temp_stage in self._request_fn_mapping else True
        self._current_stage = temp_stage if self._over is False else self._current_stage

    def set_replacement_rules(self, f: Callable[[], int]) -> None:
        self._replace_rules = f

    def _distribute_parser(self, result_package: ResultPackage) -> ParseResult:
        return self._parse_fn_mapping[self._current_stage](result_package)

    '''
    running process
    '''
    def start(self) -> None:
        core_logger.info(f'Call task {self._task_name} start function.')
        if self._state == TaskState.WaitStart:
            return self._start()
        elif self._state == TaskState.WaitToken:
            pass
        elif self._state == TaskState.Downloading:
            pass
        elif self._state == TaskState.Stopped:
            return self._start()
        elif self._state == TaskState.Over:
            pass
        elif self._state == TaskState.Error:
            pass

    def _start(self) -> None:
        if self._current_stage == 0:
            self._current_stage += 1
        self._start_stage()

    def _start_stage(self) -> None:
        self._request_fn_mapping[self._current_stage]()
        self._state = TaskState.Downloading

    def stop(self) -> None:
        core_logger.info(f'Call task {self._task_name} stop function.')
        if self._state == TaskState.WaitStart:
            pass
        elif self._state == TaskState.WaitToken:
            return self._stop()
        elif self._state == TaskState.Downloading:
            return self._stop()
        elif self._state == TaskState.Stopped:
            pass
        elif self._state == TaskState.Over:
            pass
        elif self._state == TaskState.Error:
            pass

    def _stop(self) -> None:
        if self._downloader is not None:
            if self._downloader.is_alive():
                self._downloader.stop()
        self._state = TaskState.Stopped

    def safe_stop(self) -> None:
        core_logger.info(f'Call task {self._task_name} safe stop function.')
        if self._state == TaskState.WaitStart:
            pass
        elif self._state == TaskState.WaitToken:
            return self._safe_stop()
        elif self._state == TaskState.Downloading:
            return self._safe_stop()
        elif self._state == TaskState.Stopped:
            pass
        elif self._state == TaskState.Over:
            pass
        elif self._state == TaskState.Error:
            pass

    def _safe_stop(self) -> None:
        if self._downloader is not None:
            if self._downloader.is_alive():
                self._downloader.safe_stop()
        self._state = TaskState.Stopped

    def _create_and_start_downloader(self, request_package_list: RequestPackageList, sync: bool) -> None:
        raise BaseException('Please override this function')

    def _convert_request_result(self, result: Any, round_end: bool = False) -> Union[ResultPackage, int]:
        raise BaseException('Please override this function')

    def _result_to_params(self, result: Any) -> None:
        if self._rules_of_result_to_params is None:
            self._data.append(result)
        else:
            self._rules_of_result_to_params(result)

    def set_result_convert_rules(self, f: Callable[[Any], None]) -> None:
        self._rules_of_result_to_params = f

    def _parse_request_result(self, result: Any) -> None:
        result_package = self._convert_request_result(result)
        if result_package.ok:
            parse_result = self._distribute_parser(result_package)
            self._params_list.remove(parse_result.request_param)
            self._remain -= 1
            self._result_to_params(parse_result.result)
        else:
            # log or print exception
            pass

    def _when_completing_a_round_of_requests(self, result: Any) -> None:
        core_logger.debug(f'{self._task_name} completing a round of requests.')
        status_code = self._convert_request_result(result, round_end=True)
        if status_code == ExitState.Normal:
            self._state = TaskState.Stopped
            if self._params_list:  # if list is not empty
                return self._restart()
            else:
                return self._stage_complete(ExitState.Normal)
        elif status_code == ExitState.Cancel:
            return self._stage_complete(ExitState.Cancel)

    def _restart(self) -> None:
        core_logger.debug(f'{self._task_name} re-start.')
        return self._start_stage()

    def _stage_complete(self, status_code: int) -> None:
        if status_code == ExitState.Normal:
            self._replace_stage()
            if self._over is False:
                self._params_list = self._data
                self._data = list()
                self._remain = len(self._params_list)
                self._total = self._remain
                self._start_stage()
            else:
                assert len(self._params_list) == 0
                assert self._remain == 0
        elif status_code == ExitState.Cancel:
            pass

    '''
    Store
    '''
    def export_storage(self) -> StorageUnit:
        core_logger.debug(f'Export task {self._task_name}.')
        return StorageUnit(
            self._tid,
            self._task_name,
            self.TypeID,
            self._over,
            self._current_stage,
            self._params_list,
            self._data,
            self._save_path
        )

    '''
    Auxiliary Functions
    '''
    def set_type_name(self, name: str) -> None:
        self._type_name = name

    def _get_stage_name(self) -> str:
        if self._error:
            return 'Error'
        elif self._over:
            return 'Over'
        elif self._current_stage == 0:
            return 'Init'
        else:
            return self._stage_name_mapping[self._current_stage]

    @property
    def progress(self) -> Tuple[str, str, int, int]:
        return self._get_stage_name(), self._state, self._remain, self._total

    @property
    def msg(self) -> Tuple[bool, int, str, str, str, str, str, int, int]:
        return (
            self._over, self._tid, self._task_name, self._type_name,
            self._save_path, self._get_stage_name(), self._state, self._remain, self._total
        )


def direct_download(sync: bool = False):
    def wrapper(fn):
        def inner(self, *args, **kwargs):
            request_package_list = fn(self, *args, **kwargs)
            self._create_and_start_downloader(request_package_list, sync)
        return inner
    return wrapper
