from typing import Any
from json import dumps, loads
from datetime import datetime
from json.decoder import JSONDecodeError
from interface import Command, SendType

# Parameter 'Command' and 'SendType' please refer to file interface.py

SignList = ['S', 'R']  # Case-insensitive


def create_identification_number(number: str = None):
    if number is not None:
        return 'R' + number[1:]
    timestamp = int(datetime.now().timestamp())
    return f'S{timestamp}'


RequestFormatStander = {
    'IdentificationNumber': str,
    'Command': int,
    'Account': str,
    'Password': str,
    'ProxyMode': int,
    'Proxy': str,
    'Timeout': int,
    'ConcurrencyNumber': int,
    'IntervalTime': int,
    'Increment': bool,
    'TID': int,
    'KeyWord': str,
    'TaskName': str,
    'SavePath': str
}


ReplyFormatStander = {
    'IdentificationNumber': str,
    'SendType': int,
    'Content': Any  # they muse can be serialized
}


class PreSendUnit:
    def __init__(self, send_type: int, content: Any):
        self.SendType = send_type
        self.content = content


class TaskReportUnit:
    def __init__(self, send_type: int, tid: int, content: Any):
        assert type(tid) is int
        self.SendType = send_type
        self.tid = tid
        self.content = content

    def convert(self):
        return PreSendUnit(
            self.SendType,
            {'TID': self.tid, 'Content': self.content}
        )


class SendMsgUnit:
    def __init__(self, identification_number: str, send_type: int, content: Any):
        self.data = None
        self.effective = True

        try:
            identification_number = identification_number.upper()
            assert type(send_type) is int and send_type in SendType.list()
            dict_ = {'IdentificationNumber': identification_number,
                     'SendType': send_type, 'Content': content}
            string = dumps(dict_)
            self.data = string.encode()
        except AssertionError:
            self.effective = False
        except TypeError:
            self.effective = False


class AcceptMsgUnit:
    def __init__(self, data: bytes):
        self.data = None
        self.effective = True
        self.command = None
        self.IdentificationNumber = None
        try:
            self.data = loads(data.decode())  # type: dict
            assert type(self.data) is dict
            key_list = self.data.keys()
            for key, value in RequestFormatStander.items():
                assert key in key_list and type(self.data[key]) is value
            assert self.data['Command'] in Command.list()
            upper_number = self.data['IdentificationNumber'].upper()  # type: str
            assert upper_number[0] in SignList and upper_number[1:].isdigit()
            self.IdentificationNumber = upper_number
            self.command = self.data['Command']
        except UnicodeDecodeError:
            self.effective = False
        except JSONDecodeError:
            self.effective = False
        except AssertionError:
            self.effective = False
        # if not self.effective:
        #     core_logger.warning('Illegal request.')
        # this statement should be writing in class 'Transport'
