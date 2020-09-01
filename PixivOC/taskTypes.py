from task import *
from Download import RequestPackageList
from api import SingleWorkAPI, UserWorksAPI


class SingleWork(TokenTask):
    TypeID = 1
    TypeName = 'SingleWork'

    def _get_stage_name(self) -> str:
        if self._CurrentStage == 1:
            return 'GetWorkDetails'
        if self._CurrentStage == 2:
            return 'DownloadPictures'

    def _set_stage(self) -> int:
        return 2 if self._CurrentStage == 1 else -1

    def _start_stage(self):
        if self._CurrentStage == 1:
            return self._stage_1_token()
        if self._CurrentStage == 2:
            return self._stage_2()

    def _distribute_parser(self, result_package: ResultPackage) -> ParseResult:
        if self._CurrentStage == 1:
            return self._stage_1_parser(result_package)
        if self._CurrentStage == 2:
            return self.picture_parser(result_package)

    @token_stage_wrapper
    def _stage_1(self, token: str) -> RequestPackageList:
        work_id = int(self._ParamsList[0])
        request_package = SingleWorkAPI.get_package(work_id, token)
        return [request_package]

    def _stage_1_token(self):
        return self._get_token(self._stage_1)

    @staticmethod
    def _stage_1_parser(result_package: ResultPackage) -> ParseResult:
        result = SingleWorkAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, result)

    @stage_wrapper
    def _stage_2(self) -> RequestPackageList:
        return [SingleWorkAPI.get_picture_request_package(url) for url in self._ParamsList]


class UserWorks(TokenTask):
    TypeID = 2
    TypeName = 'UserWorks'

    def _get_stage_name(self) -> str:
        if self._CurrentStage == 1:
            return 'GetWorksNumber'
        if self._CurrentStage == 2:
            return 'GetPageUrls'
        if self._CurrentStage == 3:
            return 'DownloadPictures'

    def _set_stage(self) -> int:
        if self._CurrentStage == 1:
            if type(self._ParamsList[0]) is str:
                return 3
            else:
                return 2
        if self._CurrentStage == 2:
            return 3
        if self._CurrentStage == 3:
            return -1

    def _start_stage(self):
        if self._CurrentStage == 1:
            return self._stage_1_token()
        if self._CurrentStage == 2:
            return self._stage_2_token()
        if self._CurrentStage == 3:
            return self._stage_3()

    def _distribute_parser(self, result_package: ResultPackage) -> ParseResult:
        if self._CurrentStage == 1:
            return self._stage_1_parser(result_package)
        if self._CurrentStage == 2:
            return self._stage_2_parser(result_package)
        if self._CurrentStage == 3:
            return self.picture_parser(result_package)

    @token_stage_wrapper
    def _stage_1(self, token: str):
        author_id = self._ParamsList[0]
        req_package = UserWorksAPI.get_package(author_id, token)
        return [req_package]

    def _stage_1_token(self):
        return self._get_token(self._stage_1)

    @staticmethod
    def _stage_1_parser(result_package: ResultPackage) -> ParseResult:
        author_id = result_package.msg[0]
        page_number = UserWorksAPI.parse_page(result_package.result)
        if page_number == 1:
            return ParseResult(author_id, UserWorksAPI.parse_picture(result_package.result))
        else:
            return ParseResult(author_id, [(author_id, i) for i in range(1, page_number+1)])

    @token_stage_wrapper
    def _stage_2(self, token: str) -> RequestPackageList:
        return [UserWorksAPI.get_package(author_id, token, page) for author_id, page in self._ParamsList]

    def _stage_2_token(self):
        return self._get_token(self._stage_2)

    @staticmethod
    def _stage_2_parser(result_package: ResultPackage) -> ParseResult:
        picture_url = UserWorksAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, picture_url)

    @stage_wrapper
    def _stage_3(self):
        return [UserWorksAPI.get_picture_request_package(url) for url in self._ParamsList]


TaskTypeList = [
    SingleWork,
    UserWorks
]
