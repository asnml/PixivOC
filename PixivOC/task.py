from asyncio import Future
from typing import Any, Callable
from interface import SendType
from structure import TaskReportUnit
from mobileToken import TOKEN_MANAGER
from log import core_logger
from Download import (
    DownloadThread,
    CLIENT_SESSION_PARAMS,
    RequestPackageList,
    ExitState,
    ResultPackage
)


class ParseResult:
    def __init__(self, request_param: Any, result: Any = None):
        assert request_param is not None
        self.request_param = request_param
        self.result = result


class BaseTaskStage:
    Increment = True

    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None]):
        #         progress_update_fn: Callable[[str, int, int], None]):
        self._StageName = 'DefaultStageName'
        self.State = WaitStart()
        self._TimeoutIncrement = self.Increment
        self._ParamsList = params_list  # please note: this is not deepcopy variable
        self._Data = data  # please note: this is not deepcopy variable
        self._StageCompleteCallbackFn = stage_complete_callback_fn
        # self._ProgressUpdateFn = progress_update_fn
        self.DownloadThread = None

        self.Total = len(self._ParamsList) + len(self._Data)
        self._call_complete_fn = True

    def start(self) -> None:
        pass

    def stop(self) -> None:
        return self.State.stop(self)

    def downloader_loop_over_callback(self, future: Future) -> None:
        core_logger.debug('Downloader over.')
        self.State = Stopped()
        result_package = future.result()  # type: ResultPackage
        if result_package.result == ExitState.Normal:
            if self._is_complete():
                return self._StageCompleteCallbackFn(ExitState.Normal)
            else:
                self.State = WaitStart()
                return self._restart()
        elif result_package.result == ExitState.Cancel:
            return self._StageCompleteCallbackFn(ExitState.Cancel)

    def _is_complete(self) -> bool:
        if self._ParamsList:
            return False
        else:
            return True

    def _restart(self) -> None:
        core_logger.debug('re-start.')
        if self._TimeoutIncrement:
            now_timeout = CLIENT_SESSION_PARAMS.total_timeout
            CLIENT_SESSION_PARAMS.set_total_timeout(now_timeout+30)
        return self.start()

    def downloader_single_request_callback(self, future: Future) -> None:
        result_package = future.result()  # type: ResultPackage
        if result_package.ok:
            parse_result = self._parse_request_result(result_package)
            self._ParamsList.remove(parse_result.request_param)
            # core_logger.debug(f'Progress: {len(self._ParamsList)}/{self._All}')
            # self._ProgressUpdateFn(self._StageName, len(self._ParamsList), self.Total)
            if parse_result.result is not None:
                if type(parse_result.result) is list:
                    self._Data.extend(parse_result.result)
                else:
                    self._Data.append(parse_result.result)
        else:
            # log or print exception
            pass

    def is_alive(self):
        if self.DownloadThread is None:
            return False
        return self.DownloadThread.is_alive()

    @property
    def progress(self):
        return len(self._ParamsList), self.Total

    @property
    def msg(self):
        return self._StageName, self.is_alive(), len(self._ParamsList), self.Total

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        raise Exception('Please override this function.')


class TokenTaskStage(BaseTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn)

    def start(self):
        self.State.start(
            self,
            need_token=True,
            get_token_callback=self.get_token_callback
        )

    def get_token_callback(self, token: str):
        if token == 0:
            self.State = WaitStart()
            return
        request_package_list = self._create_request_package_list(token)
        self.DownloadThread = DownloadThread(self.downloader_single_request_callback, sync=True)
        self.DownloadThread.start(
            self.downloader_loop_over_callback,
            request_package_list
        )
        self.State = Downloading()
        # When you request pixiv api interface,
        # you must be use sync downloader.
        # Use async downloader will raise ConnectionResetError exception.
        # I don't know hwo to fixed it.

    # **************************************
    # you should override following function
    # **************************************

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        raise Exception('Please override this function.')

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        raise Exception('Please override this function.')


class NoTokenTaskStage(BaseTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn)

    def start(self):
        self.State.start(
            self,
            request_package_list=self._create_request_package_list()
        )

    # **************************************
    # you should override following function
    # **************************************

    def _create_request_package_list(self) -> RequestPackageList:
        raise Exception('Please override this function.')

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        raise Exception('Please override this function.')


class TaskOverStage(BaseTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn)
        self._StageName = 'TaskOver'

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class StorageUnit:
    def __init__(self, tid: int, task_name: str, task_type: int, over: bool,
                 current_stage: int, params_list: list, data: list, save_path: str):
        self.TID = tid
        self.TaskName = task_name
        self.TaskType = task_type
        self.Over = over
        self.CurrentStage = current_stage
        if not data:  # if list of data is empty
            assert params_list is not None
        self.ParamsList = params_list
        self.Data = data
        self.SavePath = save_path

    def json(self):
        return [
            self.TID,
            self.TaskName,
            self.TaskType,
            self.Over,
            self.CurrentStage,
            self.ParamsList,
            self.Data,
            self.SavePath
        ]


class BaseTask:
    TypeID = 0
    TypeName = 'BaseTask'

    def __init__(self, storage: StorageUnit, accept_report_fn: Callable[[TaskReportUnit], None]):
        self._TID = storage.TID
        self._TaskName = storage.TaskName
        self._TaskType = self.TypeID
        self._Over = storage.Over
        self._CurrentStage = storage.CurrentStage
        self._ParamsList = storage.ParamsList
        self._Data = storage.Data
        self._SavePath = storage.SavePath

        if self._Over:
            self._Stage = TaskOverStage(
                self._ParamsList, self._Data, self._stage_complete_callback
            )
        else:
            self._Stage = self._create_stage()
        self._AcceptReportFn = accept_report_fn
        core_logger.info(f'Create task {self._TaskName}.')

    def start(self) -> None:
        core_logger.info(f'Call task {self._TaskName} start function.')
        return self._Stage.start()

    def stop(self) -> None:
        core_logger.info(f'Call task {self._TaskName} stop process.')
        return self._Stage.stop()

    def export_storage(self) -> StorageUnit:
        core_logger.debug(f'Export task {self._TaskName}.')
        return StorageUnit(
            self._TID,
            self._TaskName,
            self._TaskType,
            self._Over,
            self._CurrentStage,
            self._ParamsList,
            self._Data,
            self._SavePath
        )

    # def _progress_update(self, stage_name: str, now: int, all_: int):
    #     self._AcceptReportFn(TaskReportUnit(
    #         SendType.TaskStatusUpdate, self._TID, [stage_name, now, all_]
    #     ))

    def _stage_complete_callback(self, status_code: int) -> None:
        if status_code == ExitState.Normal:
            self._ParamsList = self._Data
            self._Data = []
            self._CurrentStage = self._goto_stage()
            self._Stage = self._create_stage()
            if self._Stage is not None: self._Stage.start()
        elif status_code == ExitState.Cancel:
            pass

    def _task_over(self) -> BaseTaskStage:
        result = self._return_value()
        self._Over = True
        self._AcceptReportFn(TaskReportUnit(SendType.TaskOver, self._TID, result))
        return TaskOverStage(
            self._ParamsList, self._Data, self._stage_complete_callback
        )

    @property
    def msg(self):
        stage_name, is_alive, now, total = self._Stage.msg
        return self._Over, self._TID, self._TaskName, self.TypeName, stage_name, is_alive, now, total, self._SavePath

    # ******************************************
    # you should override the following function
    # ******************************************

    def _create_stage(self) -> BaseTaskStage or None:
        # At end must use this form:
        # if self._CurrentStage == some:
        #     return self._task_over()
        raise Exception('Please override this function.')

    def _return_value(self) -> Any:
        """
        Note that the return value must be serializable.
        :return:
        """
        raise Exception('Please override this function.')

    # ***************************************
    # you can override the following function
    # ***************************************

    def _goto_stage(self) -> int:
        """
        Function of unconditional jump to any stage.
        Add your statement in this function,
        and then return a int value that representative process stage.
        :return:
        """
        return self._CurrentStage + 1


'''
Task State
'''


class TaskState:
    @staticmethod
    def start(task_stage: BaseTaskStage,
              need_token: bool = False,
              request_package_list: RequestPackageList = None,
              get_token_callback=None):
        raise Exception('Please override ths function.')

    @staticmethod
    def stop(task_stage: BaseTaskStage):
        raise Exception('Please override ths function.')


class WaitStart(TaskState):
    @staticmethod
    def str():
        return 'WaitStart'

    def __str__(self):
        return 'WaitStart'

    @staticmethod
    def start(task_stage: BaseTaskStage,
              need_token: bool = False,
              request_package_list: RequestPackageList = None,
              get_token_callback=None):

        if need_token:
            assert get_token_callback is not None
            token = TOKEN_MANAGER.get_token(get_token_callback)
            if token != '':
                get_token_callback(token)
                task_stage.State = Downloading()
            else:
                task_stage.State = WaitToken()

        else:
            assert request_package_list is not None
            task_stage.DownloadThread = DownloadThread(task_stage.downloader_single_request_callback)
            task_stage.DownloadThread.start(task_stage.downloader_loop_over_callback, request_package_list)
            task_stage.State = Downloading()

    @staticmethod
    def stop(task_stage: BaseTaskStage):
        print("Task not start, can't call this function.")


class WaitToken(TaskState):
    @staticmethod
    def str():
        return 'WaitToken'

    def __str__(self):
        return 'WaitToken'

    @staticmethod
    def start(task_stage: BaseTaskStage,
              need_token: bool = False,
              request_package_list: RequestPackageList = None,
              get_token_callback=None):
        print("Task has been started.")

    @staticmethod
    def stop(task_stage: BaseTaskStage):
        print("Please call this function when the task state change to Downloading")


class Downloading(TaskState):
    @staticmethod
    def str():
        return 'Downloading'

    def __str__(self):
        return 'Downloading'

    @staticmethod
    def start(task_stage: BaseTaskStage,
              need_token: bool = False,
              request_package_list: RequestPackageList = None,
              get_token_callback=None):
        print("Task has been started.")

    @staticmethod
    def stop(task_stage: BaseTaskStage):
        task_stage.DownloadThread.close()
        task_stage.State = Stopped()


class Stopped(TaskState):
    @staticmethod
    def str():
        return 'Stopped'

    def __str__(self):
        return 'Stopped'

    @staticmethod
    def start(task_stage: BaseTaskStage,
              need_token: bool = False,
              request_package_list: RequestPackageList = None,
              get_token_callback=None):

        if need_token:
            assert get_token_callback is not None
            token = TOKEN_MANAGER.get_token(get_token_callback)
            if token != '':
                get_token_callback(token)
                task_stage.State = Downloading()
            else:
                task_stage.State = WaitToken()

        else:
            assert request_package_list is not None
            task_stage.DownloadThread = DownloadThread(task_stage.downloader_single_request_callback)
            task_stage.DownloadThread.start(task_stage.downloader_loop_over_callback, request_package_list)
            task_stage.State = Downloading()

    @staticmethod
    def stop(task_stage: BaseTaskStage):
        print("Task has been stopped.")
