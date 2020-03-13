# async
import asyncio
from aiohttp import TCPConnector, ClientConnectorError, ClientTimeout
from aiohttp.tracing import Trace
from aiohttp.connector import is_ip_address, ClientRequest, \
    EventResultOrError, ServerFingerprintMismatch, ResponseHandler
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
)
from _socket import AF_INET, AI_NUMERICHOST


# sync
from requests import adapters


class AsyncSniConnector(TCPConnector):
    """
    Add attribute "SNI-Host" to the request headers to modify
    the server name in certificate verification.
    """
    async def _create_direct_connection(
            self,
            req: 'ClientRequest',
            traces: List['Trace'],
            timeout: 'ClientTimeout',
            *,
            client_error: Type[Exception] = ClientConnectorError
    ) -> Tuple[asyncio.Transport, ResponseHandler]:
        sslcontext = self._get_ssl_context(req)
        fingerprint = self._get_fingerprint(req)

        try:
            # Cancelling this lookup should not cancel the underlying lookup
            #  or else the cancel event will get broadcast to all the waiters
            #  across all connections.
            host = req.url.raw_host
            assert host is not None
            port = req.port
            assert port is not None

            headers = req.headers
            sni_host = None
            for head, value in headers.items():
                if head.lower() == 'sni-host':
                    sni_host = headers[head]

            hosts = await asyncio.shield(self._resolve_host(
                host,
                port,
                sni_host,
                traces=traces), loop=self._loop)
        except OSError as exc:
            # in case of proxy it is not ClientProxyConnectionError
            # it is problem of resolving proxy ip itself
            raise ClientConnectorError(req.connection_key, exc) from exc

        last_exc = None  # type: Optional[Exception]

        for hinfo in hosts:
            host = hinfo['host']
            port = hinfo['port']

            try:
                transp, proto = await self._wrap_create_connection(
                    self._factory, host, port, timeout=timeout,
                    ssl=sslcontext, family=hinfo['family'],
                    proto=hinfo['proto'], flags=hinfo['flags'],
                    server_hostname=hinfo['hostname'] if sslcontext else None,
                    local_addr=self._local_addr,
                    req=req, client_error=client_error)
            except ClientConnectorError as exc:
                last_exc = exc
                continue

            if req.is_ssl() and fingerprint:
                try:
                    fingerprint.check(transp)
                except ServerFingerprintMismatch as exc:
                    transp.close()
                    if not self._cleanup_closed_disabled:
                        self._cleanup_closed_transports.append(transp)
                    last_exc = exc
                    continue

            return transp, proto
        else:
            assert last_exc is not None
            raise last_exc

    async def _resolve_host(self,
                            host: str, port: int, sni_host: str = None,
                            traces: Optional[List['Trace']] = None
                            ) -> List[Dict[str, Any]]:
        if is_ip_address(host):

            if sni_host is not None:
                # return [{'hostname': sni_host, 'host': host, 'port': port,
                #          'family': AF_INET, 'proto': 0, 'flags': AI_NUMERICHOST}]
                return [{'hostname': sni_host, 'host': host, 'port': port,
                         'family': self._family, 'proto': 0, 'flags': 0}]

            return [{'hostname': host, 'host': host, 'port': port,
                     'family': self._family, 'proto': 0, 'flags': 0}]

        if not self._use_dns_cache:

            if traces:
                for trace in traces:
                    await trace.send_dns_resolvehost_start(host)

            res = (await self._resolver.resolve(
                host, port, family=self._family))

            if traces:
                for trace in traces:
                    await trace.send_dns_resolvehost_end(host)

            return res

        key = (host, port)

        if (key in self._cached_hosts) and \
                (not self._cached_hosts.expired(key)):

            if traces:
                for trace in traces:
                    await trace.send_dns_cache_hit(host)

            return self._cached_hosts.next_addrs(key)

        if key in self._throttle_dns_events:
            if traces:
                for trace in traces:
                    await trace.send_dns_cache_hit(host)
            await self._throttle_dns_events[key].wait()
        else:
            if traces:
                for trace in traces:
                    await trace.send_dns_cache_miss(host)
            self._throttle_dns_events[key] = \
                EventResultOrError(self._loop)
            try:

                if traces:
                    for trace in traces:
                        await trace.send_dns_resolvehost_start(host)

                addrs = await \
                    self._resolver.resolve(host, port, family=self._family)
                if traces:
                    for trace in traces:
                        await trace.send_dns_resolvehost_end(host)

                self._cached_hosts.add(key, addrs)
                self._throttle_dns_events[key].set()
            except BaseException as e:
                # any DNS exception, independently of the implementation
                # is set for the waiters to raise the same exception.
                self._throttle_dns_events[key].set(exc=e)
                raise
            finally:
                self._throttle_dns_events.pop(key)

        return self._cached_hosts.next_addrs(key)


class SyncSniConnector(adapters.HTTPAdapter):
    """
    Reference: https://github.com/requests/toolbelt/pull/157
    """
    def send(self, request, **kwargs):
        host_header = None
        for header in request.headers:
            if header.lower() == "sni-host":
                host_header = request.headers[header]
                del request.headers[header]
                break

        connection_pool_kwargs = self.poolmanager.connection_pool_kw

        if host_header:
            connection_pool_kwargs["assert_hostname"] = host_header
        elif "assert_hostname" in connection_pool_kwargs:
            connection_pool_kwargs.pop("assert_hostname", None)

        return super().send(request, **kwargs)
