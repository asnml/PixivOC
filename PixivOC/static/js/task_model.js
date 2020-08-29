var _task_dict = {}

function createTask(over, tid, task_name, type_name, save_path, stage_name, state, less) {
    var task = new Object
    task.Over = over // bool
    task.Tid = tid // int
    task.TaskName = task_name // str
    task.TypeName = type_name // str
    task.SavePath = save_path // str
    task.StageName = stage_name // str
    task.State = state // str
    task.Less = less // int
    return task
}

function update_task_msg(task, over, tid, task_name, type_name, save_path, stage_name, state, less) {
    task.Over = over // bool
    task.Tid = tid // int
    task.TaskName = task_name // str
    task.TypeName = type_name // str
    task.SavePath = save_path // str
    task.StageName = stage_name // str
    task.State = state // str
    task.Less = less // int
}

function task_msg(task) {
    var string_list = Array()
    string_list.push(task.Tid)
    string_list.push(task.TaskName)
    string_list.push(task.TypeName)
    string_list.push(task.SavePath)
    string_list.push(task.StageName)
    string_list.push(task.State)
    string_list.push(task.Less)
    return string_list
}

function add_task(task) {
    _task_dict[task.Tid] = task
}

function delete_task(tid) {
    var tid_ = parseInt(tid)
    if (tid_.toString() == "NaN") {
        return null;
    }
    var flag = false;
    for (var key of Object.keys(_task_dict)) {
        if (key == tid_) {
            flag = true;
            break
        }
    }
    if (flag) {
        delete _task_dict[tid_]
    } else {
        return null;
    }
}

function difference_task(tid_list) {
    var difference_list = Array()
    for (var key of Object.keys(_task_dict)) {
        var flag = true
        for (var tid of tid_list) {
            if (tid == key) {
                flag = false
                break
            }
        }
        if (flag) {
            difference_list.push(key)
        }
    }
    return difference_list
}

function find_task(tid) {
    return _task_dict[tid]
}

function get_task_msg(tid) {
    var task = find_task(tid)
    if (task != null) {
        return task_msg(task)
    } else {
        return null
    }
}

function all_task_msg() {
    var msg = Array()
    for (var key of Object.keys(_task_dict)) {
        msg.push(task_msg(_task_dict[key]))
    }
    return msg
}