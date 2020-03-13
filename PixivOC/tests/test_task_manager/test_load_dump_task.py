import time
from main import TaskManager, EnvironmentSetting, Queue


def dump():
    task_manager = TaskManager(Queue())
    task_manager.add_user_works_task('26323136', 'TestLoadAndDump1', 'PictureSave')
    task_manager._dump_tasks()
    time.sleep(1)


def load_and_details():
    EnvironmentSetting.set_proxy_mode(2)
    task_manager = TaskManager(Queue())
    task_manager._load_tasks()
    task_manager.add_user_works_task('28145748', 'TestLoadAndDump2', 'PictureSave')
    for msg in task_manager.all_task_details():
        print(msg)


def main():
    dump()
    load_and_details()


if __name__ == '__main__':
    main()
