from typing import Any
from flask import Flask, request
from controller import Check, Server, ServerPort


Check.assert_task_cls_meet_specifications()
server = Server()
app = Flask(__name__)


def start() -> None:
    app.run('127.0.0.1', ServerPort)


def extract_args(word_list: list) -> (bool, list):
    args_list = []
    try:
        for keyword, type_ in word_list:
            args = request.args.get(keyword, type=type_)
            if args is None:
                return False, []
            args_list.append(args)
        return True, args_list
    except KeyError:
        return False, []
    except ValueError:
        return False, []


def wrap_return_value(b: bool, result: Any) -> dict:
    return {
        "status": b,
        "result": result
    }


'''
sys
'''


@app.route('/sys/exit')
def exit_() -> dict:
    pass


'''
user
'''


@app.route('/user/login')
def login() -> dict:
    b, args_list = extract_args([
        ['account', str],
        ['password', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.login(*args_list))


@app.route('/user/refreshToken')
def refresh_token() -> dict:
    return wrap_return_value(True, server.refresh_token())


@app.route('/user/logout')
def logout() -> dict:
    pass


@app.route('/user/isLogin')
def is_login() -> dict:
    return wrap_return_value(True, server.is_login())


@app.route('/user/tokenMsg')
def token_msg() -> dict:
    return wrap_return_value(True, server.token_msg())


'''
environment
'''


@app.route('/environment/setProxyMode')
def set_proxy_mode() -> dict:
    b, args_list = extract_args([
        ['mode', int],
        ['address', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_proxy_mode(*args_list))


@app.route('/environment/setTimeout')
def set_timeout() -> dict:
    b, args_list = extract_args([
        ['timeout', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_timeout(*args_list))


@app.route('/environment/setConcurrencyNumber')
def set_concurrency_number() -> dict:
    b, args_list = extract_args([
        ['number', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_concurrency_number(*args_list))


@app.route('/environment/setIntervalTime')
def set_interval_time() -> dict:
    b, args_list = extract_args([
        ['second', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_interval_time(*args_list))


@app.route('/environment/setIncrement')
def set_increment() -> dict:
    b, args_list = extract_args([
        ['increment', bool]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_increment(*args_list))


@app.route('/environment/getEnvironment')
def get_environment() -> dict:
    return wrap_return_value(True, server.get_environment())


'''
operation
'''


@app.route('/operation/startTask')
def start_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.start_task(*args_list))


@app.route('/operation/stopTask')
def stop_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.stop_task(*args_list))


@app.route('/operation/deleteTask')
def delete_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.delete_task(*args_list))


@app.route('/operation/taskDetails')
def task_details() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.task_details(*args_list))


@app.route('/operation/allTaskDetails')
def all_task_details() -> dict:
    return wrap_return_value(True, server.all_task_details())


'''
create
'''


@app.route('/create/singleWork')
def single_work() -> dict:
    b, args_list = extract_args([
        ['keyWord', str],
        ['taskName', str],
        ['savePath', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.single_work(*args_list))


@app.route('/create/userWorks')
def user_works() -> dict:
    b, args_list = extract_args([
        ['keyWord', str],
        ['taskName', str],
        ['savePath', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.user_works(*args_list))


@app.route('/create/workDetails')
def work_details() -> dict:
    pass


@app.route('/create/userWorksLink')
def user_works_link() -> dict:
    pass


if __name__ == '__main__':
    start()
