# ptt
PTT - Python Time Tracker

What is PTT ?
-------------

It's just a simple time tracker to load and save tasks done or in progress.
It consists in typing the task description and push Enter or the Add task button.

Where is saved the data ?
-------------------------

In the folder /data. The data is saved in the JSON format. The current data is saved in a file called "my_tasks.json".
When the application starts, it tries to load up the file contents mentionned before.
Also, if the file exists, a copy of the file is created under the name "my_tasks.backup".
This latest file purpose is just to replace manually the former one... just in case (file lost, corrupted or cleared).
Of course if you start again the application with an ampty "my_tasks.json"... it'll clear the backup one.

With which tools, libraries etc... the application was made ?
-------------------------------------------------------------

Python 3.7.0 and PyQt 5.11.2
Forms were created/designed with the Qt Designer and the .ui files are loaded dynamically in the application

JetBrains PyCharm Community Edition 2018.1.4 for the coding
The icon was made with GIMP (image multi-layered with all dimensions then exported to .ico format)
Pyinstaller for freezing the code (avoiding to build it as one file... for better performance)

Is it your 1st application and 1st time using Python ?
------------------------------------------------------

Yes x2, so there are probably horrors made in the code, concepts unclear etc... so forgive me !

How to build the application ?
------------------------------

pyinstaller ptt_main.py -w -n ptt.exe --add-data="ui\*.*";"ui" --add-data="data\*.*";"data" -i "ui\ptt.ico" --version-file "ptt_version_info.txt"
