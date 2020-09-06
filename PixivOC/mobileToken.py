# coding = utf-8

# System
from os import listdir
from hashlib import md5
from datetime import datetime
from json import dump, load, loads
from typing import Callable

# Network
from asyncio import Future
from Download import DownloadThread, RequestPackage, ResultPackage
from log import core_logger


class OperationFailedException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


AccessTokenUpdateExpiration = 60 * 60 * 24 * 30  # unit: second


class TokenManager:
    instance = None
    init = True

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self, refresh_token: str = None):
        if not self.init:
            return
        self.init = False

        # build params
        self._ClientID = 'MOBrBDS8blbauoSck0ZfDbtuzpyT'
        self._ClientSecret = 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj'
        self._LoginHash = '28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c'

        # token
        self._AccessToken = None
        self._RefreshToken = refresh_token
        self._AccessTokenUpdateTime = 0

        # network
        self._DownloadThread = None

        # operating mechanism
        self._Refreshing = False
        self._SendTokenList = []
        self._SendQueue = None

        self._load_setting()
        core_logger.info('Create TokenManager instance.')

    def _load_setting(self):
        # Pay attention to the real search path
        # Search path is running file path, not module path.
        if 'Token.json' in listdir('.'):
            with open('Token.json') as file:
                data = load(file)
                self._AccessToken = data['AccessToken']
                self._RefreshToken = data['RefreshToken']
                self._AccessTokenUpdateTime = data['AccessTokenUpdateTime']
            core_logger.info('Find token file, loading.')
            now_timestamp = int(datetime.now().timestamp())
            if now_timestamp - self._AccessTokenUpdateTime >= AccessTokenUpdateExpiration:
                self._AccessToken = None
                self._RefreshToken = None
                self._AccessTokenUpdateTime = 0
                core_logger.info('According to the last update date '
                                'more than 30 days, the data is cleared')
        else:
            core_logger.info('Not find token file.')

    def set_refresh_token(self, refresh_token):
        self._RefreshToken = refresh_token
        core_logger.debug('Call function set_refresh_token.')

    @property
    def msg(self) -> str:
        if self._RefreshToken is None:
            return "You haven't logged in yet."
        update_time = datetime.fromtimestamp(self._AccessTokenUpdateTime).strftime('%Y-%m-%d %H:%M:%S')
        return f"AccessToken: {self._AccessToken}\n" \
               f"RefreshToken: {self._RefreshToken}\n" \
               f"AccessTokenUpdateTime: {update_time}"

    @property
    def has_refresh_token(self):
        if self._RefreshToken is None:
            return False
        else:
            return True

    def get_token(self, instance_callback: Callable[[str], None]) -> str:
        if int(datetime.now().timestamp()) - self._AccessTokenUpdateTime < 45 * 60:
            return self._AccessToken
        else:
            if not self._Refreshing:
                self.refresh_auth_token()
                self._Refreshing = True
            self._SendTokenList.append(instance_callback)
            return ''

    def login(self, username: str, password: str) -> bool:
        core_logger.info('Login account.')
        return self.refresh_auth_token(username=username, password=password)

    def refresh_auth_token(self, username: str = None, password: str = None, refresh_token: str = None) -> bool:

        url = 'https://oauth.secure.pixiv.net/auth/token'
        now = datetime.now()
        x_client_time = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        x_client_hash = md5((x_client_time + self._LoginHash).encode()).hexdigest()
        headers = {
            'User-Agent': 'PixivAndroidApp/5.0.64 (Android 6.0)',
            'x-client-time': x_client_time,
            'x-client-hash': x_client_hash
        }
        data = {
            'get_secure_url': 1,
            'client_id': self._ClientID,
            'client_secret': self._ClientSecret,
        }

        if username is not None and password is not None:
            data['grant_type'] = 'password'
            data['username'] = username
            data['password'] = password
        elif refresh_token is not None or self._RefreshToken is not None:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = refresh_token or self._RefreshToken
        else:
            raise Exception('Refresh token, but not contain username and password or contain refresh token.')

        request_package = RequestPackage(url, 'POST', headers, data=data)
        self._DownloadThread = DownloadThread(self._child_fetch_callback, sync=True)
        self._DownloadThread.start(lambda future: print(end=''), [request_package])
        return True
        # must be sync downloader
        # use async download will raise ConnectionResetError exception.
        # i don't know hwo to fixed it.

    def _child_fetch_callback(self, future: Future):
        result = future.result()  # type: ResultPackage
        if result.exception is None:
            return self._extract_token(result.result.decode())
        else:
            core_logger.warning('Request refresh token failed, please check internet connection.')
            self._Refreshing = False
            while self._SendTokenList:
                callback = self._SendTokenList.pop()
                callback("Internet connection exception")

    def _extract_token(self, resp: str):
        try:
            resp = loads(resp)  # type: dict
            if resp.get('response', None) is not None:
                self._AccessToken = resp['response']['access_token']
                self._RefreshToken = resp['response']['refresh_token']
                self._AccessTokenUpdateTime = int(datetime.now().timestamp())
                # self._UserID = resp['user']['id']  # maybe will use it when multiple tokens
                core_logger.debug('Refresh token.')
            else:
                raise OperationFailedException('Operation failed, '
                                               'please check username and password and refresh token.')
        except OperationFailedException:
            core_logger.warning('Operation failed, please check username and password and refresh token.')
        except KeyError:
            # 该异常未被捕捉，异常级别应为 CRITICAL，应组织程序有序的退出
            core_logger.critical('Extract access_token error!', exc_info=True)
            raise KeyError
        return self._write_token()

    def _write_token(self):
        with open('Token.json', 'w', encoding='utf-8') as file:
            dump({
                'AccessToken': self._AccessToken,
                'RefreshToken': self._RefreshToken,
                'AccessTokenUpdateTime': self._AccessTokenUpdateTime
            }, file)

        self._Refreshing = False
        self._send_token()

    def _send_token(self):
        """
        This function will definitely end
        because the callback functions are all functions that
        create a download thread and start it
        :return:
        """
        while self._SendTokenList:
            callback = self._SendTokenList.pop()
            callback(self._AccessToken)
            # because type of self._AccessToken is str,
            # so don't worry about its value being changed by the function.


TOKEN_MANAGER = TokenManager()
