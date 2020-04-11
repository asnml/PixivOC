# import time
import asyncio
from Download import *
# from threading import currentThread
from copy import deepcopy
from tests.test_downloader.HashValue import equal

DOWNLOAD_COUNT = 0
DOWNLOAD_MAX = 0

CANCEL_THREAD = None


def create_baidu_package_list():
    domain_list = [
        ('https://www.baidu.com/img/bd_logo1.png',
         '1.png'),
        ('https://www.baidu.com/img/baidu_resultlogo@2.png',
         '2.png'),
        ('https://dss0.bdstatic.com/5aV1bjqh_Q23odCf/static/superman/img/logo_top-e3b63a0b1b.png',
         '3.png'),
        ('https://dss2.bdstatic.com/kfoZeXSm1A5BphGlnYG/icon/weather/aladdin/png_18/a2.png',
         '4.png')
    ]
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/78.0.3904.97 Safari/537.36"
    }
    return [RequestPackage(x[0], 'GET', headers=headers, msg=x[1]) for x in domain_list]


def create_pixiv_package_list():
    url_list = [
        (f"https://i.pximg.net/img-original/img/2019/02/22/17/26/17/73324421_p0.jpg",
         "73324421", "73324421.jpg"),
        (f"https://i.pximg.net/img-original/img/2019/06/29/01/05/39/75454114_p0.jpg",
         "75454114", "75454114.jpg"),
        (f"https://i.pximg.net/img-original/img/2019/07/06/00/00/02/75568860_p0.jpg",
         "75568860", "75568860.jpg"),
        ("https://i.pximg.net/img-original/img/2019/12/10/20/37/30/78232796_p0.jpg",
         "78232796", "78232796.jpg")
    ]
    ret = []
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/78.0.3904.97 Safari/537.36"
    }
    for url in url_list:
        h = deepcopy(headers)
        h['Referer'] = f"https://www.pixiv.net/artworks/{url[1]}"
        ret.append(RequestPackage(url[0], 'GET', headers=h, msg=url[2]))
    return ret


def main_fetch_callback(future: asyncio.Future) -> None:
    # print(f'Callback thread id: {currentThread().ident}')
    print(f'Exit state: {future.result().result}')


def child_fetch_callback_save_picture(future: asyncio.Future) -> None:
    result_package = future.result()  # type: ResultPackage
    if result_package.exception is None:
        if equal(result_package.result):
            print(f'Download {result_package.msg}')
    else:
        print(result_package.exception)

    global DOWNLOAD_COUNT
    DOWNLOAD_COUNT += 1


def child_fetch_callback_cancel(future: asyncio.Future) -> None:
    result_package = future.result()  # type: ResultPackage
    if result_package.exception is None:
        if equal(result_package.result):
            print(f'Download {result_package.msg}')
    else:
        print(result_package.exception)

    # 模拟用户调用
    CANCEL_THREAD.close()


def test_async_domain():
    PROXY_MANAGER.change_to_direct()
    domain_package_list = create_baidu_package_list()
    domain_thread = DownloadThread(child_fetch_callback_save_picture)
    domain_thread.start(main_fetch_callback, domain_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests async domain over.')


def test_async_proxy():
    PROXY_MANAGER.change_to_proxy('http://127.0.0.1:1081')
    proxy_package_list = create_pixiv_package_list()
    proxy_thread = DownloadThread(child_fetch_callback_save_picture)
    proxy_thread.start(main_fetch_callback, proxy_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests async proxy over.')


def test_async_ip():
    PROXY_MANAGER.change_to_ip()
    ip_package_list = create_pixiv_package_list()
    ip_thread = DownloadThread(child_fetch_callback_save_picture)
    ip_thread.start(main_fetch_callback, ip_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests async ip over.')


def test_async_cancel():
    global CANCEL_THREAD
    domain_package_list = create_baidu_package_list()
    CANCEL_THREAD = DownloadThread(child_fetch_callback_cancel)
    CANCEL_THREAD.start(main_fetch_callback, domain_package_list)


def test_sync_domain():
    PROXY_MANAGER.change_to_direct()
    domain_package_list = create_baidu_package_list()
    download_thread = DownloadThread(child_fetch_callback_save_picture, sync=True)
    download_thread.start(main_fetch_callback, domain_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests sync domain over.')


def test_sync_proxy():
    PROXY_MANAGER.change_to_proxy('http://127.0.0.1:1081')
    proxy_package_list = create_pixiv_package_list()
    proxy_thread = DownloadThread(child_fetch_callback_save_picture, sync=True)
    proxy_thread.start(main_fetch_callback, proxy_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests sync proxy over.')


def test_sync_ip():
    PROXY_MANAGER.change_to_ip()
    ip_package_list = create_pixiv_package_list()
    ip_thread = DownloadThread(child_fetch_callback_save_picture, sync=True)
    ip_thread.start(main_fetch_callback, ip_package_list)

    _ = DOWNLOAD_COUNT + 4
    while DOWNLOAD_COUNT < _:
        pass
    print('tests sync ip over.')


if __name__ == '__main__':
    # print(f'Main thread id: {currentThread().ident}')

    # async tests

    # test_async_domain()
    # test_async_proxy()
    test_async_ip()

    # sync tests

    # test_sync_domain()
    # test_sync_proxy()

    # this tests must be done separately.
    # test_async_cancel()
    # time.sleep(5)

    # test_sync_ip()
    # this function exist error.
    # will cause SSL exception: domain i.pximg.net not match a248.e.akamai.net
