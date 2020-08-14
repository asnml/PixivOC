import json
from os import path, listdir
from time import sleep
from datetime import datetime
from threading import Thread, Lock
from log import core_logger
from mobileToken import TOKEN_MANAGER
from task import StorageUnit
from Download import PROXY_MANAGER, CLIENT_SESSION_PARAMS
from taskTypes import BaseTask, TaskTypeList, SingleWork, UserWorks


ServerPort = 13575

DATA_FILE_NAME = 'Data.json'
SLEEP_TIME = 0.1

SaveLock = Lock()
AutoSaveTime = 300  # unit: second


class Check:
    @staticmethod
    def assert_task_cls_meet_specifications() -> None:
        id_list = []
        name_list = []
        for task_cls in TaskTypeList:
            assert 'TypeID' in dir(task_cls)
            assert 'TypeName' in dir(task_cls)
            assert task_cls.TypeID not in id_list
            assert task_cls.TypeName not in name_list
            id_list.append(task_cls.TypeID)
            name_list.append(task_cls.TypeName)

    @staticmethod
    def all(task_name: str, save_path: str, allow_null: bool) -> bool:
        if Check.task_name(task_name) and Check.save_path(save_path, allow_null):
            return True
        return False

    @staticmethod
    def task_name(task_name: str) -> bool:
        illegal_char_list = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_char_list:
            if task_name.find(char) != -1:
                return False
        return True

    @staticmethod
    def save_path(save_path: str, allow_null: bool) -> bool:
        if allow_null and save_path == '':
            return True
        elif not allow_null and save_path == '':
            return False
        abs_path = path.abspath(save_path)
        return path.isdir(abs_path)


class TaskManager:
    def __init__(self):
        self.TaskMapping = dict()  # tid: instance
        self._load_tasks()

        self._AutoSaveThread = Thread(target=self._auto_save_thread)
        self._AutoSaveThread.daemon = True
        self._AutoSaveThread.start()

    def exit(self):
        for task in self.TaskMapping.values():  # type: BaseTask
            task.safe_stop()
        self._dump_tasks()

    @staticmethod
    def _get_timestamp() -> int:
        return int(datetime.now().timestamp())

    @staticmethod
    def _find_task(type_id: int) -> BaseTask or None:
        for task_cls in TaskTypeList:
            if type_id == task_cls.TypeID:
                return task_cls
        return None

    def _auto_save_thread(self):
        while True:
            sleep(AutoSaveTime)
            SaveLock.acquire()
            self._dump_tasks()
            SaveLock.release()

    def _load_tasks(self) -> None:
        if DATA_FILE_NAME not in listdir('.'):
            file = open(DATA_FILE_NAME, 'w')
            file.close()
        else:
            with open(DATA_FILE_NAME) as file:
                data = json.load(file)
            for task in data:
                storage_unit = StorageUnit(*task)
                task_cls = self._find_task(storage_unit.TypeID)
                self.TaskMapping[storage_unit.TID] = task_cls(storage_unit)
            core_logger.info('Load tasks.')

    def _dump_tasks(self) -> None:
        writing = []
        for task in self.TaskMapping.values():  # type: BaseTask
            writing.append(task.export_storage().json())
        with open(DATA_FILE_NAME, 'w', encoding='utf-8') as file:
            json.dump(writing, file)
        core_logger.debug('Dump tasks.')

    def start(self, tid: int) -> bool:
        for task_tid in self.TaskMapping.keys():
            if tid == task_tid:
                task = self.TaskMapping[task_tid]  # type: BaseTask
                task.start()
                return True
        return False

    def stop(self, tid: int) -> bool:
        for task_tid in self.TaskMapping.keys():
            if tid == task_tid:
                task = self.TaskMapping[task_tid]  # type: BaseTask
                task.stop()
                return True
        return False

    def delete(self, tid) -> bool:
        find = None
        for task_tid in self.TaskMapping.keys():
            if tid == task_tid:
                find = task_tid
                task = self.TaskMapping[task_tid]  # type: BaseTask
                task.stop()
        if find is not None:
            del self.TaskMapping[find]
            return True
        else:
            return False

    def detail(self, tid) -> list:
        for task_tid in self.TaskMapping.keys():
            if tid == task_tid:
                task = self.TaskMapping[task_tid]  # type: BaseTask
                msg = task.msg
                return msg
        return []

    def all_task_detail(self) -> list:
        return [task.msg for task in self.TaskMapping.values()]

    # *********************
    # Create task functions
    # *********************

    def add_single_keyword_task(self, keyword: str, task_name: str, save_path: str,
                                int_keyword: bool, allow_null: bool, cls) -> tuple:
        if not Check.all(task_name, save_path, allow_null):
            return False, []
        if int_keyword:
            try:
                keyword = int(keyword)
            except ValueError:
                return False, []
        type_id = cls.TypeID
        timestamp = self._get_timestamp()  # if you use program quickly create task, may be will repeat.
        storage_unit = StorageUnit(
            timestamp, task_name, type_id, False, 1, [keyword], [], save_path
        )
        task = cls(storage_unit)  # type: BaseTask
        self.TaskMapping[timestamp] = task
        msg = task.msg  # type: tuple
        return True, msg


class EnvironmentSetting:
    @staticmethod
    def set_proxy_mode(mode_code: int, proxy_address: str = None) -> bool:
        """
        Direct: 0, Proxy: 1, IP: 2
        :param mode_code: The mode of you want.
        :param proxy_address: Proxy ip address.
        :return:
        """
        try:
            assert mode_code in [0, 1, 2]
            if mode_code == 1:
                assert proxy_address is not None
        except AssertionError:
            return False
        if mode_code == 0:
            return PROXY_MANAGER.change_to_direct()
        if mode_code == 1:
            return PROXY_MANAGER.change_to_proxy(proxy_address)
        if mode_code == 2:
            return PROXY_MANAGER.change_to_ip()

    @staticmethod
    def set_timeout(timeout: int) -> bool:
        return CLIENT_SESSION_PARAMS.set_total_timeout(timeout)

    @staticmethod
    def set_concurrency_number(number: int) -> bool:
        return CLIENT_SESSION_PARAMS.set_concurrency_number(number)

    @staticmethod
    def set_interval_time(interval: int) -> bool:
        return CLIENT_SESSION_PARAMS.set_interval(interval)

    @staticmethod
    def set_increment(b: bool) -> bool:
        try:
            assert type(b) is bool
        except AssertionError:
            return False
        BaseTask.Increment = b
        return True

    @staticmethod
    def get_setting() -> [str, str, int, int, int]:
        proxy, proxy_address = PROXY_MANAGER.get_setting()
        timeout = CLIENT_SESSION_PARAMS.total_timeout
        concurrency_number = CLIENT_SESSION_PARAMS.concurrency_number
        interval_time = CLIENT_SESSION_PARAMS.interval
        return proxy, proxy_address, timeout, concurrency_number, interval_time


class Server:
    def __init__(self):
        self._TaskManager = TaskManager()

    '''
    sys
    '''

    def exit(self) -> bool:
        pass

    '''
    user
    '''

    @staticmethod
    def login(account: str, password: str) -> bool:
        return TOKEN_MANAGER.login(account, password)

    @staticmethod
    def refresh_token():
        if not TOKEN_MANAGER.has_refresh_token:
            return False
        return TOKEN_MANAGER.refresh_auth_token()

    def logout(self) -> bool:
        pass

    @staticmethod
    def is_login() -> bool:
        return TOKEN_MANAGER.has_refresh_token

    @staticmethod
    def token_msg() -> str:
        return TOKEN_MANAGER.msg

    '''
    environment
    '''

    @staticmethod
    def set_proxy_mode(mode: int, address: str) -> bool:
        return EnvironmentSetting.set_proxy_mode(mode, address)

    @staticmethod
    def set_timeout(timeout: int) -> bool:
        return EnvironmentSetting.set_timeout(timeout)

    @staticmethod
    def set_concurrency_number(number: int) -> bool:
        return EnvironmentSetting.set_concurrency_number(number)

    @staticmethod
    def set_interval_time(second: int) -> bool:
        return EnvironmentSetting.set_interval_time(second)

    @staticmethod
    def set_increment(increment: bool) -> bool:
        return EnvironmentSetting.set_increment(increment)

    @staticmethod
    def get_environment() -> tuple:
        return EnvironmentSetting.get_setting()

    '''
    operation
    '''

    def start_task(self, tid: int) -> (bool, str):
        if not TOKEN_MANAGER.has_refresh_token:
            return False, 'Please login.'
        return self._TaskManager.start(tid), ""

    def stop_task(self, tid: int) -> (bool, str):
        if not TOKEN_MANAGER.has_refresh_token:
            return False, 'Please login.'
        return self._TaskManager.stop(tid), ""

    def delete_task(self, tid: int) -> (bool, str):
        if not TOKEN_MANAGER.has_refresh_token:
            return False, 'Please login.'
        return self._TaskManager.delete(tid), ""

    def task_detail(self, tid: int) -> list:
        return self._TaskManager.detail(tid)

    def all_task_detail(self) -> list:
        return self._TaskManager.all_task_detail()

    '''
    create
    '''

    def single_work(self, keyword: str, task_name: str, save_path: str):
        return self._TaskManager.add_single_keyword_task(
            keyword, task_name, save_path, True, False, SingleWork
        )

    def user_works(self, keyword: str, task_name: str, save_path: str):
        return self._TaskManager.add_single_keyword_task(
            keyword, task_name, save_path, True, False, UserWorks
        )

    def work_details(self):
        pass

    def user_works_link(self):
        pass
