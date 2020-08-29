import json
from os import listdir, _exit
from typing import Any
from time import sleep
from threading import Thread
from datetime import timedelta
from flask import Flask, request, session, redirect
from controller import Check, Server, core_logger

OptionsFileName = "Options.json"

ServerPort = 13575
SecretKey = "Any string, the more complex the better"
ConsolePassword = "Hello world"

AcceptRequest = True


def load_web_setting():
    global ServerPort, SecretKey, ConsolePassword
    if OptionsFileName not in listdir('.'):
        with open(OptionsFileName, 'w', encoding='utf-8') as file:
            json.dump({
                'ServerPort': ServerPort,
                'SecretKey': SecretKey,
                'ConsolePassword': ConsolePassword
            }, file)
    else:
        with open(OptionsFileName, encoding='utf-8') as file:
            data = json.load(file)
            ServerPort = data['ServerPort']
            SecretKey = data['SecretKey']
            ConsolePassword = data['ConsolePassword']


Check.assert_task_cls_meet_specifications()
server = Server()
load_web_setting()
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = SecretKey
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)


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


@app.errorhandler(404)
def catch_404(error):
    print(error)  # Just to eliminate code reminders
    return "Page not found"


@app.errorhandler(Exception)
def catch_unknown_exception(error):
    core_logger.exception(error)
    return wrap_return_value(False, "An unknown exception occurred on the server.")


@app.before_request
def permission_check():
    if request.endpoint == 'set_permission' or request.endpoint == 'has_permission'\
            or request.endpoint == 'static':
        pass
    else:
        if session.get('login') is None:
            return wrap_return_value(False, "You don't have permission to access the link.")
        else:
            if AcceptRequest is False:
                return wrap_return_value(False, "Server has closed.")


'''
permission
'''


@app.route('/permission/login', methods=["POST"])
def set_permission() -> dict:
    b, args_list = extract_args([
        ['password', str]
    ])
    if b is False:
        return wrap_return_value(False, None)
    if ConsolePassword != args_list[0]:
        return wrap_return_value(True, False)
    session.permanent = True
    session['login'] = True
    return wrap_return_value(True, True)


@app.route('/permission/hasPermission')
def has_permission() -> dict:
    return wrap_return_value(True, False if session.get('login') is None else True)


'''
site
'''


@app.route('/')
def font_page():
    return "Hello :)"


@app.route('/favicon.ico')
def fav():
    return redirect('/static/favicon.ico')


'''
sys
'''


def real_exit_func():
    sleep(5)  # make sure return response
    server.exit()
    core_logger.info("Close software.")
    _exit(0)


@app.route('/sys/exit', methods=["POST"])
def exit_() -> dict:
    global AcceptRequest
    AcceptRequest = False
    child_thread = Thread(target=real_exit_func)
    child_thread.start()
    return wrap_return_value(True, True)


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
