import time
from main import TaskManager, EnvironmentSetting, Queue, UserWorksTask


def dump():
    task_manager = TaskManager(Queue())
    task_manager.add_single_keyword_task(
        '26323136', 'TestLoadAndDump1', '.',
        True, False, UserWorksTask
    )
    task_manager._dump_tasks()
    time.sleep(1)


def load_and_details():
    EnvironmentSetting.set_proxy_mode(2)
    task_manager = TaskManager(Queue())
    task_manager.add_single_keyword_task(
        '28145748', 'TestLoadAndDump2', 'PictureSave',
        True, False, UserWorksTask
    )
    for msg in task_manager.all_task_details():
        print(msg)


def main():
    dump()
    load_and_details()


if __name__ == '__main__':
    main()
