# PTT - Python Time Tracker

Copyright (C) 2019 David CH. All rights reserved.\
Portions Copyright (C) 2019 David CH. All rights reserved.\
For conditions of distribution and use, see LICENSE.TXT.

What is PTT ?
-------------

It's just a simple time tracker to load and save tasks done or in progress.\
It consists in typing the task description and push Enter or the Add task button.

Where is the data saved ?
-------------------------

In the folder /data. The data is saved in the JSON format. The current data is saved in a file called "my_tasks.json".\
When the application starts, it tries to load up the file contents mentionned before.

Also, if the file exists, a copy of the file is created under the name "my_tasks.backup".\
This latest file purpose is just to manually replace the former one... just in case (= file lost, corrupted or cleared).

Of course if you start again the application with an ampty "my_tasks.json"... it will overwrite the existing backup file.

With which tools, libraries etc... the application was made ?
-------------------------------------------------------------

* Python 3.7.0 and PyQt 5.11.2 (API/GUI library)
* Forms were created/designed with the Qt Designer and the .ui files are loaded dynamically in the application
* JetBrains PyCharm Community Edition 2018.1.4 (IDE)
* The icon was made with GIMP
* Pyinstaller for freezing the code (not built in one file mode, for performance)
* Inno Setup 6.0.3 for the free Windows installer

Is it your 1st application and 1st time using Python ?
------------------------------------------------------

Yes to both, so there are probably horrors made in the code, concepts unclear etc... so forgive me !\
There are tons of details to fix, so don't be too harsh, i'm trying to fix them as soon i see them.

How to build the application ?
------------------------------

With Pyinstaller, that should give something like this :

```
pyinstaller ptt_main.py -w -n ptt.exe --add-data="ui\*.*";"ui" --add-data="data\*.*";"data" -i "ui\ptt.ico" --version-file "ptt_version_info.txt"
```
