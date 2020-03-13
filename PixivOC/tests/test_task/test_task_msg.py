from taskTypes import *


unit_1 = StorageUnit(1, '测试', 1, 2, [1, 2, 3, 4, 5], ['a', 'b', 'c', 'd'], 'PictureSave/19/')
task = UserWorksTask(unit_1, lambda x: x)
print(task.msg)
