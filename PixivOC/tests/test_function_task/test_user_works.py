import time
from main import *


send_queue, accept_queue = Queue(), Queue()
TOKEN_MANAGER.set_send_queue(send_queue)
task_manager = TaskManager(send_queue)
server = Server(task_manager, send_queue, accept_queue)
server.start()


def create_json(number: str, command: int, account: str = '', password: str = '',
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


change_mode = create_json('S1', 3, proxy_mode=2)
create_task = create_json('S2', 104, keyword='28145748', task_name='TestUserWorks', save_path='.')


bytes_data_1 = json.dumps(change_mode).encode()
bytes_data_2 = json.dumps(create_task).encode()

accept_queue.put(bytes_data_1)
accept_queue.put(bytes_data_2)

time.sleep(1)

task_id = 0
while True:
    if send_queue.empty():
        break
    bytes_ = send_queue.get_nowait()
    unit = json.loads(bytes_.decode())
    print(unit)
    if unit['SendType'] == 11:
        task_id = unit['Content']

start_task = create_json('S3', 11, tid=task_id)
bytes_data_3 = json.dumps(start_task).encode()
accept_queue.put(bytes_data_3)

while True:
    if not send_queue.empty():
        bytes_ = send_queue.get()
        unit = json.loads(bytes_.decode())
        print(unit)
        if unit['SendType'] == 14:
            break

time.sleep(5)
