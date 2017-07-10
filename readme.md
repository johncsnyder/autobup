
# autobup


Auto bup backup using fsevents on OS X


Example usage:


- Run `autobup -h` to get help


- Run in the background `nohup autobup > /usr/local/var/log/autobup.log &`


- Requires MacFSEvents

`https://pypi.python.org/pypi/MacFSEvents`



- Example `.bupignore` file:

	```
	.DS_Store
	test.egg-info
	.git
	__pycache__
	test/__pycache__
	```

	Does not support glob patterns yet
