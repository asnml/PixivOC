class Command:
    Login = 1
    Logout = 2
    SetProxyMode = 3
    SetTimeout = 4
    SetConcurrencyNumber = 5
    SetIntervalTime = 6
    SetIncrement = 7

    StartTask = 11
    StopTask = 12
    DeleteTask = 13
    TaskDetails = 14
    AllTaskDetails = 15

    AddWorkDetailsTask = 101
    AddSingleWorkTask = 102
    AddUserWorksLinkTask = 103
    AddUserWorksTask = 104

    @staticmethod
    def list():
        return [
            1, 2, 3, 4, 5,
            11, 12, 13, 14, 15,
            101, 102, 103, 104
        ]


class SendType:
    Reply = 1
    TokenStatusUpdate = 2
    CreateTask = 11
    DeleteTask = 12
    TaskStatusUpdate = 13
    TaskOver = 14
    TaskListUpdate = 15

    @staticmethod
    def list():
        return [
            1, 2, 11, 12, 13, 14, 15
        ]
