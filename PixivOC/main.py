import json
from os import path, listdir
from time import sleep
from datetime import datetime
from threading import Thread, Lock
from multiprocessing import Queue
from log import core_logger
from mobileToken import TOKEN_MANAGER
from interface import SendType, Command
from optional import ServerPort
from TransportServer import SingleLinkServer
from task import StorageUnit, BaseTask, BaseTaskStage
from Download import PROXY_MANAGER, CLIENT_SESSION_PARAMS
from structure import PreSendUnit, \
    SendMsgUnit, AcceptMsgUnit, create_identification_number
from taskTypes import TaskTypeList, WorkDetailsTask, SingleWorkTask, \
    UserWorksLinkTask, UserWorksTask


DATA_FILE_NAME = 'Data.json'
SLEEP_TIME = 0.1


SaveLock = Lock()
AutoSaveTime = 300  # unit: second

Running = True


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
    def __init__(self, send_queue: Queue):
        self.TaskMapping = dict()  # tid: instance
        self._SendQueue = send_queue
        self._load_tasks()

        self._AutoSaveThread = Thread(target=self._auto_save_thread)
        self._AutoSaveThread.daemon = True
        self._AutoSaveThread.start()

    def exit(self):
        for task in self.TaskMapping.values():  # type: BaseTask
            task.make_sure_stop()
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

    def _report(self, unit: PreSendUnit):
        identification_number = create_identification_number()
        send_unit = SendMsgUnit(identification_number, unit.SendType, unit.content)
        if unit.SendType == SendType.CreateTask or \
                unit.SendType == SendType.DeleteTask or unit.SendType == SendType.TaskOver:
            SaveLock.acquire()
            self._dump_tasks()
            SaveLock.release()
        if send_unit.effective:
            self._SendQueue.put(send_unit.data)

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
                task_cls = self._find_task(storage_unit.TaskType)
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

    def details(self, tid) -> list:
        for task_tid in self.TaskMapping.keys():
            if tid == task_tid:
                task = self.TaskMapping[task_tid]  # type: BaseTask
                msg = task.msg
                return msg
        return []

    def all_task_details(self) -> list:
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
        type_id = UserWorksTask.TypeID
        timestamp = self._get_timestamp()  # if you use program quickly create task, may be will repeat.
        storage_unit = StorageUnit(
            timestamp, task_name, type_id, False, 1, [keyword], [], save_path
        )
        task = cls(storage_unit)  # type: BaseTask
        self.TaskMapping[timestamp] = task
        msg = task.msg  # type: tuple
        return (True, *msg)


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
        BaseTaskStage.Increment = b
        return True

    @staticmethod
    def get_setting():
        proxy, proxy_address = PROXY_MANAGER.get_setting()
        timeout = CLIENT_SESSION_PARAMS.total_timeout
        concurrency_number = CLIENT_SESSION_PARAMS.concurrency_number
        interval_time = CLIENT_SESSION_PARAMS.interval
        return proxy, proxy_address, timeout, concurrency_number, interval_time


class Server:
    def __init__(self, task_manager: TaskManager, send_queue: Queue, accept_queue: Queue):
        self._TaskManager = task_manager
        self._SendQueue = send_queue
        self._AcceptQueue = accept_queue

    def start(self):
        self.loop_check_accept_queue()

    def loop_check_accept_queue(self):
        while Running:
            if not self._AcceptQueue.empty():
                content = self._AcceptQueue.get()
                unit = AcceptMsgUnit(content)
                if unit.effective:
                    self.reply(unit)
            else:
                sleep(SLEEP_TIME)

    def reply(self, unit: AcceptMsgUnit):
        result = ''

        if not TOKEN_MANAGER.has_refresh_token and unit.command > 10:
            result = [False, 'Please login.']

        elif unit.command == Command.Exit:
            global Running
            Running = False
            reply_number = create_identification_number(unit.IdentificationNumber)
            unit = SendMsgUnit(reply_number, SendType.Reply, True)
            self._SendQueue.put(unit.data)
            self._TaskManager.exit()
            sleep(0.5)
            return

        elif unit.command == Command.Login:
            result = TOKEN_MANAGER.login(
                unit.data['Account'],
                unit.data['Password']
            )

        elif unit.command == Command.Logout:
            pass

        elif unit.command == Command.IsLogin:
            result = TOKEN_MANAGER.has_refresh_token

        elif unit.command == Command.SetProxyMode:
            result = EnvironmentSetting.set_proxy_mode(
                unit.data['ProxyMode'],
                unit.data['Proxy']
            )

        elif unit.command == Command.SetTimeout:
            result = EnvironmentSetting.set_timeout(unit.data['Timeout'])

        elif unit.command == Command.SetConcurrencyNumber:
            result = EnvironmentSetting.set_concurrency_number(unit.data['ConcurrencyNumber'])

        elif unit.command == Command.SetIntervalTime:
            result = EnvironmentSetting.set_interval_time(unit.data['IntervalTime'])

        elif unit.command == Command.SetIncrement:
            result = EnvironmentSetting.set_increment(unit.data['Increment'])

        elif unit.command == Command.GetEnvironment:
            result = EnvironmentSetting.get_setting()

        elif unit.command == Command.StartTask:
            result = self._TaskManager.start(unit.data['TID'])

        elif unit.command == Command.StopTask:
            result = self._TaskManager.stop(unit.data['TID'])

        elif unit.command == Command.DeleteTask:
            result = self._TaskManager.delete(unit.data['TID'])

        elif unit.command == Command.TaskDetails:
            result = self._TaskManager.details(unit.data['TID'])

        elif unit.command == Command.AllTaskDetails:
            result = self._TaskManager.all_task_details()

        elif unit.command == Command.AddWorkDetailsTask:
            result = self._TaskManager.add_single_keyword_task(
                unit.data['KeyWord'], unit.data['TaskName'], '',
                True, True, WorkDetailsTask
            )

        elif unit.command == Command.AddSingleWorkTask:
            result = self._TaskManager.add_single_keyword_task(
                unit.data['KeyWord'], unit.data['TaskName'], unit.data['SavePath'],
                True, False, SingleWorkTask
            )

        elif unit.command == Command.AddUserWorksLinkTask:
            result = self._TaskManager.add_single_keyword_task(
                unit.data['KeyWord'], unit.data['TaskName'], '',
                True, True, UserWorksLinkTask
            )

        elif unit.command == Command.AddUserWorksTask:
            result = self._TaskManager.add_single_keyword_task(
                unit.data['KeyWord'], unit.data['TaskName'], unit.data['SavePath'],
                True, False, UserWorksTask
            )

        reply_number = create_identification_number(unit.IdentificationNumber)
        unit = SendMsgUnit(reply_number, SendType.Reply, result)
        self._SendQueue.put(unit.data)


class Run:
    @staticmethod
    def run():
        Check.assert_task_cls_meet_specifications()
        send_queue, accept_queue = Queue(), Queue()
        task_manager = TaskManager(send_queue)
        TOKEN_MANAGER.set_send_queue(send_queue)
        transport_server = SingleLinkServer(send_queue, accept_queue, ServerPort)
        transport_server.daemon = True
        transport_server.start()
        server = Server(task_manager, send_queue, accept_queue)
        server.start()


if __name__ == '__main__':
    Run.run()
