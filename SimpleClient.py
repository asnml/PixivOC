import sys
import time
import json
import selectors
from os import system
from socket import socket
from struct import pack, unpack
from datetime import datetime
from threading import Thread
from multiprocessing import Process, Queue

SERVER_IP_ADDRESS = ('127.0.0.1', 13575)

TaskList = []
TokenStatus = False
GeneratorMapping = {}
SendQueue, AcceptQueue = Queue(), Queue()


'''
TransportClient
传输客户端
'''


class TransportClient(Process):
    def __init__(self, accept_queue: Queue, send_queue: Queue):
        super().__init__()
        self._Client = socket()
        self._ClientAcceptQueue = accept_queue
        self._ClientSendQueue = send_queue

    def run(self) -> None:
        print('Run child process.')
        self.connect_server()

    def connect_server(self):
        try:
            self._Client.connect(SERVER_IP_ADDRESS)
            print('Connected to server.')
        except ConnectionRefusedError:
            print('Server has down.')
            sys.exit(0)

        selector = selectors.DefaultSelector()
        selector.register(self._Client, selectors.EVENT_READ)
        while True:
            events = selector.select(timeout=0.1)
            if events:
                data = self._Client.recv(4)
                if not data:
                    sys.exit(0)
                length = unpack('i', data)[0]
                data = self._Client.recv(length)
                content = unpack(f'{length}s', data)[0]
                self._ClientAcceptQueue.put(content)

            if not self._ClientSendQueue.empty():
                encoded_msg = self._ClientSendQueue.get()
                msg_length = len(encoded_msg)
                length_pack = pack('i', msg_length)
                msg_pack = pack(f'{msg_length}s', encoded_msg)
                self._Client.send(length_pack)
                self._Client.send(msg_pack)


'''
Data mode.
数据模型
'''


class Task:
    def __init__(self, tid, task_name, task_type, stage_name, running, now, total, save_path):
        self.TID = tid
        self.TaskName = task_name
        self.TaskType = task_type
        self.StageName = stage_name
        self.Running = running
        self.Now = now
        self.Total = total
        self.SavePath = save_path

    def update(self, tid, task_name, task_type, stage_name, running, less, total, save_path):
        self.TID = tid
        self.TaskName = task_name
        self.TaskType = task_type
        self.StageName = stage_name
        self.Running = running
        self.Now = less
        self.Total = total
        self.SavePath = save_path

    def update_progress(self, stage_name, less, total):
        self.StageName = stage_name
        self.Now = less
        self.Total = total

    def string(self):
        return f'{self.TID}, {self.TaskName}, {self.TaskType}, {self.StageName}, ' \
               f'{self.Running}, {self.Now}, {self.Total}, {self.SavePath}'


class AcceptMsgUnit:
    def __init__(self, identification_number: str, send_type: int, content):
        self.IdentificationNumber = identification_number
        self.SendType = send_type
        self.Content = content


'''
Function tools.
'''


def create_identification_number(number: str = None):
    if number is not None:
        return 'R' + number[1:]
    timestamp = str(datetime.now().timestamp()).replace('.', '')
    return f'S{timestamp}'


def create_default_json(number: str, command: int, account: str = '', password: str = '',
                        proxy_mode: int = 100, proxy: str = '', timeout: int = 0, concurrency: int = 0,
                        interval: int = 0, increment: bool = True, tid: int = 0, keyword: str = '',
                        task_name: str = '', save_path: str = ''):
    return {
        'IdentificationNumber': number,
        'Command': command,
        'Account': account,
        'Password': password,
        'ProxyMode': proxy_mode,
        'Proxy': proxy,
        'Timeout': timeout,
        'ConcurrencyNumber': concurrency,
        'IntervalTime': interval,
        'Increment': increment,
        'TID': tid,
        'KeyWord': keyword,
        'TaskName': task_name,
        'SavePath': save_path
    }


'''
Running function.
'''


def accept_queue_obj(accept_queue: Queue):
    # Running in child thread.
    while True:
        if not accept_queue.empty():
            content = accept_queue.get_nowait()  # type: bytes
            d = json.loads(content.decode())
            unit = AcceptMsgUnit(
                d['IdentificationNumber'],
                d['SendType'],
                d['Content']
            )
            accept(unit)
        else:
            time.sleep(0.1)


def send(fn):
    def wrapper(*args, **kwargs):
        generator = fn(*args, **kwargs)
        json_data = next(generator)
        number = json_data['IdentificationNumber']
        return_number = create_identification_number(number)
        global GeneratorMapping
        GeneratorMapping[return_number] = generator
        bytes_data = json.dumps(json_data).encode()
        SendQueue.put(bytes_data)
    return wrapper


def accept(unit: AcceptMsgUnit):
    if unit.IdentificationNumber[0] == 'R':
        find = None
        for number in GeneratorMapping.keys():
            if number == unit.IdentificationNumber:
                find = number
                generator = GeneratorMapping[number]
                try:
                    generator.send(unit)
                except StopIteration:
                    pass
        if find:
            del GeneratorMapping[find]
    else:
        if unit.SendType == 2:
            return process_token_status_change(unit)
        if unit.SendType == 11:
            return process_create_task(unit)
        if unit.SendType == 13:
            return process_task_status_change(unit)
        if unit.SendType == 14:
            return process_task_over(unit)


'''
Process server report
处理服务器主动上报数据
'''


def process_token_status_change(unit: AcceptMsgUnit):
    global TokenStatus
    TokenStatus = unit.Content


def process_create_task(unit: AcceptMsgUnit):
    tid = unit.Content
    return task_detail_2(tid)


def process_task_status_change(unit: AcceptMsgUnit):
    task_report = unit.Content
    for task in TaskList:
        if task.TID == task_report['TID']:
            task.update_progress(*task_report['Content'])


def process_task_over(unit: AcceptMsgUnit):
    task_report = unit.Content
    for task in TaskList:
        if task.TID == task_report['TID']:
            print(f'Task {task.TaskName} download over')


'''
Client send command
实现请求命令的发送以及返回值的处理
'''


@send
def login() -> dict:
    account = input('>>> Please input account: ')
    password = input('>>> Please input password: ')
    yield create_default_json(create_identification_number(), 1, account, password)


def logout():
    print('>>> The function has not been written')


@send
def set_proxy_mode():
    mode = input('>>> Please input mode: ')
    address = input('>>> Please input proxy address: ')
    try:
        mode = int(mode)
        assert mode in [0, 1, 2]
    except ValueError:
        return print('Illegal value.')
    except AssertionError:
        return print('Illegal value.')
    unit = yield create_default_json(create_identification_number(),
                                     3, proxy_mode=mode, proxy=address)
    if unit.Content:
        print('Successfully set proxy mode.')
    else:
        print('Failed to set proxy mode.')


@send
def set_timeout():
    timeout = input('>>> Please input timeout: ')
    try:
        timeout = int(timeout)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 4, timeout=timeout)
    if unit.Content:
        print('Successfully set timeout.')
    else:
        print('Failed to set timeout.')


@send
def set_concurrency_number():
    number = input('>>> Please input concurrency number: ')
    try:
        number = int(number)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 5, concurrency=number)
    if unit.Content:
        print('Successfully set concurrency number.')
    else:
        print('Failed to set concurrency number.')


@send
def set_interval_time():
    interval = input('>>> Please input interval: ')
    try:
        interval = int(interval)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 6, interval=interval)
    if unit.Content:
        print('Successfully set interval time.')
    else:
        print('Failed to set interval time.')


@send
def set_increment():
    increment = input('>>> Please input true or false')
    if increment not in ['true', 'false']:
        return print('Illegal value')
    increment = True if increment == 'true' else False
    unit = yield create_default_json(create_identification_number(), 7, increment=increment)
    if unit.Content:
        print('Successfully set increment.')
    else:
        print('Failed to set increment.')


@send
def start_task():
    tid = input('>>> Please input task id: ')
    try:
        tid = int(tid)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 11, tid=tid)
    if unit.Content:
        print('Successfully start task.')
    else:
        print('Failed to start task.')


@send
def stop_task():
    tid = input('>>> Please input task id: ')
    try:
        tid = int(tid)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 12, tid=tid)
    if unit.Content:
        print('Successfully stop task.')
    else:
        print('Failed to stop task.')


@send
def delete_task():
    tid = input('>>> Please input task id: ')
    try:
        tid = int(tid)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 13, tid=tid)
    if unit.Content:
        print('Successfully delete task.')
    else:
        print('Failed to delete task.')


@send
def task_detail():
    tid = input('>>> Please input task id: ')
    try:
        tid = int(tid)
    except ValueError:
        return print('Illegal value')
    unit = yield create_default_json(create_identification_number(), 14, tid=tid)
    match = False
    global TaskList
    for task in TaskList:
        if task.TID == unit.Content[0]:
            task.update(*unit.Content)
            match = True
            break
    if not match:
        task = Task(*unit.Content)
        TaskList.append(task)


@send
def task_detail_2(tid: int):
    unit = yield create_default_json(create_identification_number(), 14, tid=tid)
    match = False
    global TaskList
    for task in TaskList:
        if task.TID == unit.Content[0]:
            task.update(*unit.Content)
            match = True
            break
    if not match:
        task = Task(*unit.Content)
        TaskList.append(task)


@send
def all_task_detail():
    unit = yield create_default_json(create_identification_number(), 15)
    global TaskList
    for single in unit.Content:
        match = False
        for task in TaskList:
            if task.TID == single[0]:
                task.update(*single)
                match = True
                break
        if not match:
            task = Task(*single)
            TaskList.append(task)


@send
def add_single_word_task():
    work_id = input('>>> Please input work id: ')
    task_name = input('>>> Please input task name: ')
    save_path = input('>>> Please input save path: ')
    try:
        int(work_id)
    except ValueError:
        return print('Illegal work id')
    yield create_default_json(create_identification_number(),
                              102, keyword=work_id, task_name=task_name, save_path=save_path)


@send
def add_user_works_task():
    work_id = input('>>> Please input user id: ')
    task_name = input('>>> Please input task name: ')
    save_path = input('>>> Please input save path: ')
    try:
        int(work_id)
    except ValueError:
        return print('Illegal work id')
    yield create_default_json(create_identification_number(),
                              104, keyword=work_id, task_name=task_name, save_path=save_path)


'''
Main run
'''


def show():
    try:
        while True:
            system('cls')
            for task in TaskList:
                print(task.string())
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def main():
    command_list = [
        'Login',
        'Logout',
        'SetProxyMode',
        'SetTimeout',
        'SetConcurrencyNumber',
        'SetIntervalTime',
        'SetIncrement',
        'StartTask',
        'StopTask',
        'DeleteTask',
        'TaskDetails',
        'AllTaskDetails',
        'AddWorkDetailsTask',
        'AddSingleWorkTask',
        'AddUserWorksTask',
        'Help'
    ]
    while True:
        command = input('>>>')
        if command == '':
            continue
        if command not in command_list:
            print('Error command')
        if command == 'Login':
            login()
        if command == 'Logout':
            logout()
        if command == 'SetProxyMode':
            set_proxy_mode()
        if command == 'SetTimeout':
            set_timeout()
        if command == 'SetConcurrencyNumber':
            set_concurrency_number()
        if command == 'SetIntervalTime':
            set_interval_time()
        if command == 'SetIncrement':
            set_increment()
        if command == 'StartTask':
            start_task()
        if command == 'StopTask':
            stop_task()
        if command == 'DeleteTask':
            delete_task()
        if command == 'TaskDetails':
            task_detail()
        if command == 'AllTaskDetails':
            all_task_detail()
        if command == 'AddSingleWorkTask':
            add_single_word_task()
        if command == 'AddUserWorksTask':
            add_user_works_task()
        if command == 'Show':
            show()
        if command == 'Help':
            for x in command_list:
                print(x)


if __name__ == '__main__':
    add_thread = Thread(target=accept_queue_obj, args=(AcceptQueue,))
    add_thread.daemon = True
    add_thread.start()

    Client = TransportClient(AcceptQueue, SendQueue)
    Client.daemon = True
    Client.start()
    main()
