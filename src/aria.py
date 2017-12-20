# -*- coding: utf-8 -*-
import os
import socket
import sys
import xmlrpclib
from aria_actions import speed_convert
from workflow import Workflow3
from workflow.background import run_in_background, is_running


def get_rpc():
    global server
    rpc_path = wf.settings['rpc_path']
    server = xmlrpclib.ServerProxy(rpc_path).aria2
    try:
        version = server.getVersion(secret)
    except (xmlrpclib.Fault, socket.error):
        current_secret = secret.split(':')[1]
        wf.add_item(u'Aria2 may not be running, try starting it?', u'Press Enter',
                arg=u'--run-aria2', valid=True)
        wf.add_item(u'Or change RPC path?', u'Currently using ' + rpc_path,
                arg=u'--go-rpc-setting', valid=True)
        wf.add_item(u'Or change RPC secret?', u'Currently using \'' + current_secret + '\'',
                arg=u'--go-secret-setting', valid=True)
        return False
    else:
        return True


def size_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti']:
        if abs(num) < 1024.0:
            return '{num:.2f} {unit}{suffix}'.format(num=num, unit=unit, suffix=suffix)
        num /= 1024.0
    return '{num:.1f} {unit}{suffix}'.format(num=num, unit='Pi', suffix=suffix)


def time_fmt(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    w, d = divmod(d, 7)
    y, w = divmod(w, 52)
    units = ['y', 'w', 'd', 'h', 'm', 's']
    parts = [str(eval(unit)) + str(unit) for unit in units if eval(unit) > 0]
    time = ''.join(parts)
    return time


def apply_filter(tasks, filters):
    if filters:
        for filter in filters:
            tasks = wf.filter(filter, tasks,
                    lambda task: get_task_name(task), min_score=20)
    return tasks


def kill_notifier():
    if os.path.isfile(wf.cachefile('notifier.pid')):
        with open(wf.cachefile('notifier.pid'), 'r') as pid_file:
            pid = pid_file.readline()
        os_command = 'pkill -TERM -P ' + pid
        os.system(os_command)


def get_task_name(task):
    gid = task['gid']
    bt = server.tellStatus(secret, gid, ['bittorrent'])
    path = server.getFiles(secret, gid)[0]['path']
    if bt:
        file_num = len(server.getFiles(secret, gid))
        if 'info' in bt:
            bt_name = bt['bittorrent']['info']['name']
        else:
            bt_name = os.path.basename(os.path.dirname(path))
        if not bt_name:
            bt_name = 'Task name not obtained yet'
        name = u'{bt_name} (BT: {file_num} files)'.format(bt_name=bt_name, file_num=file_num)
    else:
        name = os.path.basename(path)
        if not name:
            name = 'Task name not obtained yet'
    return name


def no_result_notify(status, filters):
    info = 'No ' + status + ' download'
    if filters:
        info += ' with '
        for filter in filters:
            info += '\'' + filter + '\' '
    wf.add_item(info)

def add_modifier_subs(item, active=False, done=False, info=''):
    subs = {'cmd': 'Resume download',
            'shift': 'Copy URL',
            'alt': 'Remove download'}
    if active:
        subs['cmd'] = 'Pause download'
    if done:
        subs['cmd'] = info
    item.add_modifier('cmd',subs['cmd'])
    item.add_modifier('shift',subs['shift'])
    item.add_modifier('alt',subs['alt'])
    


def get_tasks(command, status, filters):
    if status == 'active':
        if not get_active_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'pending':
        if not get_pending_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'paused':
        if not get_paused_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'done':
        if not get_completed_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'error':
        if not get_error_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'removed':
        if not get_removed_tasks(command, filters):
            no_result_notify(status, filters)
    elif status == 'waiting':
        a = get_pending_tasks(command, filters)
        b = get_paused_tasks(command, filters)
        if not (a or b):
            no_result_notify(status, filters)
    elif status == 'incomplete':
        a = get_paused_tasks(command, filters)
        b = get_error_tasks(command, filters)
        c = get_removed_tasks(command, filters)
        if not (a or b or c):
            no_result_notify(status, filters)
    elif status == 'stopped':
        a = get_completed_tasks(command, filters)
        b = get_error_tasks(command, filters)
        c = get_removed_tasks(command, filters)
        if not (a or b or c):
            no_result_notify(status, filters)
    elif status == 'all':
        a = get_active_tasks(command, filters)
        b = get_pending_tasks(command, filters)
        c = get_paused_tasks(command, filters)
        d = get_completed_tasks(command, filters)
        e = get_error_tasks(command, filters)
        f = get_removed_tasks(command, filters)
        if not (a or b or c or d or e or f):
            no_result_notify('Aria2', filters)


def get_active_tasks(command, filters):
    active = server.tellActive(secret, ['gid', 'completedLength', 'totalLength',
        'downloadSpeed', 'uploadSpeed', 'connections'])
    active = apply_filter(active, filters)
    if not active:
        return False
    for task in active:
        name = get_task_name(task)
        speed = int(task['downloadSpeed'])
        completed = int(task['completedLength'])
        total = int(task['totalLength'])
        if total == 0:
            percentage = 0
        else:
            percentage = float(completed) / float(total) * 100
        if speed > 0:
            seconds = (total - completed) / speed
            remaining = time_fmt(seconds)
        else:
            remaining = u'∞'
        info = u'{percentage:.2f}%, {completed} / {total}, {speed}, {remaining} left'.format(
                percentage=percentage,
                completed=size_fmt(completed),
                total=size_fmt(total),
                speed=size_fmt(speed, suffix='B/s'),
                remaining=remaining
                )
        arg = '--' + command + ' ' + task['gid']
        item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_active)
        add_modifier_subs(item=item,active=True)
    return True


def get_pending_tasks(command, filters):
    waiting = server.tellWaiting(secret, -1, 10, ['gid', 'status', 'completedLength',
        'totalLength'])
    waiting = [task for task in waiting if task['status'] == 'waiting']
    waiting = apply_filter(waiting, filters)
    if not waiting:
        return False
    for task in waiting:
        name = get_task_name(task)
        completed = int(task['completedLength'])
        total = int(task['totalLength'])
        if total == 0:
            percentage = 0
        else:
            percentage = float(completed) / float(total) * 100
        info = '{percentage:.2f}%, {completed} / {total}'.format(
                percentage=percentage,
                completed=size_fmt(completed),
                total=size_fmt(total))
        arg = '--' + command + ' ' + task['gid']
        item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_waiting)
        add_modifier_subs(item=item,active=True)
    return True


def get_paused_tasks(command, filters):
    waiting = server.tellWaiting(secret, -1, 10, ['gid', 'status', 'completedLength',
        'totalLength'])
    paused = [task for task in waiting if task['status'] == 'paused']
    paused = apply_filter(paused, filters)
    if not paused:
        return False
    for task in paused:
        name = get_task_name(task)
        completed = int(task['completedLength'])
        total = int(task['totalLength'])
        if total == 0:
            percentage = 0
        else:
            percentage = float(completed) / float(total) * 100
        info = '{percentage:.2f}%, {completed} / {total}'.format(
                percentage=percentage,
                completed=size_fmt(completed),
                total=size_fmt(total))
        arg = '--' + command + ' ' + task['gid']
        item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_paused)
        add_modifier_subs(item=item)
    return True


def get_stopped_tasks():
    stopped = server.tellStopped(secret, -1, 20, ['gid', 'status', 'completedLength',
        'totalLength', 'errorMessage'])
    return stopped


def get_completed_tasks(command, filters):
    stopped = get_stopped_tasks()
    completed = [task for task in stopped if task['status'] == 'complete']
    completed = apply_filter(completed, filters)
    if not completed:
        return False
    for task in completed:
        name = get_task_name(task)
        size = int(task['completedLength'])
        info = '100%, File Size: {size}'.format(size=size_fmt(size))
        arg = '--' + command + ' ' + task['gid']
        filepath = server.getFiles(secret, task['gid'])[0]['path'].encode('utf-8')
        if not os.path.exists(filepath):
            info = '[deleted] ' + info
            item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_deleted)
        else:
            item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_complete)
        add_modifier_subs(item=item,done=True, info=info)
    return True


def get_error_tasks(command, filters):
    stopped = get_stopped_tasks()
    error = [task for task in stopped if task['status'] == 'error']
    error = apply_filter(error, filters)
    if not error:
        return False
    for task in error:
        name = get_task_name(task)
        arg = '--' + command + ' ' + task['gid']
        completed = int(task['completedLength'])
        total = int(task['totalLength'])
        if total == 0:
            percentage = 0
        else:
            percentage = float(completed) / float(total) * 100
        info = u'{percentage:.2f}%, {completed} / {total}, {msg}'.format(
                percentage=percentage,
                completed=size_fmt(completed),
                total=size_fmt(total),
                msg=task.get('errorMessage', u'Unknown Error.'))
        item = wf.add_item(name, info, arg=arg, valid=True, icon=icon_error)
        add_modifier_subs(item=item,done=True, info=info)
    return True


def get_removed_tasks(command, filters):
    stopped = get_stopped_tasks()
    removed = [task for task in stopped if task['status'] == 'removed']
    removed = apply_filter(removed, filters)
    if not removed:
        return False
    for task in removed:
        name = get_task_name(task)
        arg = '--' + command + ' ' + task['gid']
        item = wf.add_item(name, u'This task is removed by user.', arg=arg, valid=True, icon=icon_removed)
        add_modifier_subs(item=item,done=True, info=info)    
    return True


def get_stats():
    if get_rpc():
        stats = server.getGlobalStat(secret)
        options = server.getGlobalOption(secret)
        wf.add_item('Active: ' + stats['numActive'],
                arg='--go-active', valid=True, icon=icon_active)
        wf.add_item('Waiting: ' + stats['numWaiting'],
                arg='--go-waiting', valid=True, icon=icon_waiting)
        wf.add_item('Stopped: ' + stats['numStopped'],
                arg='--go-stopped', valid=True, icon=icon_stopped)
        wf.add_item('Download: ' + size_fmt(int(stats['downloadSpeed']), suffix='B/s'),
                'Current download limit: {limit} KiB/s'.format(
                    limit=options['max-overall-download-limit']),
                arg='--go-download-limit-setting', valid=True, icon=icon_download)
        wf.add_item('Upload: ' + size_fmt(int(stats['uploadSpeed']), suffix='B/s'),
                'Current upload limit: {limit} KiB/s'.format(
                    limit=options['max-overall-upload-limit']),
                arg='--go-upload-limit-setting', valid=True, icon=icon_upload)


def limit_speed(type, param):
    if get_rpc():
        limit = int(server.getGlobalOption(secret)['max-overall-' + type +'-limit'])
        limit = speed_convert(limit)[1]
        param_s = speed_convert(param)[1]
        wf.add_item('Limit ' + type +' speed to: {limit}'.format(limit=param_s),
                'Current ' + type + ' limit (0 for no limit): ' + limit,
                arg='--limit-' + type + ' ' + param, valid=True)


def limit_num(param):
    if get_rpc():
        limit = server.getGlobalOption(secret)['max-concurrent-downloads']
        wf.add_item('Limit concurrent downloads to: {limit}'.format(limit=param),
                'Current concurrent downloads limit: ' + limit,
                arg='--limit-num ' + param, valid=True)


def main(wf):
    if wf.first_run:
        kill_notifier()

    statuses = ['all', 'active', 'pending', 'paused', 'waiting',
            'done', 'error', 'removed', 'stopped']
    actions = ['reveal', 'rm', 'url', 'pause', 'resume']
    settings = ['rpc', 'secret', 'limit', 'limitup', 'limitnum', 'clear', 'add', 'quit',
            'stat', 'help', 'pauseall', 'resumeall']
    commands = actions + settings

    command = 'reveal'
    status = 'all'
    param = ''

    if len(wf.args) == 1:
        if wf.args[0] in commands:
            command = wf.args[0]
        elif wf.args[0] in statuses:
            status = wf.args[0]
        else:
            param = wf.args[0:]
    elif len(wf.args) > 1:
        if wf.args[0] in settings:
            command = wf.args[0]
            param = wf.args[1]      #settings take one param only
        elif wf.args[0] in actions:
            command = wf.args[0]
            param = wf.args[1:]     #actions can take multiple param to filter the result
        elif wf.args[0] in statuses:
            status = wf.args[0]
            param = wf.args[1:]     #statuses can take multiple param to filter the result
        else:
            param = wf.args[0:]

    if command not in settings:
        if command == 'pause':
            status = 'active'
        elif command == 'resume':
            status = 'incomplete'
        if get_rpc():
            get_tasks(command, status, param)
    else:
        if command == 'rpc':
            wf.add_item('Set Aria2\'s RPC Path', 'Set the path to ' + param,
                arg=u'--rpc-setting ' + param, valid=True)
        elif command == 'secret':
            wf.add_item('Set Aria2\'s RPC Secret', 'Set the secret to ' + param,
                arg=u'--secret-setting ' + param, valid=True)
        elif command == 'add':
            wf.add_item('Add new download: ' + param, arg='--add ' + param, valid=True)
        elif command == 'clear':
            wf.add_item('Clear all stopped download?', arg='--clear', valid=True)
        elif command == 'pauseall':
            wf.add_item('Pause all active downloads?', arg='--pauseall', valid=True)
        elif command == 'resumeall':
            wf.add_item('Resume all paused downloads?', arg='--resumeall', valid=True)
        elif command == 'help':
            wf.add_item('Need some help?', arg='--help', valid=True)
        elif command == 'quit':
            wf.add_item('Quit Aria2?', arg='--quit', valid=True)
        elif command == 'limit':
            limit_speed('download', param)
        elif command == 'limitup':
            limit_speed('upload', param)
        elif command == 'limitnum':
            limit_num(param)
        elif command == 'stat':
            get_stats()

    if wf.update_available:
        wf.add_item('New version available',
                    'Action this item to install the update',
                    autocomplete='workflow:update')

    wf.send_feedback()

    if not is_running('notifier'):
        cmd = ['/usr/bin/python', wf.workflowfile('notifier.py')]
        run_in_background('notifier', cmd)


if __name__ == '__main__':

    icon_active = 'active.png'
    icon_paused = 'paused.png'
    icon_waiting = 'waiting.png'
    icon_complete = 'complete.png'
    icon_deleted = 'deleted.png'
    icon_removed = 'removed.png'
    icon_error = 'error.png'
    icon_download = 'download.png'
    icon_upload = 'upload.png'
    icon_stopped = 'stopped.png'

    defaults = {
        'rpc_path': 'http://localhost:6800/rpc',
        'secret': ''
    }
    update_settings = {
        'github_slug': 'Wildog/Ariafred',
        'frequency': 1
    }

    wf = Workflow3(default_settings=defaults, update_settings=update_settings)

    server = None

    if 'secret' not in wf.settings:
        wf.settings['secret'] = ''
    secret = 'token:' + wf.settings['secret']
    wf.rerun=1
    sys.exit(wf.run(main))
