#Ariafred

![screenshot](http://7xqhhm.com1.z0.glb.clouddn.com/images/ariafred.gif)
Manage Aria2 downloads directly in Alfred, with background notification.

##Usage

###Activate Ariafred

The default hot key is `Command` + `Shift` + `A`, or you can type keyword `aria` in Alfred to activate Ariafred

###Filter by Query

1. Type task name to filter
2. Type `active` / `done` / `paused` / `queued` / `error` to filter by status
3. You can filter by status and task name simultaneously:
![filter](http://7xqhhm.com1.z0.glb.clouddn.com/images/filter.png)

###Overall status

![stat](http://7xqhhm.com1.z0.glb.clouddn.com/images/stat.png)

1. Type keyword `stat` to view overall status
2. Press `Enter` on Active / Waiting / Stopped to view tasks in corresponding status
3. Press `Enter` on Download / Upload to go to speed limit settings

###Add a task

Type `add` plus the url, HTTP/FTP/SFTP/Magnet supported

###Open saved directory

Press `Enter` on any task

###Pause/Resume tasks

1. Press `Command` + `Enter` on any task
2. Or type `pause` / `resume` then press `Enter` on a task
4. Type `pauseall` / `resumeall` will pause/resume all task 

###Remove tasks

1. Press `Option` + `Enter` on any task
2. Or type `remove` then press `Enter` on a task

###Copy URL to clipboard

1. Press `Control` + `Enter` on any task
2. Type `url` then press `Enter` on a task

###Clear all stopped tasks

Type `clear` then press `Enter`

###Set speed limit and max concurrent downloads

1. Type `limit` plus speed(KiB/s) to set download speed limit
2. Type `limitup` plus speed(KiB/s) to set upload speed limit
2. Type `limitup` plus a number to set max concurrent downloads

###Set RPC address

The default RPC address Ariafred connects to is `http://localhost:6800/rpc`, change via typing `rpc`  plus your own RPC address then press `Enter`

###Start/Quit Aria2

![filter](http://7xqhhm.com1.z0.glb.clouddn.com/images/run.png)

1. Ariafred will prompt you to start Aria2 or change RPC address if it fails to connect to Aria2, press `Enter` on starting aria2 to try launching Aria2
2. Type `quit` to quit Aria2

###Get help

Type `help` to view this page anytime

###Update

Ariafred will automatically check for update and prompt you to update

###Caveat

Background notification will not work under Mac OS X 10.8 or older system

##License
MIT
