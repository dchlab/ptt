#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* --------------------------------------------------------------------------------- *
* Application name : PTT (Python Time Tracker)
* Script name : ptt_info.py
* Created by DCH (June 2019 -> 2020)
* --------------------------------------------------------------------------------- *
* Modified by XXX on the DD/MM/YYYY
* --------------------------------------------------------------------------------- *
* Notes : only contains for now the class PttAppInfo
* --------------------------------------------------------------------------------- *
"""

# ------------------------------------------- #
# Imports
# ------------------------------------------- #

from PyQt5.QtCore import QT_VERSION_STR


# Class PttAppInfo : just for storing externally the application information (version, author etc...)
class PttAppInfo:
    def __init__(self):
        self.version = "0.2.7 (04/01/2020)"
        self.author = "dchlab (David CH.)"
        self.github = "https://github.com/dchlab"
        self.dependencies = "PyQt {}".format(QT_VERSION_STR)
