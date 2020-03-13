from math import ceil
from json import loads
from typing import Any
from re import compile, findall
from Download import RequestPackage

PRE_PAGE = 500


class BaseApi:
    suffix_pattern = compile(r'^.+/((\d+).+)$')
    old_domain = "https://i.pximg.net"
    new_domain = "https://tc-pximg01.techorus-cdn.com"

    @staticmethod
    def get_package(*args, **kwargs) -> RequestPackage:
        raise Exception('Please override ths function.')

    @staticmethod
    def parse_result(result: bytes) -> Any:
        raise Exception('Please override ths function.')

    @staticmethod
    def parse_page(result: bytes, pre_page: int = PRE_PAGE) -> int:
        raise Exception('Please override ths function.')

    @staticmethod
    def parse_picture(result: bytes) -> list:
        raise Exception('Please override ths function.')

    @staticmethod
    def public_api_header(token: str) -> dict:
        return {
            'Referer': 'http://spapi.pixiv.net/',
            'User-Agent': 'PixivIOSApp/5.8.7',
            'Authorization': f'Bearer {token}'
        }

    @staticmethod
    def app_api_header(token: str) -> dict:
        return {
            'host': 'app-api.pixiv.net',
            'App-OS': 'ios',
            'App-OS-Version': '12.2',
            'App-Version': '7.6.2',
            'User-Agent': 'PixivIOSApp/7.6.2 (iOS 12.2; iPhone9,1)',
            'Authorization': f'Bearer {token}'
        }

    @staticmethod
    def replace_domain(url: str):
        return url.replace(BaseApi.old_domain, BaseApi.new_domain, 1)

    @staticmethod
    def get_picture_request_package(url: str) -> RequestPackage:
        picture_name, pid = findall(BaseApi.suffix_pattern, url)[0]
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/78.0.3904.97 Safari/537.36",
            'Host': "i.pximg.net",
            'SNI-Host': "i.pximg.net",
            # 'Referer': f"https://www.pixiv.net/artworks/{pid}"
        }
        return RequestPackage(url, 'GET', headers=headers, msg=(picture_name, url))


class WorkDetailsAPI(BaseApi):
    @staticmethod
    def get_package(work_id, token, include_sanity_level=False) -> RequestPackage:
        url = f'https://public-api.secure.pixiv.net/v1/works/{work_id}.json'
        params = {
            'image_sizes': 'px_128x128,small,medium,large,px_480mw',
            'include_stats': 'true',
            'include_sanity_level': str(include_sanity_level).lower()
        }
        return RequestPackage(
            url,
            'GET',
            headers=BaseApi.public_api_header(token),
            params=params,
            msg=work_id
        )

    @staticmethod
    def parse_result(result: bytes) -> dict:
        result = loads(result, encoding='utf-8')
        if result['status'] == 'success':
            return result['response']
        else:
            system = result['errors']['system']  # type: dict
            if 'code' in system.keys() and system['code'] == 206:
                return {'Error': 'Work has been delete'}
            else:
                return {'Error': 'Request failed.'}


class SingleWorkAPI(BaseApi):
    @staticmethod
    def get_package(work_id, token, include_sanity_level=False) -> RequestPackage:
        url = f'https://public-api.secure.pixiv.net/v1/works/{work_id}.json'
        params = {
            'image_sizes': 'px_128x128,small,medium,large,px_480mw',
            'include_stats': 'true',
            'include_sanity_level': str(include_sanity_level).lower()
        }
        return RequestPackage(
            url,
            'GET',
            headers=BaseApi.public_api_header(token),
            params=params,
            msg=work_id
        )

    @staticmethod
    def parse_picture(result: bytes) -> list:
        result = loads(result, encoding='utf-8')
        if result['status'] == 'success':
            picture_url_list = []
            for picture in result['response']:
                page_count = picture['page_count']
                if page_count == 1:
                    url = BaseApi.replace_domain(picture['image_urls']['large'])
                    picture_url_list.append(url)
                else:
                    front, number, back = findall(UserWorksAPI.page_count_pattern, picture['image_urls']['large'])[0]
                    for i in range(page_count):
                        url = BaseApi.replace_domain(f'{front}{i}{back}')
                        picture_url_list.append(url)
            return picture_url_list
        else:
            return []


class UserWorksAPI(BaseApi):
    page_count_pattern = compile(r'^(.+\d+_[a-z]+)(\d)(.+)$')

    @staticmethod
    def get_package(author_id: int, token: str,
                    page: int = 1, per_page: int = PRE_PAGE, image_sizes: str = 'large',
                    include_stats: bool = True, include_sanity_level: bool = True) -> RequestPackage:
        url = f'https://public-api.secure.pixiv.net/v1/users/{author_id}/works.json'
        if image_sizes == 'all':
            # image_sizes = 'px_128x128,px_480mw,large'
            image_sizes = 'large'
        params = {
            'page': page,
            'per_page': per_page,
            'include_stats': 'true' if include_stats is True else 'false',
            'include_sanity_level': 'true' if include_sanity_level is True else 'false',
            'image_sizes': image_sizes
        }
        return RequestPackage(
            url,
            'GET',
            headers=BaseApi.public_api_header(token),
            params=params,
            msg=(author_id, page)
        )

    @staticmethod
    def parse_page(result: bytes, pre_page: int = PRE_PAGE) -> int:
        result = loads(result, encoding='utf-8')
        total = result['pagination']['total']
        return ceil(total/pre_page)

    @staticmethod
    def parse_picture(result: bytes) -> list:
        result = loads(result, encoding='utf-8')
        picture_url_list = []
        for picture in result['response']:
            page_count = picture['page_count']
            if page_count == 1:
                url = BaseApi.replace_domain(picture['image_urls']['large'])
                picture_url_list.append(url)
            else:
                front, number, back = findall(UserWorksAPI.page_count_pattern, picture['image_urls']['large'])[0]
                for i in range(page_count):
                    url = BaseApi.replace_domain(f'{front}{i}{back}')
                    picture_url_list.append(url)
        return picture_url_list
