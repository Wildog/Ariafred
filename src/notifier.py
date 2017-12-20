# -*- coding: utf-8 -*-
import os
import socket
import sys
import threading
import xmlrpclib
from workflow import Workflow3


def escape(s, char=' '):
    return s.replace(char, '\\' + char)


def notify(msg, title='Ariafred', gid=''):
    notifier = os.path.join(wf.workflowdir, 'Ariafred.app/Contents/MacOS/Ariafred')
    notifier = escape(notifier)
    msg = escape(msg, char='[')
    os_command = '%s -title "%s" -message "%s"' % (notifier.encode('utf-8'),
                                                   title.encode('utf-8'),
                                                   msg.encode('utf-8'))
    if gid:
        dir = server.tellStatus(secret, gid, ['dir'])['dir']
        filepath = server.getFiles(secret, gid)[0]['path'].encode('utf-8')
        if os.path.exists(filepath):
            click_command = 'open -R "%s"' % filepath
        else:
            click_command = 'open "%s" ' % dir
        os_command = '%s -execute \'%s\'' % (os_command, click_command)
    os.system(os_command)


def main(wf):
    update_watch_list()
    get_notified()


def update_watch_list():
    threading.Timer(2.0, update_watch_list).start()
    try:
        active = server.tellActive(secret, ['gid'])
    except (xmlrpclib.Fault, socket.error):
        pass
    else:
        for task in active:
            gid = task['gid']
            with lock:
                if gid not in watch_list:
                    watch_list.append(gid)


def get_notified():
    threading.Timer(1.0, get_notified).start()
    for gid in watch_list:
        try:
            task = server.tellStatus(secret, gid, ['status', 'errorMessage'])
            status = task['status']
        except (xmlrpclib.Fault, socket.error):
            pass
        else:
            if status == 'active':
                return
            elif status == 'complete':
                notify(title='Download completed: ', msg=get_task_name(gid), gid=gid)
            elif status == 'error':
                notify(title='Error occurred while downloading "' + get_task_name(gid) + '":',
                        msg=task['errorMessage'], gid=gid)
            with lock:
                watch_list.remove(gid)


def get_task_name(gid):
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


if __name__ == '__main__':

    watch_list = []
    lock = threading.Lock()

    wf = Workflow3()

    rpc_path = wf.settings['rpc_path']
    secret = 'token:' + wf.settings['secret']
    server = xmlrpclib.ServerProxy(rpc_path).aria2

    sys.exit(wf.run(main))
