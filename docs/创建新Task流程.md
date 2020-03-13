#### 创建新 Task 类型流程

1. 在 `api.py` 文件里面添加新 `Task` 所需的 `API` 类。
2. 在 `taskTypes.py` 文件里面添加新的 `Task` 以及其 `Stage` 类，然后将 `Task` 类名添加到在文件底端的 `TaskTypeList` 列表。
3. 在 `interface.py` 文件里面添加命令参数。
4. 在 `main.py` 中导入类，~~在 `TaskManager` 类里面添加实例化函数~~，在 `Server` 类的 `reply` 函数中添加实例化语句。
5. 更新 `TaskOver` 返回值文档。