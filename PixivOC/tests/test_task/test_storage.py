from task import *
from Download import PROXY_MANAGER
from taskTypes import UserWorksStage1

RUNNING = True
# TestPrePage = 5


class TestUserWorksStorage(BaseTask):
    def _create_stage(self) -> BaseTaskStage:
        if self._CurrentStage == 1:
            return UserWorksStage1(self._ParamsList, self._Data,
                                   self._stage_complete_callback, self._progress_update)
        self._task_over()

    def _return_value(self) -> Any:
        return ''


def disguise_sent_to_server(msg_unit: TaskReportUnit):
    print(msg_unit.content)
    global RUNNING
    RUNNING = False


if __name__ == '__main__':
    PROXY_MANAGER.change_to_ip()
    STORAGE = StorageUnit(1, 'TestStorage', 1, 1, [28145748], [], '.')
    TASK = TestUserWorksStorage(STORAGE, disguise_sent_to_server)
    TASK.start()
    while RUNNING:
        pass
    NEW_STORAGE = TASK.export_storage()
    print('TID: ', NEW_STORAGE.TID)
    print('TaskName: ', NEW_STORAGE.TaskName)
    print('TaskType: ', NEW_STORAGE.TaskType)
    print('CurrentStage: ', NEW_STORAGE.CurrentStage)
    print('ParamsList: ', NEW_STORAGE.ParamsList)
    print('Data: ', NEW_STORAGE.Data)
    print('SavePath: ', NEW_STORAGE.SavePath)
