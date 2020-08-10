"""
MainFetchCallback and ChildFetchCallback all running in child thread.
"""
import asyncio
from asyncio import Future
from time import sleep
from typing import Callable

from threading import Thread
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError
from requests import session

from .log import downloader_logger
from .proxy import ProxyManager
from .connector import AsyncSniConnector, SyncSniConnector
from .exception import KnownException, UnknownException
from .structure import (
    RequestPackage,
    ResultPackage,
    RequestPackageList,
    ClientSessionParams,
    ExitState,
    SyncSign,
    SyncFuture
)


CLIENT_SESSION_PARAMS = ClientSessionParams()
PROXY_MANAGER = ProxyManager()


# thread and event loop level
class DownloadThread:
    def __init__(self, child_fetch_callback: Callable[[Future or SyncFuture], None], sync: bool = False):
        self._Loop = asyncio.new_event_loop()
        self._ChildFetchCallback = child_fetch_callback
        self._Thread = None
        self.Sync = sync
        self.SyncBreakSign = SyncSign()
        downloader_logger.debug('Create download thread manager variable.')

    def is_alive(self) -> bool:
        if self._Thread is not None:
            return self._Thread.is_alive()
        return False

    def start(self, main_fetch_callback: Callable[[Future or SyncFuture], None],
              request_package_list: RequestPackageList):

        real_package_list = [PROXY_MANAGER.convert(package) for package in request_package_list]

        if self.Sync:
            return self._sync_start(main_fetch_callback, real_package_list)
        else:
            return self._async_start(main_fetch_callback, real_package_list)

    def _async_start(self, main_fetch_callback: Callable[[Future or SyncFuture], None],
                     request_package_list: RequestPackageList):

        self._Thread = Thread(
            target=start_child_thread_loop,
            args=(self._Loop,
                  main_fetch_callback,
                  self._ChildFetchCallback,
                  request_package_list,
                  CLIENT_SESSION_PARAMS.headers,
                  CLIENT_SESSION_PARAMS.total_timeout,
                  CLIENT_SESSION_PARAMS.concurrency_number)
        )

        self._Thread.daemon = True
        self._Thread.start()

    def _sync_start(self, main_fetch_callback: Callable[[Future or SyncFuture], None],
                    request_package_list: RequestPackageList):
        self._Thread = Thread(
            target=start_requests_session,
            args=(self.SyncBreakSign,
                  main_fetch_callback,
                  self._ChildFetchCallback,
                  request_package_list,
                  CLIENT_SESSION_PARAMS.headers,
                  CLIENT_SESSION_PARAMS.total_timeout,
                  CLIENT_SESSION_PARAMS.interval)
        )

        self._Thread.daemon = True
        self._Thread.start()

    def close(self):
        if self.Sync:
            self.SyncBreakSign.make_true()
        else:
            pending = asyncio.all_tasks(self._Loop)
            for task in pending:
                task.cancel()
                task.remove_done_callback(self._ChildFetchCallback)
        downloader_logger.debug('Close download thread.')

    def make_sure_close(self):
        self.close()
        while self.is_alive():
            sleep(0.01)
        downloader_logger.debug('Download thread alive is False.')


'''
async downloader
'''


# thread level
def start_child_thread_loop(loop: asyncio.BaseEventLoop,
                            main_fetch_callback: Callable[[Future or SyncFuture], None],
                            child_fetch_callback: Callable[[Future or SyncFuture], None],
                            request_package_list: RequestPackageList,
                            headers: dict or None,
                            total_timeout: int,
                            concurrency_number: int):
    downloader_logger.debug('Async downloader start.')

    asyncio.set_event_loop(loop)
    main_fetch_task = loop.create_task(
        main_fetch(request_package_list, child_fetch_callback,
                   headers, total_timeout, concurrency_number)
    )
    main_fetch_task.add_done_callback(main_fetch_callback)
    loop.run_until_complete(main_fetch_task)
    downloader_logger.debug('Async download thread over.')


# session level
async def main_fetch(request_package_list: RequestPackageList,
                     child_fetch_callback: Callable[[Future or SyncFuture], None],
                     headers: dict or None, total_timeout: int, concurrency_number: int) -> ResultPackage:
    loop = asyncio.get_event_loop()
    connector = AsyncSniConnector(loop=loop)
    client_timeout = ClientTimeout(total=total_timeout)
    async with ClientSession(loop=loop,
                             connector=connector, timeout=client_timeout,
                             headers=headers) as client:

        tasks = [asyncio.create_task(child_fetch(client, package)) for package in request_package_list]
        for task in tasks:
            task.add_done_callback(child_fetch_callback)

        split_list = [tasks[i: i+concurrency_number] for i in range(0, len(tasks), concurrency_number)]

        try:
            for split_tasked_list in split_list:
                await asyncio.wait(split_tasked_list)
        except asyncio.CancelledError:
            return ResultPackage(ExitState.Cancel, None)
        return ResultPackage(ExitState.Normal, None)
        # The process can return normally,
        # because only the callback function of child_fetch is cancelled


# request level
async def child_fetch(client: ClientSession, package: RequestPackage) -> ResultPackage:
    try:
        if package.method == 'GET':
            async with client.get(
                    package.url,
                    headers=package.headers, params=package.params, data=package.data,
                    proxy=package.proxy
            ) as resp:
                return ResultPackage(result=await resp.read(), msg=package.msg)
        else:
            async with client.post(
                    package.url,
                    headers=package.headers, params=package.params, data=package.data,
                    proxy=package.proxy
            ) as resp:
                return ResultPackage(result=await resp.read(), msg=package.msg)
    except asyncio.CancelledError:
        pass
    except ClientConnectorError:
        return ResultPackage(None, None, exception=KnownException('aiohttp.ClientConnectorError'))
    except Exception as e:
        # log.warring('unknow error.')
        # 这种继承方式是获取不到tracer的，待修改
        # Throw exception for callback function
        return ResultPackage(None, None, exception=UnknownException(e))


'''
sync downloader
'''


def start_requests_session(break_sign: SyncSign,
                           main_fetch_callback: Callable[[Future or SyncFuture], None],
                           child_fetch_callback: Callable[[Future or SyncFuture], None],
                           request_package_list: RequestPackageList,
                           headers: dict or None, total_timeout: int, interval: int):
    downloader_logger.debug('Sync downloader start.')

    s = session()
    s.mount('https://', SyncSniConnector())
    s.headers = headers

    break_loop = break_sign  # this value should be False

    for package in request_package_list:
        if break_loop:
            break

        exception = False
        resp = None
        # i don't know why this warning appears in the statement child_fetch_callback(***
        # Local variable 'resp' might be referenced before assignment
        try:
            if package.method == 'GET':
                resp = s.get(
                    package.url,
                    headers=package.headers, params=package.params,
                    data=package.data, proxies={'https': package.proxy},
                    timeout=total_timeout
                )
            else:
                resp = s.post(
                    package.url,
                    headers=package.headers, params=package.params,
                    data=package.data, proxies={'https': package.proxy},
                    timeout=total_timeout
                )
        except Exception as e:
            resp = UnknownException(e)
            exception = True
        finally:
            if break_loop:
                break
            if exception:
                child_fetch_callback(SyncFuture(ResultPackage(None, None, exception=resp)))
            else:
                child_fetch_callback(SyncFuture(ResultPackage(result=resp.content, msg=package.msg)))
            sleep(interval)

    if break_loop:
        main_fetch_callback(SyncFuture(ResultPackage(ExitState.Cancel, None)))
    main_fetch_callback(SyncFuture(ResultPackage(ExitState.Normal, None)))
    downloader_logger.debug('Sync download thread over.')
