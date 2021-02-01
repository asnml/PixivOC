from abs_task import automatic_numbering, ParseResult, direct_download
from task import TokenTask, certification_download
from Download import ResultPackage, RequestPackageList
from api import SingleWorkAPI, UserWorksAPI


@automatic_numbering
class SingleWork(TokenTask):
    def __init__(self, storage):
        super().__init__(storage)
        self.set_type_name('SingleWork')
        self.add_stage(self._stage_1, self._stage_1_parser, 'GetWorkDetails')
        self.add_stage(self._stage_2, self.picture_parser, 'DownloadPictures')

    @certification_download(sync=True)
    def _stage_1(self, token: str) -> RequestPackageList:
        work_id = int(self._params_list[0])
        request_package = SingleWorkAPI.get_package(work_id, token)
        return [request_package]

    @staticmethod
    def _stage_1_parser(result_package: ResultPackage) -> ParseResult:
        result = SingleWorkAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, result)

    @direct_download(sync=False)
    def _stage_2(self) -> RequestPackageList:
        return [SingleWorkAPI.get_picture_request_package(url) for url in self._params_list]


@automatic_numbering
class UserWorks(TokenTask):
    def __init__(self, storage):
        super().__init__(storage)
        self.set_type_name('UserWorks')
        self.set_replacement_rules(self.my_stage_replace_rules)
        self.add_stage(self._stage_1, self._stage_1_parser, 'GetWorksNumber')
        self.add_stage(self._stage_2, self._stage_2_parser, 'GetPageUrls')
        self.add_stage(self._stage_3, self.picture_parser, 'DownloadPictures')

    def my_stage_replace_rules(self) -> int:
        if self._current_stage == 1 and type(self._data[0]) is str:
            return 3
        return self._current_stage + 1

    @certification_download(sync=True)
    def _stage_1(self, token: str) -> RequestPackageList:
        author_id = int(self._params_list[0])
        req_package = UserWorksAPI.get_package(author_id, token)
        return [req_package]

    @staticmethod
    def _stage_1_parser(result_package: ResultPackage) -> ParseResult:
        author_id = result_package.msg[0]
        page_number = UserWorksAPI.parse_page(result_package.result)
        if page_number == 1:
            return ParseResult(author_id, UserWorksAPI.parse_picture(result_package.result))
        else:
            return ParseResult(author_id, [(author_id, i) for i in range(1, page_number+1)])

    @certification_download(sync=True)
    def _stage_2(self, token: str) -> RequestPackageList:
        return [UserWorksAPI.get_package(author_id, token, page) for author_id, page in self._params_list]

    @staticmethod
    def _stage_2_parser(result_package: ResultPackage) -> ParseResult:
        picture_url = UserWorksAPI.parse_picture(result_package.result)
        return ParseResult(result_package.msg, picture_url)

    @direct_download(sync=False)
    def _stage_3(self) -> RequestPackageList:
        return [UserWorksAPI.get_picture_request_package(url) for url in self._params_list]
