from os import listdir, mkdir, path
from task import *
from api import UserWorksAPI, SingleWorkAPI, WorkDetailsAPI


'''
Usually used stage.
'''


class SavePicture(NoTokenTaskStage):
    def __init__(self, task_name: str, save_path: str, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None],
                 progress_update_fn: Callable[[str, int, int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn, progress_update_fn)
        self._StageName = 'DownloadPicture'

        abs_path = path.abspath(save_path)
        self._SavePath = path.join(abs_path, task_name)
        if task_name not in listdir(abs_path):
            mkdir(self._SavePath)


'''
Work Details
'''


class WorkDetailsTask(BaseTask):
    TypeID = 1
    TypeName = 'WorkDetails'

    def _create_stage(self) -> BaseTaskStage or None:
        if self._CurrentStage == 1:
            return WorkDetailsStage1(self._ParamsList, self._Data,
                                     self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 2:
            return self._task_over()

    def _return_value(self) -> Any:
        return self._ParamsList[0]


class WorkDetailsStage1(TokenTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None],
                 progress_update_fn: Callable[[str, int, int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn, progress_update_fn)
        self._StageName = 'GetWorkDetails'
        self.WorkID = self._ParamsList[0]
        assert type(self.WorkID) is int

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        result = WorkDetailsAPI.parse_result(result_package.result)
        return ParseResult(self.WorkID, result)

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        req_package = WorkDetailsAPI.get_package(self.WorkID, token)
        return [req_package]


'''
Single Work
'''


class SingleWorkTask(BaseTask):
    TypeID = 2
    TypeName = 'SingleWork'

    def _create_stage(self) -> BaseTaskStage or None:
        if self._CurrentStage == 1:
            return SingleWorkStage1(self._ParamsList, self._Data,
                                    self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 2:
            return SingleWorkStage2(self._TaskName, self._SavePath,
                                    self._ParamsList, self._Data,
                                    self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 3:
            return self._task_over()

    def _return_value(self) -> Any:
        return ''


class SingleWorkStage1(TokenTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None],
                 progress_update_fn: Callable[[str, int, int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn, progress_update_fn)
        self._StageName = 'GetWorkDetails'
        self.WorkID = self._ParamsList[0]
        assert type(self.WorkID) is int

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        result = SingleWorkAPI.parse_picture(result_package.result)
        return ParseResult(self.WorkID, result)

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        req_package = SingleWorkAPI.get_package(self.WorkID, token)
        return [req_package]


class SingleWorkStage2(SavePicture):
    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        with open(path.join(self._SavePath, result_package.msg[0]), 'wb') as file:
            file.write(result_package.result)
        return ParseResult(result_package.msg[1])

    def _create_request_package_list(self) -> RequestPackageList:
        return [SingleWorkAPI.get_picture_request_package(url) for url in self._ParamsList]


'''
User Works Link
'''


class UserWorksLinkTask(BaseTask):
    TypeID = 3
    TypeName = 'UserWorksLink'

    def _goto_stage(self) -> int:
        if self._CurrentStage == 1:
            if type(self._ParamsList[0]) == str:
                return 3
        return super()._goto_stage()

    def _create_stage(self) -> BaseTaskStage or None:
        if self._CurrentStage == 1:
            return UserWorksStage1(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 2:
            return UserWorksStage2(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 3:
            return self._task_over()

    def _return_value(self) -> Any:
        return self._ParamsList


class UserWorksStage1(TokenTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None],
                 progress_update_fn: Callable[[str, int, int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn, progress_update_fn)
        self._StageName = 'GetWorksNumber'

        assert type(params_list[0]) == int
        self._AuthorID = params_list[0]

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        page_number = UserWorksAPI.parse_page(result_package.result)
        if page_number == 1:
            return ParseResult(self._AuthorID, UserWorksAPI.parse_picture(result_package.result))
        else:
            return ParseResult(self._AuthorID, [(self._AuthorID, i) for i in range(1, page_number+1)])

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        req_package = UserWorksAPI.get_package(self._AuthorID, token)
        return [req_package]


class UserWorksStage2(TokenTaskStage):
    def __init__(self, params_list: list, data: list,
                 stage_complete_callback_fn: Callable[[int], None],
                 progress_update_fn: Callable[[str, int, int], None]):
        super().__init__(params_list, data, stage_complete_callback_fn, progress_update_fn)
        self._StageName = 'GetPageUrls'

    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        picture_url = UserWorksAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, picture_url)

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        return [UserWorksAPI.get_package(t[0], token, page=t[1]) for t in self._ParamsList]


'''
User Works
'''


class UserWorksTask(BaseTask):
    TypeID = 4
    TypeName = 'UserWorks'

    def _goto_stage(self) -> int:
        if self._CurrentStage == 1:
            if type(self._ParamsList[0]) == str:
                return 3
        return super()._goto_stage()

    def _create_stage(self) -> BaseTaskStage or None:
        if self._CurrentStage == 1:
            return UserWorksStage1(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 2:
            return UserWorksStage2(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 3:
            return UserWorksStage3(self._TaskName, self._SavePath,
                                   self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 4:
            return self._task_over()

    def _return_value(self) -> Any:
        return ''


class UserWorksStage3(SavePicture):
    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        with open(path.join(self._SavePath, result_package.msg[0]), 'wb') as file:
            file.write(result_package.result)
        return ParseResult(result_package.msg[1])

    def _create_request_package_list(self) -> RequestPackageList:
        return [UserWorksAPI.get_picture_request_package(url) for url in self._ParamsList]


TaskTypeList = [
    WorkDetailsTask,
    SingleWorkTask,
    UserWorksLinkTask,
    UserWorksTask
]
