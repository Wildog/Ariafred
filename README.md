# Ariafred

![screenshot](https://github.com/Wildog/Ariafred/raw/master/screenshots/ariafred.gif)

Manage Aria2 downloads directly in Alfred, with background notification.

## Usage

### Activate Ariafred

You can set hotkey to activate Ariafred after installing it, my personal recommendation is `Command` + `Shift` + `A`, you can also type keyword `aria` in Alfred to activate Ariafred

### Filter by query

1. Type keywords to filter by task name
2. Type `active` / `done` / `paused` / `pending` / `error` to filter by status
3. You can filter by status and task name simultaneously:

![filter](https://github.com/Wildog/Ariafred/raw/master/screenshots/filter.png)

### Overall status

![stat](https://github.com/Wildog/Ariafred/raw/master/screenshots/stat.png)

1. Type keyword `stat` to view overall status
2. Press `Enter` on Active / Waiting / Stopped to view tasks in corresponding status
3. Press `Enter` on Download / Upload to go to speed limit settings

### Add a task

Type `add` plus the url then press `Enter`, HTTP/FTP/SFTP/Magnet links are supported. 

It is recommended that you add a default download path in your `aria2.conf`, take it as an example: `dir=/foo/bar`, tasks added by Ariafred will be downloaded to this path.

### Add BT task via .torrent files

![bt](https://github.com/Wildog/Ariafred/raw/master/screenshots/bt.png)

Execute [file action](https://www.alfredapp.com/help/features/file-search/#file-actions) 'Add BT download to Aria2'

### Reveal download

1. Press `Enter` on a task to reveal download in Finder
2. Press `Ctrl` + `Enter` on a task to reveal download in Alfred
3. Click on a notification to reveal related download in Finder

### Pause/Resume tasks

1. Press `Command` + `Enter` on a task
2. Or type `pause` / `resume` then press `Enter` on a task
3. Type `pauseall` / `resumeall` will pause/resume all task 

### Remove tasks

1. Press `Option` + `Enter` on a task
2. Or type `rm` then press `Enter` on a task

### Copy URL to clipboard

1. Press `Control` + `Enter` on a task
2. Type `url` then press `Enter` on a task

### Clear all stopped tasks

Type `clear` then press `Enter`

### Set speed limit and max concurrent downloads

1. Type `limit` plus speed(KiB/s) to set download speed limit
2. Type `limitup` plus speed(KiB/s) to set upload speed limit
3. Type `limitnum` plus a number to set max concurrent downloads

### Set RPC

1. The default RPC address Ariafred connects to is `http://localhost:6800/rpc`, change via typing `rpc`  plus your own RPC address then press `Enter`. FYI, Ariafred uses xml-rpc instead of json-rpc that some WebUI uses for Aria2, so make sure your RPC address end with `/rpc` but not `/jsonrpc`.
2. The default rpc-secret Ariafred uses is empty, if you have configured your own rpc-secret in your `aria2.conf` you should set the secret by typing `secret` plus your own rpc-secret then press `Enter` 

### Start/Quit Aria2

![filter](https://github.com/Wildog/Ariafred/raw/master/screenshots/run.png)

1. Ariafred will prompt you to start Aria2 or change RPC address if it fails to connect to Aria2, press `Enter` on starting aria2 to try launching Aria2
2. Type `quit` to quit Aria2

### Get help

Type `help` to view this page anytime

### Update

Ariafred will automatically check for update and prompt you to update

### Caveat

Background notification will not work under Mac OS X 10.8 or older system

## License

MIT
