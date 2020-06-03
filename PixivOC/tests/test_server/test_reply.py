from main import *


Account = ''
Password = ''


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


change_mode = create_json('S1', 4, proxy_mode=2)
login = create_json('S2', 1, account=Account, password=Password)
create_task = create_json('S3', 101, keyword='79468013', task_name='TestServer', save_path='.')
query_all_details = create_json('S4', 15)

bytes_data_1 = json.dumps(change_mode).encode()
bytes_data_2 = json.dumps(login).encode()
bytes_data_3 = json.dumps(create_task).encode()
bytes_data_4 = json.dumps(query_all_details).encode()

accept_queue.put(bytes_data_1)
accept_queue.put(bytes_data_2)
accept_queue.put(bytes_data_3)
accept_queue.put(bytes_data_4)

while True:
    if not send_queue.empty():
        bytes_ = send_queue.get()
        unit = json.loads(bytes_.decode())
        print(unit)
