"""
MainFetchCallback and ChildFetchCallback all running in child thread.
"""
import asyncio
from asyncio import Future
from time import sleep
from typing import Callable, Union

from threading import Thread
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError
from requests import session

from .log import downloader_logger
from .proxy import ProxyManager
from .connector import AsyncSniConnector, SyncSniConnector
from .exception import KnownException, UnknownException
from .abs_downloader import (
    RequestPackage,
    ResultPackage,
    RequestPackageList,
    ExitState
)
from .structure import (
    ClientSessionParams,
    BreakSign,
    SyncFuture
)


CLIENT_SESSION_PARAMS = ClientSessionParams()
PROXY_MANAGER = ProxyManager()


# variable in main thread
class DownloadThread:
    def __init__(
        self,
        child_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
        main_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
        sync: bool = False
    ):
        self._Loop = asyncio.new_event_loop()
        self._ChildFetchCallback = child_fetch_callback
        self._MainFetchCallback = main_fetch_callback
        self._Thread = None
        self.Sync = sync
        self._BreakSign = BreakSign()
        downloader_logger.debug('Create download thread manager variable.')

    def is_alive(self) -> bool:
        if self._Thread is not None:
            return self._Thread.is_alive()
        return False

    def start(self, request_package_list: RequestPackageList) -> None:

        temp = [CLIENT_SESSION_PARAMS.convert(package) for package in request_package_list]
        real_package_list = [PROXY_MANAGER.convert(package) for package in temp]

        if self.Sync:
            return self._sync_start(real_package_list)
        else:
            return self._async_start(real_package_list)

    def _async_start(self, request_package_list: RequestPackageList) -> None:

        self._Thread = Thread(
            target=start_child_thread_loop,
            args=(self._Loop,
                  self._BreakSign,
                  self._MainFetchCallback,
                  self._ChildFetchCallback,
                  request_package_list,
                  CLIENT_SESSION_PARAMS.headers,
                  CLIENT_SESSION_PARAMS.total_timeout,
                  CLIENT_SESSION_PARAMS.concurrency_number)
        )

        self._Thread.daemon = True
        self._Thread.start()

    def _sync_start(self, request_package_list: RequestPackageList) -> None:
        self._Thread = Thread(
            target=start_requests_session,
            args=(self._BreakSign,
                  self._MainFetchCallback,
                  self._ChildFetchCallback,
                  request_package_list,
                  CLIENT_SESSION_PARAMS.headers,
                  CLIENT_SESSION_PARAMS.total_timeout,
                  CLIENT_SESSION_PARAMS.interval)
        )

        self._Thread.daemon = True
        self._Thread.start()

    def stop(self) -> None:
        self._BreakSign.make_true()
        if self.Sync is False:
            pending = asyncio.all_tasks(self._Loop)
            for task in pending:
                task.cancel()
                task.remove_done_callback(self._ChildFetchCallback)
        downloader_logger.debug('Close download thread.')

    def safe_stop(self) -> None:
        self.stop()
        while self.is_alive():
            sleep(0.01)
        downloader_logger.debug('Download thread alive is False.')


'''
async downloader
'''


# run in child thread
def start_child_thread_loop(loop: asyncio.BaseEventLoop,
                            break_sign: BreakSign,
                            main_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
                            child_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
                            request_package_list: RequestPackageList,
                            headers: Union[dict, None],
                            total_timeout: int,
                            concurrency_number: int) -> None:
    downloader_logger.debug('Async downloader start.')

    asyncio.set_event_loop(loop)
    main_fetch_task = loop.create_task(
        main_fetch(
            request_package_list,
            break_sign,
            child_fetch_callback,
            headers, total_timeout, concurrency_number
        )
    )
    main_fetch_task.add_done_callback(main_fetch_callback)
    loop.run_until_complete(main_fetch_task)
    downloader_logger.debug('Async download thread over.')


# main fetch (control stream)
async def main_fetch(request_package_list: RequestPackageList,
                     break_sign: BreakSign,
                     child_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
                     headers: Union[dict, None], total_timeout: int, concurrency_number: int) -> ResultPackage:
    loop = asyncio.get_event_loop()
    connector = AsyncSniConnector(loop=loop)
    client_timeout = ClientTimeout(total=total_timeout)
    async with ClientSession(loop=loop,
                             connector=connector, timeout=client_timeout) as client:

        tasks = [asyncio.create_task(child_fetch(client, package)) for package in request_package_list]
        for task in tasks:
            task.add_done_callback(child_fetch_callback)

        split_list = [tasks[i: i+concurrency_number] for i in range(0, len(tasks), concurrency_number)]

        try:
            for split_tasked_list in split_list:
                await asyncio.wait(split_tasked_list)
        except asyncio.CancelledError:
            return ResultPackage(ExitState.Cancel, None)

        if break_sign:
            return ResultPackage(ExitState.Cancel, None)
        else:
            return ResultPackage(ExitState.Normal, None)
        # The process can return normally,
        # because only the callback function of child_fetch is cancelled


# child fetch (request)
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
    except asyncio.TimeoutError:
        return ResultPackage(None, None, KnownException('asyncio.TimeoutError'))
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


# run in child thread
def start_requests_session(break_sign: BreakSign,
                           main_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
                           child_fetch_callback: Callable[[Union[Future, SyncFuture]], None],
                           request_package_list: RequestPackageList,
                           headers: Union[dict, None], total_timeout: int, interval: int) -> None:
    downloader_logger.debug('Sync downloader start.')

    s = session()
    s.mount('https://', SyncSniConnector())

    break_loop = break_sign  # this value should be False

    for package in request_package_list:
        if break_loop:
            break

        exception = False
        resp = None
        # i don't know why this warning appears in the statement child_fetch_callback(***
        # Local variable 'resp' might be referenced before assignment
        proxy = {key: package.proxy for key in ['http', 'https']}
        try:
            if package.method == 'GET':
                resp = s.get(
                    package.url,
                    headers=package.headers, params=package.params,
                    data=package.data, proxies=proxy,
                    timeout=total_timeout
                )
            else:
                resp = s.post(
                    package.url,
                    headers=package.headers, params=package.params,
                    data=package.data, proxies=proxy,
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
