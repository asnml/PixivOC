from main import TaskManager, EnvironmentSetting, Queue


def main():
    EnvironmentSetting.set_proxy_mode(2)
    task_manager = TaskManager(Queue())
    msg = task_manager.all_task_details()
    print(msg)


if __name__ == '__main__':
    main()
