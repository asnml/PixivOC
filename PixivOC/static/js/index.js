const tbody = $('tbody')
const polite = $('#polite')


// environment parameter
var login_status = false;
var proxy = null;
var proxy_address = null;
var timeout = null;
var async = null;
var sync = null;


// set toast default parameter
$('.toast').toast({ delay: 5000, autohide: false })


// set timer
const update_task_time = 1000 * 2
const update_environment_time = 1000 * 60
var atd_;
var ls_;
var es_;


// set click event
$("#close_software").on('click', close_software)
$("#console_submit").on('click', set_permission)
$("#login_submit").on('click', login)
$("#param_submit").on('click', set_environment)
$("#task_submit").on('click', create_task)
tbody.on('click', '.btn_start', btn_start)
tbody.on('click', '.btn_stop', btn_stop)
tbody.on('click', '.btn_delete', btn_delete)


// set modal init event
$('#parameterModal').on('show.bs.modal', function(event) {
    var btn_id = $(event.relatedTarget).attr('id')
    var modal = $(this)
    var show_ = modal.find('p')
    show_.text(btn_id.split("_").join(" "))
    var proxy_div = modal.find('#param_proxy')
    var int_div = modal.find('#param_int')
    if (btn_id == 'set_proxy') {
        proxy_div.css('display', 'block')
        int_div.css('display', 'none')
    } else {
        proxy_div.css('display', 'none')
        int_div.css('display', 'block')
        var input_ = int_div.find('input')
        var text_ = "now: "
        switch (btn_id) {
            case "set_timeout":
                text_ += timeout
                break;
            case "set_async":
                text_ += async
                break;
            case "set_sync":
                text_ += sync
        }
        input_.attr('placeholder', text_)
    }
})


$('#taskModal').on('show.bs.modal', function(event) {
    var btn_id = $(event.relatedTarget).attr('id')
    var modal = $(this)
    modal.find('p').text(btn_id.split("_").join(" "))
})


$('#detailModal').on('show.bs.modal', function(event) {
    var button = $(event.relatedTarget)
    var tid = button.closest('tr').data('tid')
    var msg = get_task_msg(parseInt(tid))
    var modal = $(this)
    if (msg != null) {
        modal.find('#detail_msg0').text("TID: " + msg[0])
        modal.find('#detail_msg1').text("TaskName: " + msg[1])
        modal.find('#detail_msg2').text("TypeName: " + msg[2])
        modal.find('#detail_msg3').text("SavePath: " + msg[3])
        modal.find('#detail_msg4').text("StageName: " + msg[4])
        modal.find('#detail_msg5').text("State: " + msg[5])
        modal.find('#detail_msg6').text("Less: " + msg[6])
    }
})


// init
check_permission()


// function area


function close_software() {
    var url = "/sys/exit"
    $.post(url, function(response) {
        var status = response['status']
        if (status) {
            clearInterval(atd_)
            clearInterval(ls_)
            clearInterval(es_)
            $("#exitModal").modal('show')
        }
    })
}


function check_permission() {
    var url = "/permission/hasPermission"
    $.get(url, function(response) {
        var resp = response['result']
        if (resp) {
            set_interval()
        } else {
            $("#consoleModal").modal('show')
        }
    })
}


function set_interval() {
    atd_ = setInterval(update_all_task_detail, update_task_time)
    ls_ = setInterval(update_login_status, update_environment_time)
    es_ = setInterval(update_environment_setting, update_environment_time)
    update_all_task_detail()
    update_login_status()
    update_environment_setting()
}


function set_permission() {
    var url = "/permission/login"
    var password = $("#console_input").val()
    if (password == "") {
        return alert('Please input console password')
    }
    $.post(url, { 'password': password }, function(response) {
        var status = response['status']
        var resp = response['result']
        if (status == true && resp == true) {
            $("#consoleModal").modal('hide')
            set_interval()
        } else {
            alert("Password error")
        }
    })

}


function login() {
    // use rgex check input
    var url = "/user/login"
    var modal_body = $(this).closest('div').siblings('.modal-body')
    var account = modal_body.find('#account_input').find('input').val()
    var password = modal_body.find('#password_input').find('input').val()
    send_alert("send login request", "primary")
    $.post(url, { "account": account, "password": password }, function(response) {
        var status = response['status']
        var resp = response['result']
        if (status == true && resp == true) {
            send_alert("server accept loging request and call login function", "success")
        } else {
            send_alert("missing parameters or maybe server cannot accept the request", "warning")
        }
    }, "json")
}


function set_environment() {
    // use rgex check input
    var modal_body = $(this).closest('div').siblings('.modal-body')
    var type_ = modal_body.find('p').text()
    if (type_ == "set proxy") {
        var url = "/environment/setProxyMode"
        var mode = modal_body.find("#inputGroupSelect01").val() // 1, 2, 3
        var address = "";
        if (mode == 2) {
            address = modal_body.find("#param_address_input").find("input").val()
        }
        send_alert("send request of set environment", "primary")
        $.post(url, { 'mode': mode - 1, 'address': address }, function(response) {
            var status = response['status']
            var resp = response['result']
            if (status == true && resp == true) {
                send_alert("successfully set environment parameter", "success")
            } else {
                send_alert("failed to set environment parameter\nparameter error or maybe server cannot accept the request", "warning")
            }
            update_environment_setting()
        }, "json")
    } else {
        var value = modal_body.find("#param_int_input").find("input").val()
        var int_value = parseInt(value).toString()
        if (int_value == "NaN") {
            return
        }
        var url
        var dict_
        switch (type_) {
            case "set timeout":
                url = "/environment/setTimeout"
                dict_ = { "timeout": int_value }
                break;
            case "set async":
                url = "/environment/setConcurrencyNumber"
                dict_ = { "number": int_value }
                break;
            case "set sync":
                url = "/environment/setIntervalTime"
                dict_ = { "second": int_value }
        }
        send_alert("send request of set environment", "primary")
        $.post(url, dict_, function(response) {
            var status = response['status']
            var resp = response['result']
            if (status == true && resp == true) {
                send_alert("successfully set environment parameter", "success")
            } else {
                send_alert("failed to set environment parameter\n parameter type error or maybe server cannot accept the request", "warning")
            }
            update_environment_setting()
        }, "json")
    }
}


function create_task() {
    var modal_body = $(this).closest('div').siblings('.modal-body')
    var type_ = modal_body.find('p').text()
    var task_name = modal_body.find("#taskname_input").find("input").val()
    var key_word = modal_body.find("#keyword_input").find("input").val()
    var save_path = modal_body.find("#savepath_input").find("input").val()
    send_alert("send request of create task", "primary")
    var url;
    if (type_ == "single work") {
        url = "/create/singleWork"
    }
    if (type_ == "user works") {
        url = "/create/userWorks"
    }
    $.post(url, { "keyWord": key_word, "taskName": task_name, "savePath": save_path }, function(response) {
        var status = response['status']
        var resp = response['result'][0]
        if (status == true && resp == true) {
            send_alert("successfully create task", "success")
        } else {
            send_alert("failed to create task\nplease check save path and parameters or maybe server cannot accept the request", "warning")
        }
        update_all_task_detail()
    })
}


function btn_start() {
    var url = "/operation/startTask"
    var tid = $(this).closest('tr').data('tid')
    $.post(url, { "tid": tid }, function(response) {
        var status = response['status']
        var resp = response['result'][0]
        if (status == true && resp == true) {
            send_alert("successfully start task", "success")
        } else {
            send_alert("failed to start task, please check has login", "warning")
        }
        update_all_task_detail()
    })
}


function btn_stop() {
    var url = "/operation/stopTask"
    var tid = $(this).closest('tr').data('tid')
    $.post(url, { "tid": tid }, function(response) {
        var status = response['status']
        var resp = response['result'][0]
        if (status == true && resp == true) {
            send_alert("successfully stop task", "success")
        } else {
            send_alert("failed to stop task, please check has login", "warning")
        }
        update_all_task_detail()
    })
}


function btn_delete() {
    var tid = $(this).closest('tr').data('tid')
    $(this).closest('tr').remove()
    delete_task(tid)
    var url = '/operation/deleteTask'
    $.post(url, { 'tid': tid }, function() {
        update_all_task_detail()
    })
}


const button_group = `
<td>
    <div class="btn-group btn-group-sm" role="group" aria-label="Basic example">
        <button type="button" class="btn btn-light btn_start">
            <span class="icon-start"></span>
        </button>
        <button type="button" class="btn btn-light btn_stop">
            <span class="icon-stop"></span>
        </button>
        <button type="button" class="btn btn-light btn_detail" data-toggle="modal" data-target="#detailModal">
            <span class="icon-detail"></span>
        </button>
        <button type="button" class="btn btn-light btn_delete">
            <span class="icon-delete"></span>
        </button>
    </div>
</td>
`


function generate_string_of_row(string_list) {
    // string_list: group of table head.
    result = ""
    result += `<tr data-tid="` + string_list[0] + `">`
    for (var i = 1; i < string_list.length; i++) {
        result += "<td>" + string_list[i] + "</td>"
    }
    result += button_group
    result += "</tr>"
    return result
}


function generate_update_string(string_list) {
    // string_list: group of table head.
    result = ""
    for (var i = 1; i < string_list.length; i++) {
        result += "<td>" + string_list[i] + "</td>"
    }
    result += button_group
    return result
}


function add_row(string_list) {
    // string_list: group of table head.
    var row_string = generate_string_of_row(string_list)
    tbody.append(row_string)
}


function update_table() {
    var tr_dict = {}
    tbody.children().each(function(index, tr) {
        tr_dict[$(tr).data('tid')] = tr // tr is dom object
    })
    var msg_list = all_task_msg()
    msg_list.forEach(msg => {
        if (msg[0] in tr_dict) {
            var tr = tr_dict[msg[0]]
            tr.innerHTML = generate_update_string(msg)
        } else {
            add_row(msg)
        }
    })
}


function update_all_task_detail() {
    var url = "/operation/allTaskDetail"
    $.get(url, function(result) {
        // var tid_list = Array()
        // for (var task_msg of result['result']){
        //     tid_list.push(task_msg[1])
        // }
        // var difference_list = difference_task(tid_list)
        // for (var tid of difference_list){
        //     $("tr [data-tid='1597153292']").remove()
        // }
        for (var task_msg of result['result']) {
            var task = find_task(task_msg[1])
            if (task == null) {
                add_task(createTask(
                    task_msg[0], task_msg[1], task_msg[2], task_msg[3],
                    task_msg[4], task_msg[5], task_msg[6], task_msg[7]
                ))
            } else {
                update_task_msg(
                    task,
                    task_msg[0], task_msg[1], task_msg[2], task_msg[3],
                    task_msg[4], task_msg[5], task_msg[6], task_msg[7]
                )
            }
        }
        update_table()
    }, "json")
}


function update_login_status() {
    var url = "/user/hasLogin"
    $.get(url, function(result) {
        login_status = result['result']
        $("#login_status").text("Login status: " + login_status)
    }, "json")
}


function update_environment_setting() {
    var url = "/environment/getEnvironment"
    $.get(url, function(result) {
        var resp = result['result']
        proxy = resp[0]
        proxy_address = resp[1]
        timeout = resp[2]
        async = resp[3]
        sync = resp[4]

        if (proxy_address == "") {
            $("#proxy_status").text("Proxy status: " + proxy)
        } else {
            var text = "Proxy status: " + proxy + " - Proxy address: " + proxy_address
            $("#proxy_status").text(text)
        }
    }, "json")
}


const alert_string = `
<button type="button" class="close" data-dismiss="alert">
    <span aria-hidden="true">&times;</span>
</button>
</div>
`


function send_alert(msg, level) {
    if (level == "primary" || level == "success" || level == "warning" || level == "danger") {
        var add = ""
        add += `<div class="alert alert-` + level + ` alert-dismissible fade show" role="alert">`
        add += msg
        add += alert_string
        polite.append(add)
    } else {
        var add = ""
        add += `<div class="alert alert-danger alert-dismissible fade show" role="alert">`
        add += "Missing or using wrong parameters when calling function 'send_alert'"
        add += alert_string
        polite.append(add)
    }
}