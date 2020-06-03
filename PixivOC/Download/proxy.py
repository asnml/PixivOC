from random import choice
from re import compile, sub
from .domain import DOMAIN_RESOLVE
from .structure import RequestPackage
from .log import downloader_logger


class ProxyState:
    Direct = 0
    Proxy = 1
    IP = 2


class ProxyManager:
    ProxyPattern = compile(r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+')

    def __init__(self):
        self._State = ProxyState.Direct
        self._Proxy = None
        downloader_logger.info('Create ProxyManager instance.')

    def change_to_direct(self) -> bool:
        self._State = ProxyState.Direct
        self._Proxy = None
        downloader_logger.info('Change connection mode to direct.')
        return True

    def change_to_proxy(self, proxy: str) -> bool:
        try:
            assert type(proxy) is str
        except AssertionError:
            return False
        if len(ProxyManager.ProxyPattern.findall(proxy)) != 1:
            return False
        self._State = ProxyState.Proxy
        self._Proxy = proxy
        downloader_logger.info('Change connection mode to proxy.')
        return True

    def change_to_ip(self) -> bool:
        self._State = ProxyState.IP
        self._Proxy = None
        downloader_logger.info('Change connection mode to ip.')
        return True

    def convert(self, package: RequestPackage) -> RequestPackage:
        if self._State == ProxyState.Direct:
            return package
        if self._State == ProxyState.Proxy:
            package.proxy = self._Proxy
            return package
        if self._State == ProxyState.IP:
            return self._convert_domain(package)

    @staticmethod
    def _convert_domain(package: RequestPackage) -> RequestPackage:
        pattern = compile(r'https?://(?P<domain>[^/]+)/.*')
        match = pattern.match(package.url)
        domain = match.groupdict('domain')['domain']
        ip_address = choice(DOMAIN_RESOLVE[domain])  # 可以优化为使用延迟最小的IP地址
        new_url = sub(domain, ip_address, package.url)
        package.url = new_url
        package.headers['Host'] = domain  # very important
        package.headers['SNI-Host'] = domain
        return package

    def get_setting(self):
        status, address = '', ''
        if self._State == 0:
            status = 'Direct'
        if self._State == 1:
            status = 'Proxy'
            address = self._Proxy
        if self._State == 2:
            status = 'IP'
        return status, address


def test_server_latency():
    # https://stackoverflow.com/questions/2953462/pinging-servers-in-python
    # https://stackoverflow.com/questions/2525312/measuring-ping-latency-of-a-server-python
    pass
