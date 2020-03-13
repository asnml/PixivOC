import json
import unittest
from interface import SendType, Command
from structure import SendMsgUnit, AcceptMsgUnit


class Temp:
    pass


class TestMsgUnit(unittest.TestCase):

    def test_send_unit_normal(self):
        unit = SendMsgUnit('S177003', SendType.TaskOver, {'Number': '16'})
        assert unit.effective is True

    def test_send_unit_out_range_send_type(self):
        unit = SendMsgUnit('S177003', 100001, {'Number': '16'})
        assert unit.effective is False

    def test_send_unit_values_type_error(self):
        unit = SendMsgUnit('S177003', '100001', {'Number': '16'})
        assert unit.effective is False

    def test_send_unit_cant_serialized_obj(self):
        unit = SendMsgUnit('S177003', SendType.TaskOver, Temp())
        assert unit.effective is False

    def test_accept_unit_normal(self):
        d = {
            'IdentificationNumber': 'S178320',
            'Command': Command.AllTaskDetails,
            'Account': '',
            'Password': '',
            'ProxyMode': 2,
            'Proxy': '',
            'Timeout': 0,
            'ConcurrencyNumber': 0,
            'IntervalTime': 0,
            'Increment': True,
            'TID': 0,
            'KeyWord': '',
            'TaskName': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is True

    def test_accept_unit_out_range_command(self):
        d = {
            'IdentificationNumber': 'S178320',
            'Command': 10001,
            'KeyWord': '',
            'TaskName': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False

    def test_accept_unit_values_type_error(self):
        d = {
            'IdentificationNumber': 'S178320',
            'Command': '15',
            'KeyWord': '',
            'TaskName': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False

    def test_accept_unit_miss_key(self):
        d = {
            'IdentificationNumber': 'S178320',
            'Command': Command.AllTaskDetails,
            'KeyWord': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False

    def test_accept_unit_identification_number_format_error_1(self):
        d = {
            'IdentificationNumber': '178320',
            'Command': Command.AllTaskDetails,
            'KeyWord': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False

    def test_accept_unit_identification_number_format_error_2(self):
        d = {
            'IdentificationNumber': 'S17d320',
            'Command': Command.AllTaskDetails,
            'KeyWord': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False

    def test_accept_unit_identification_number_format_error_3(self):
        d = {
            'IdentificationNumber': 'T172320',
            'Command': Command.AllTaskDetails,
            'KeyWord': '',
            'SavePath': ''
        }
        b = json.dumps(d).encode()
        unit = AcceptMsgUnit(b)
        assert unit.effective is False


if __name__ == '__main__':
    unittest.main()
