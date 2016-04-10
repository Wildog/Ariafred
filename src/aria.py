# -*- coding: utf-8 -*-
import os
import socket
import sys
import xmlrpclib
from workflow import Workflow
from workflow.background import run_in_background, is_running


def get_rpc():
    global server
    rpc_path = wf.settings['rpc_path']
    server = xmlrpclib.ServerProxy(rpc_path).aria2
    try:
        version = server.getVersion()
    except (xmlrpclib.Fault, socket.error):
        wf.add_item(u'Aria2 may not be running, try starting it?', u'Press Enter',
                arg=u'--run-aria2', valid=True)
        wf.add_item(u'Or change RPC path?', u'Currently using ' + rpc_path,
                arg=u'--go-rpc-setting', valid=True)
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


def apply_filter(tasks, filter):
    if filter:
        filtered_tasks = wf.filter(filter, tasks,
                lambda task: get_task_name(task), min_score=20)
    else:
        filtered_tasks = tasks
    return filtered_tasks


def get_task_name(task):
    gid = task['gid']
    bt = server.tellStatus(gid, ['bittorrent'])
    if bt:
        bt_name = bt['bittorrent']['info']['name']
        file_num = len(server.getFiles(gid))
        name = '{bt_name} (BT: {file_num} files)'.format(bt_name=bt_name, file_num=file_num)
    else:
        path = server.getFiles(gid)[0]['path']
        name = os.path.basename(path)
    return name


def no_result_notify(status, filter):
    info = 'No ' + status + ' download'
    if filter:
        info += u' with \'{filter}\''.format(filter=filter)
    wf.add_item(info)


def get_modifier_subs(active=False, done=False, info=''):
    subs = {'cmd': 'Resume download',
            'shift': 'Copy URL',
            'alt': 'Remove download'}
    if active:
        subs['cmd'] = 'Pause download'
    if done:
        subs['cmd'] = info
    return subs


def get_tasks(command, status, filter):
    if status == 'active':
        if not get_active_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'queued':
        if not get_queued_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'paused':
        if not get_paused_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'done':
        if not get_completed_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'error':
        if not get_error_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'removed':
        if not get_removed_tasks(command, filter):
            no_result_notify(status, filter)
    elif status == 'waiting':
        a = get_queued_tasks(command, filter)
        b = get_paused_tasks(command, filter)
        if not (a or b):
            no_result_notify(status, filter)
    elif status == 'incomplete':
        a = get_paused_tasks(command, filter)
        b = get_error_tasks(command, filter)
        c = get_removed_tasks(command, filter)
        if not (a or b or c):
            no_result_notify(status, filter)
    elif status == 'stopped':
        a = get_completed_tasks(command, filter)
        b = get_error_tasks(command, filter)
        c = get_removed_tasks(command, filter)
        if not (a or b or c):
            no_result_notify(status, filter)
    elif status == 'all':
        a = get_active_tasks(command, filter)
        b = get_queued_tasks(command, filter)
        c = get_paused_tasks(command, filter)
        d = get_completed_tasks(command, filter)
        e = get_error_tasks(command, filter)
        f = get_removed_tasks(command, filter)
        if not (a or b or c or d or e or f):
            no_result_notify('Aria2', filter)


def get_active_tasks(command, filter):
    active = server.tellActive(['gid', 'completedLength', 'totalLength', 
        'downloadSpeed', 'uploadSpeed', 'connections'])
    active = apply_filter(active, filter)
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
        subs = get_modifier_subs(active=True)
        wf.add_item(name, info, arg=arg, valid=True, 
                modifier_subtitles=subs, icon=icon_active)
    return True


def get_queued_tasks(command, filter):
    waiting = server.tellWaiting(-1, 10, ['gid', 'status', 'completedLength',
        'totalLength'])
    waiting = [task for task in waiting if task['status'] == 'waiting']
    waiting = apply_filter(waiting, filter)
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
        subs = get_modifier_subs()
        wf.add_item(name, info, arg=arg, valid=True, 
                modifier_subtitles=subs, icon=icon_waiting)
    return True


def get_paused_tasks(command, filter):
    waiting = server.tellWaiting(-1, 10, ['gid', 'status', 'completedLength',
        'totalLength'])
    paused = [task for task in waiting if task['status'] == 'paused']
    paused = apply_filter(paused, filter)
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
        subs = get_modifier_subs()
        wf.add_item(name, info, arg=arg, valid=True,
                modifier_subtitles=subs, icon=icon_paused)
    return True


def get_stopped_tasks():
    stopped = server.tellStopped(-1, 20, ['gid', 'status', 'completedLength',
        'totalLength', 'errorMessage'])
    return stopped


def get_completed_tasks(command, filter):
    stopped = get_stopped_tasks()
    completed = [task for task in stopped if task['status'] == 'complete']
    completed = apply_filter(completed, filter)
    if not completed:
        return False
    for task in completed:
        name = get_task_name(task)
        size = int(task['completedLength'])
        info = '100%, File Size: {size}'.format(size=size_fmt(size))
        arg = '--' + command + ' ' + task['gid']
        subs = get_modifier_subs(done=True, info=info)
        wf.add_item(name, info, arg=arg, valid=True, 
                modifier_subtitles=subs, icon=icon_complete)
    return True


def get_error_tasks(command, filter):
    stopped = get_stopped_tasks()
    error = [task for task in stopped if task['status'] == 'error']
    error = apply_filter(error, filter)
    if not error:
        return False
    for task in error:
        name = get_task_name(task)
        arg = '--' + command + ' ' + task['gid']
        subs = get_modifier_subs()
        wf.add_item(name, task['errorMessage'], arg=arg, valid=True, 
                modifier_subtitles=subs, icon=icon_error)
    return True


def get_removed_tasks(command, filter):
    stopped = get_stopped_tasks()
    removed = [task for task in stopped if task['status'] == 'removed']
    removed = apply_filter(removed, filter)
    if not removed:
        return False
    for task in removed:
        name = get_task_name(task)
        arg = '--' + command + ' ' + task['gid']
        subs = get_modifier_subs()
        wf.add_item(name, u'This task is removed by user.', arg=arg, valid=True,
            modifier_subtitles=subs, icon=icon_removed)
    return True


def get_stats():
    if get_rpc():
        stats = server.getGlobalStat()
        options = server.getGlobalOption()
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
        limit = int(server.getGlobalOption()['max-overall-' + type +'-limit'])
        limit = str(limit) + ' KiB/s'
        wf.add_item('Limit ' + type +' speed to: {limit} KiB/s'.format(limit=param), 
                'Current ' + type + ' limit (0 for no limit): ' + limit,
                arg='--limit-' + type + ' ' + param, valid=True)


def limit_num(param):
    if get_rpc():
        limit = server.getGlobalOption()['max-concurrent-downloads']
        wf.add_item('Limit concurrent downloads to: {limit}'.format(limit=param), 
                'Current concurrent downloads limit: ' + limit,
                arg='--limit-num ' + param, valid=True)


def main(wf):
    statuses = ['all', 'active', 'queued', 'paused', 'waiting',
            'done', 'error', 'removed', 'stopped']
    actions = ['open', 'rm', 'url', 'pause', 'resume']
    settings = ['rpc', 'limit', 'limitup', 'limitnum', 'clear', 'add', 'quit', 
            'stat', 'pauseall', 'resumeall']
    commands = actions + settings

    command = 'open'
    status = 'all'
    param = ''

    if len(wf.args) == 1:
        if wf.args[0] in commands:
            command = wf.args[0]
        elif wf.args[0] in statuses:
            status = wf.args[0]
        else:
            param = wf.args[0]
    elif len(wf.args) > 1:
        if wf.args[0] in commands:
            command = wf.args[0]
            param = wf.args[1]
        elif wf.args[0] in statuses:
            status = wf.args[0]
            param = wf.args[1]
        else:
            param = wf.args[0]

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
        elif command == 'add':
            wf.add_item('Add new download: ' + param, arg='--add ' + param, valid=True)
        elif command == 'clear':
            wf.add_item('Clear all stopped download?', arg='--clear', valid=True)
        elif command == 'pauseall':
            wf.add_item('Pause all active downloads?', arg='--pauseall', valid=True)
        elif command == 'resumeall':
            wf.add_item('Resume all paused downloads?', arg='--resumeall', valid=True)
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
    icon_removed = 'removed.png'
    icon_error = 'error.png'
    icon_download = 'download.png'
    icon_upload = 'upload.png'
    icon_stopped = 'stopped.png'

    server = None

    defaults = {'rpc_path': 'http://localhost:6800/rpc'}
    update_settings={
        'github_slug': 'Wildog/Ariafred',
        'frequency': 1
    }
    wf = Workflow(default_settings=defaults, update_settings=update_settings)
    sys.exit(wf.run(main))
