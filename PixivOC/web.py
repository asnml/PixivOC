from typing import Any
from flask import Flask, request
from controller import Check, Server, ServerPort


Check.assert_task_cls_meet_specifications()
server = Server()
app = Flask(__name__)


def start() -> None:
    app.run('127.0.0.1', ServerPort)


def extract_args(word_list: list, method_is_post=True) -> (bool, list):
    args_list = []
    try:
        if method_is_post:
            for keyword, type_ in word_list:
                arg = request.form[keyword]
                if type_ == int:
                    arg = int(arg)
                if type_ == bool:
                    if arg == 'true' or arg == 'True':
                        arg = True
                    elif arg == 'false' or arg == 'False':
                        arg = False
                    else:
                        raise ValueError
                args_list.append(arg)
            return True, args_list
        else:
            for keyword, type_ in word_list:
                arg = request.args.get(keyword, type=type_)
                if arg is None:
                    return False, []
                args_list.append(arg)
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


@app.route('/sys/exit', methods=["POST"])
def exit_() -> dict:
    pass


'''
user
'''


@app.route('/user/login', methods=["POST"])
def login() -> dict:
    b, args_list = extract_args([
        ['account', str],
        ['password', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.login(*args_list))


@app.route('/user/refreshToken', methods=["POST"])
def refresh_token() -> dict:
    return wrap_return_value(True, server.refresh_token())


@app.route('/user/logout', methods=["POST"])
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


@app.route('/environment/setProxyMode', methods=["POST"])
def set_proxy_mode() -> dict:
    b, args_list = extract_args([
        ['mode', int],
        ['address', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_proxy_mode(*args_list))


@app.route('/environment/setTimeout', methods=["POST"])
def set_timeout() -> dict:
    b, args_list = extract_args([
        ['timeout', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_timeout(*args_list))


@app.route('/environment/setConcurrencyNumber', methods=["POST"])
def set_concurrency_number() -> dict:
    b, args_list = extract_args([
        ['number', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_concurrency_number(*args_list))


@app.route('/environment/setIntervalTime', methods=["POST"])
def set_interval_time() -> dict:
    b, args_list = extract_args([
        ['second', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.set_interval_time(*args_list))


@app.route('/environment/setIncrement', methods=["POST"])
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


@app.route('/operation/startTask', methods=["POST"])
def start_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.start_task(*args_list))


@app.route('/operation/stopTask', methods=["POST"])
def stop_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.stop_task(*args_list))


@app.route('/operation/deleteTask', methods=["POST"])
def delete_task() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.delete_task(*args_list))


@app.route('/operation/taskDetail')
def task_details() -> dict:
    b, args_list = extract_args([
        ['tid', int]
    ], False)
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.task_detail(*args_list))


@app.route('/operation/allTaskDetail')
def all_task_details() -> dict:
    return wrap_return_value(True, server.all_task_detail())


'''
create
'''


@app.route('/create/singleWork', methods=["POST"])
def single_work() -> dict:
    b, args_list = extract_args([
        ['keyWord', str],
        ['taskName', str],
        ['savePath', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.single_work(*args_list))


@app.route('/create/userWorks', methods=["POST"])
def user_works() -> dict:
    b, args_list = extract_args([
        ['keyWord', str],
        ['taskName', str],
        ['savePath', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    return wrap_return_value(True, server.user_works(*args_list))


@app.route('/create/workDetails', methods=["POST"])
def work_details() -> dict:
    pass


@app.route('/create/userWorksLink', methods=["POST"])
def user_works_link() -> dict:
    pass


if __name__ == '__main__':
    start()
