import time
from Download import PROXY_MANAGER
from mobileToken import TokenManager

PROXY = 'http://127.0.0.1:1081'
ACCOUNT = input('Please input account: ')
PASSWORD = input('Please input password: ')


def print_split(fn):
    def wrapper(*args, **kwargs):
        print('\n' + '-' * 80)
        fn(*args, **kwargs)
        print('-' * 80)
    return wrapper


@print_split
def test_load_setting():
    token_manager = TokenManager()
    print(token_manager.msg)


@print_split
def test_login():
    token_manager = TokenManager()
    token_manager.login(ACCOUNT, PASSWORD)
    time.sleep(5)
    print(token_manager.msg)


@print_split
def test_proxy_login():
    PROXY_MANAGER.change_to_proxy(PROXY)
    token_manager = TokenManager()
    print(token_manager.msg)
    token_manager.login(ACCOUNT, PASSWORD)
    time.sleep(5)


@print_split
def test_proxy_refresh():
    PROXY_MANAGER.change_to_proxy(PROXY)
    token_manager = TokenManager()
    print(token_manager.msg)
    time.sleep(5)
    token_manager.refresh_auth_token()
    time.sleep(5)
    print(token_manager.msg)


@print_split
def test_ip_login():
    PROXY_MANAGER.change_to_ip()
    token_manager = TokenManager()
    token_manager.login(ACCOUNT, PASSWORD)
    time.sleep(5)
    print('token after login')
    print(token_manager.msg)


@print_split
def test_ip_refresh():
    PROXY_MANAGER.change_to_ip()
    token_manager = TokenManager()
    print(token_manager.msg)
    time.sleep(5)
    token_manager.refresh_auth_token()
    time.sleep(5)
    print(token_manager.msg)


class TestTaskToken:
    ID = 1

    def __init__(self):
        self.id = TestTaskToken.ID
        TestTaskToken.ID += 1

    def get_token(self, token_manager: TokenManager):
        token_manager.get_token(self.get_token_callback)

    def get_token_callback(self, token):
        print(f'Instance id {self.id}, token: {token}')


@print_split
def test_callback():
    PROXY_MANAGER.change_to_proxy(PROXY)
    token_manager = TokenManager()
    token_manager._AccessTokenUpdateTime = int(time.time()) - 3600

    task_1 = TestTaskToken()
    task_2 = TestTaskToken()
    task_3 = TestTaskToken()
    task_1.get_token(token_manager)
    task_2.get_token(token_manager)
    task_3.get_token(token_manager)

    time.sleep(10)


if __name__ == '__main__':
    # You can do all the tests below at once.
    # test_load_setting()
    # test_login()
    # test_proxy_login()
    # time.sleep(5)
    # test_proxy_refresh()
    test_callback()

    # or
    # test_ip_login()
    # time.sleep(10)
    # test_ip_refresh()
    while True:
        pass
