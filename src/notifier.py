# -*- coding: utf-8 -*-
import os
import socket
import sys
import threading
import xmlrpclib
from workflow import Workflow
from workflow.notify import notify


def main(wf):
    update_watch_list()
    get_notified()


def update_watch_list():
    threading.Timer(5.0, update_watch_list).start()
    try:
        active = server.tellActive(['gid']) 
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
            task = server.tellStatus(gid, ['status', 'errorMessage'])
            status = task['status']
        except (xmlrpclib.Fault, socket.error):
            pass
        else:
            if status == 'active':
                return
            elif status == 'complete':
                notify('Download completed: ', get_task_name(gid))
            elif status == 'error':
                notify('Error occurred while downloading "' + get_task_name(gid) + '":',
                        task['errorMessage'])
            with lock:
                watch_list.remove(gid)


def get_task_name(gid):
    bt = server.tellStatus(gid, ['bittorrent'])
    if bt:
        bt_name = bt['bittorrent']['info']['name']
        file_num = len(server.getFiles(gid))
        name = '{bt_name} (BT: {file_num} files)'.format(bt_name=bt_name, file_num=file_num)
    else:
        path = server.getFiles(gid)[0]['path']
        name = os.path.basename(path)
    return name


if __name__ == '__main__':

    watch_list = []
    lock = threading.Lock()

    wf = Workflow()
    rpc_path = wf.settings['rpc_path']
    server = xmlrpclib.ServerProxy(rpc_path).aria2
    sys.exit(wf.run(main))
