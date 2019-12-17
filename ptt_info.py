#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* --------------------------------------------------------------------------------- *
* Application name : PTT (Python Time Tracker)
* Script name : ptt_info.py
* Created by DCH (June / December 2019)
* --------------------------------------------------------------------------------- *
* Modified by XXX on the DD/MM/YYYY
* --------------------------------------------------------------------------------- *
* Notes : only contains for now the class PttAppInfo
* --------------------------------------------------------------------------------- *
"""


# Class PttAppInfo : just for storing externally the application information (version, author etc...)
class PttAppInfo:
    def __init__(self):
        self.version = "0.2.5 (17/12/2019)"
        self.author = "dchlab (David CH.)"
        self.github = "https://github.com/dchlab"
        self.dependencies = "PyQt5"
