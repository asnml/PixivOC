import selectors
from socket import socket
from struct import pack, unpack
from multiprocessing import Process, Queue

SELECT_TIMEOUT = 0.1
SERVER_LISTEN_NUMBER = 1
CONNECT_TIMEOUT = 3


class LongLinkServer(Process):
    def __init__(self, send_queue: Queue, accept_queue: Queue, port: int):
        super().__init__()
        assert type(port) is int
        self._Server = socket()
        self._Server.bind(('127.0.0.1', port))
        self._Server.listen(SERVER_LISTEN_NUMBER)
        self._Connect = None
        self._CoreSendQueue = send_queue
        self._CoreAcceptQueue = accept_queue

    def run(self) -> None:
        self.wait_connect()

    def wait_connect(self):
        print('Listen connect.')
        connect, address = self._Server.accept()
        print('Client connect.')
        self._Connect = connect
        return self.communicate(connect)

    def communicate(self, connect: socket):
        while not self._CoreSendQueue.empty():
            self._CoreSendQueue.get()

        selector = selectors.DefaultSelector()
        selector.register(connect, selectors.EVENT_READ)
        try:
            while True:
                events = selector.select(timeout=SELECT_TIMEOUT)
                if events:
                    data = connect.recv(4)
                    if not data:
                        return self.wait_connect()
                    length = unpack('i', data)[0]
                    data = connect.recv(length)
                    content = unpack(f'{length}s', data)[0]
                    self._CoreAcceptQueue.put(content)

                if not self._CoreSendQueue.empty():
                    encoded_msg = self._CoreSendQueue.get()  # type: bytes
                    msg_length = len(encoded_msg)
                    length_pack = pack('i', msg_length)
                    msg_pack = pack(f'{msg_length}s', encoded_msg)
                    connect.send(length_pack)
                    connect.send(msg_pack)
                    print(encoded_msg.decode())
        except BrokenPipeError:
            connect.close()
            return self.wait_connect()
        except ConnectionResetError:
            connect.close()
            return self.wait_connect()


if __name__ == '__main__':
    import time
    from threading import Thread

    def add_item(queue: Queue):
        time.sleep(8)
        queue.put('Transport send item')

    SendQueue = Queue()
    add_thread = Thread(target=add_item, args=(SendQueue,))
    add_thread.daemon = True
    add_thread.start()

    Server = LongLinkServer(Queue(), SendQueue, 13575)
    Server.wait_connect()
