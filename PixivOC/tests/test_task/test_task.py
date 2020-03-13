from taskTypes import *
from api import UserWorksAPI
from Download import PROXY_MANAGER
from structure import TaskReportUnit
from os import path


PROXY = 'http://127.0.0.1:1081'
TestPrePage = 5
# AuthorID_1 = 28145748  # 16 items 19 picture 2020/2/19
# AuthorID_2 = 5302293  # 61 works 2020/1/17

RUNNING = True


'''
User Works
'''


class UserWorksTask(BaseTask):
    TypeID = 1
    TypeName = 'UserWorks'

    def _goto_stage(self) -> int:
        if self._CurrentStage == 1:
            if type(self._ParamsList[0]) == str:
                return 3
        return super()._goto_stage()

    def _create_stage(self) -> BaseTaskStage:
        if self._CurrentStage == 1:
            return UserWorksStage1(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 2:
            return UserWorksStage2(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 3:
            return UserWorksStage3(self._TaskName, self._SavePath, self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        if self._CurrentStage == 4:
            self._task_over()

    def _return_value(self) -> Any:
        return ''


class UserWorksStage1(GetWorksNumber):
    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        page_number = UserWorksAPI.parse_page(result_package.result)
        if page_number == 1:
            return ParseResult(self._AuthorID, UserWorksAPI.parse_picture(result_package.result))
        else:
            return ParseResult(self._AuthorID, [(self._AuthorID, i) for i in range(1, page_number+1)])

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        req_package = UserWorksAPI.get_package(self._AuthorID, token)
        return [req_package]


class UserWorksStage2(GetPageUrls):
    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        picture_url = UserWorksAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, picture_url)

    def _create_request_package_list(self, token: str) -> RequestPackageList:
        return [UserWorksAPI.get_package(t[0], token, page=t[1]) for t in self._ParamsList]


class UserWorksStage3(SavePicture):
    def _parse_request_result(self, result_package: ResultPackage) -> ParseResult:
        with open(path.join(self._SavePath, result_package.msg[0]), 'wb') as file:
            file.write(result_package.result)
        return ParseResult(result_package.msg[1])

    def _create_request_package_list(self) -> RequestPackageList:
        return [UserWorksAPI.get_picture_request_package(url) for url in self._ParamsList]


def disguise_sent_to_server(msg_unit: TaskReportUnit):
    print('Send to server msg: ', msg_unit.content)
    global RUNNING
    RUNNING = False


if __name__ == '__main__':
    PROXY_MANAGER.change_to_ip()
    STORAGE = StorageUnit(1, 'Test full process', 1, 1, [28145748], [], '.')
    TASK = UserWorksTask(STORAGE, disguise_sent_to_server)
    TASK.start()
    while RUNNING:
        pass
    core_logger.debug('Test over.')
