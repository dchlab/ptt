#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* --------------------------------------------------------------------------------- *
* Application name : PTT (Python Time Tracker)
* Script name : ptt_main.py
* Created by DCH (Started on June 2019 -> 2020)
* --------------------------------------------------------------------------------- *
* Modified by XXX on the DD/MM/YYYY
* --------------------------------------------------------------------------------- *
* Notes :
* - Requires PyQT5 to run and be compiled
* - Note that the .ui files are loaded dynamically (for now)
* --------------------------------------------------------------------------------- *
* Source files required :
* - ptt_main.py                         The main script
* - ptt_info.py                         Class PttAppInfo
* Resources and UI files required :
* - /ui/ptt_main.ui                     Main window form
* - /ui/ptt_edit_task.ui                Edit task form
* - /ui/ptt.ico                         Icon used in .ui files
* User data files used :
* - /data/my_tasks.json                 Tasks saved in a JSON format
* - /data/my_tasks.backup               Backup of the previous file (at startup)
* - /data/ptt_config.ini                User settings like language preferences...
* Miscellaneous files used/generated :
* - /data/ptt.lock                      Used as pseudo lock file
* --------------------------------------------------------------------------------- *
To build the application from PyInstaller, go in the ptt (root) folder then :
pyinstaller ptt_main.py -w -n ptt.exe --add-data="ui\*.*";"ui"
            --add-data="data\*.*";"data" -i "ui\ptt.ico"
            --version-file "ptt_version_info.txt"
* --------------------------------------------------------------------------------- *
"""

# ------------------------------------------- #
# Imports
# ------------------------------------------- #

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QAction
from PyQt5.QtCore import Qt, QTime, QObject
from PyQt5.QtGui import QFont
from shutil import copyfile
from ptt_info import PttAppInfo
import sys
import os
import json
import datetime
import configparser


# ------------------------------------------- #
# Classes
# ------------------------------------------- #

# Class PttFiles : contains the data file names used in the application
class PttFiles:
    def __init__(self):
        self.my_tasks_json = "data/my_tasks.json"
        self.my_tasks_backup = "data/my_tasks.backup"
        self.ptt_lock = "data/ptt.lock"
        self.ptt_config_ini = "data/ptt_config.ini"


# Class PttResourcesFiles : contains the file names used for the resources in the application
class PttResourcesFiles:
    def __init__(self):
        self.main_ui = "ui/ptt_main.ui"
        self.edit_task_ui = "ui/ptt_edit_task.ui"
        self.ptt_ico = "ui/ptt.ico"


# Class TaskDuration : contains the task duration members
class TaskDuration:
    def __init__(self):
        self.days = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0


# Class PttConfigValues : contains the values of the ptt_config.ini file
class PttConfigValues:
    def __init__(self):
        self.UI_Language = ""


# Object for edit_task_signal calling parameters between windows
class PttEditObject(QObject):
    edit_task_signal = QtCore.pyqtSignal(int, str, str, str)


# Classes initializations
ptt_main_calling_edit = PttEditObject()
ptt_edit_task_saving = PttEditObject()
ptt_resources = PttResourcesFiles()


# ------------------------------------------- #
# Miscellaneous / Specific functions
# ------------------------------------------- #

# Function ptt_resource_path : gets absolute path to resource, works for dev mode and for PyInstaller "onefile" .exe
def ptt_resource_path(p_relative_path: str):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS (But not used as of today in PTT)
        w_base_path = sys._MEIPASS
    except:
        w_base_path = os.path.abspath(".")

    return os.path.join(w_base_path, p_relative_path)


# Function convert_task_duration_secs_to_dhms : converts a duration in secs into days/hours/minutes/secs
def convert_task_duration_secs_to_dhms(p_duration_in_secs: int, p_working_day_duration_in_secs: int):

    # Miscellaneous initializations
    w_task_duration = TaskDuration()
    w_secs_in_a_day = 86400

    # Calculating the duration in days (for a working day duration if it's filled, 24*3600 secs otherwise)
    if p_working_day_duration_in_secs > 0:
        w_task_duration.days = p_duration_in_secs // p_working_day_duration_in_secs
        w_task_duration.seconds = p_duration_in_secs % p_working_day_duration_in_secs
    else:
        w_task_duration.days = p_duration_in_secs // w_secs_in_a_day
        w_task_duration.seconds = p_duration_in_secs % w_secs_in_a_day

    # Calculating the duration in hours (with the remainder)
    if w_task_duration.seconds > 0:
        w_task_duration.hours = w_task_duration.seconds // 3600
        w_task_duration.seconds = w_task_duration.seconds % 3600

    # Calculating the duration in minutes (with the remainder)
    if w_task_duration.seconds > 0:
        w_task_duration.minutes = w_task_duration.seconds // 60
        w_task_duration.seconds = w_task_duration.seconds % 60

    # Returning the values in the form of a class
    return w_task_duration


# Function read_ptt_config : reads ptt_config.ini and returns the values found as a class
def read_ptt_config():

    # Miscellaneous initializations
    w_ptt_config_values = PttConfigValues()
    w_ptt_files = PttFiles()
    w_language = ""
    w_error_when_reading = False

    # Reading the config file
    w_ptt_config = configparser.ConfigParser()
    try:
        w_ptt_config.read(w_ptt_files.ptt_config_ini)
    except:
        print("read_ptt_config : error when reading the '{}' file".format(w_ptt_files.ptt_config_ini))
        w_error_when_reading = True

    # We continue if no error occurred when parsing the .ini file
    if w_error_when_reading is False:

        # Reading the [UI] section and its keys ; also using fallback values, just in case...
        try:
            w_ui_section = w_ptt_config["UI"]
            w_language = w_ui_section.get("language", "")
        except:
            print("read_ptt_config : cannot find the [UI] section in the '{}' file".format(w_ptt_files.ptt_config_ini))

        # If the language code found is not supported or not valid, we set it to the default value
        if w_language not in {"fr", "en"}:
            w_language = "fr"

        # Updating section [UI] / key "Language" value in the class
        w_ptt_config_values.UI_Language = w_language

    # Returning the config values class
    return w_ptt_config_values


# Function write_ptt_config : writes ptt_config.ini from the values found in a class received
def write_ptt_config(p_ptt_config_values: PttConfigValues):

    # Miscellaneous initializations
    w_ptt_files = PttFiles()
    w_language = p_ptt_config_values.UI_Language
    w_error_when_reading = False

    # If the language code found is not supported or not valid, we set it to the default value
    if w_language not in {"fr", "en"}:
        w_language = "fr"

    # Reading the config file
    w_ptt_config = configparser.ConfigParser()
    try:
        w_ptt_config.read(w_ptt_files.ptt_config_ini)
    except:
        print("write_ptt_config : error when reading the '{}' file".format(w_ptt_files.ptt_config_ini))
        w_error_when_reading = True

    # We continue if no error occurred when parsing the .ini file
    if w_error_when_reading is False:

        # Adding the [UI] section if none was found
        if w_ptt_config.has_section("UI") is False:
            try:
                w_ptt_config.add_section("UI")
            except:
                print("write_ptt_config : error when adding the [UI] section in the '{}' file"
                      .format(w_ptt_files.ptt_config_ini))

        # Updating section [UI] / key "Language" value in the config parser
        w_ptt_config.set("UI", "language", w_language)

        # Saving the whole config parser in the .ini file
        try:
            with open(w_ptt_files.ptt_config_ini, "w") as w_configfile:
                w_ptt_config.write(w_configfile)
        except:
            print("write_ptt_config : cannot write in the '{}' file".format(w_ptt_files.ptt_config_ini))


# Function ptt_load_translators : load translator(s) according to the language settings
def ptt_load_translators():

    # Miscellaneous initializations
    w_locale = ""
    w_main_translator = QtCore.QTranslator()
    w_qt_translations_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)

    # Retrieving language from the .ini config file
    w_ptt_config_values = read_ptt_config()

    # For now, we only deal with french and english languages (french is the default language)
    if w_ptt_config_values.UI_Language == "fr":
        w_locale = "fr_FR"
    elif w_ptt_config_values.UI_Language == "en":
        w_locale = "en_GB"
    elif w_ptt_config_values.UI_Language not in {"fr", "en"}:
        w_locale = "fr_FR"

    # Loading the general translator with the right "qtbase_locale.qm" (generic search with fr_FR, fr if not found...)
    # -> That will automatically fix the system texts like Yes/No texts for buttons (example)

    w_main_translator.load("qtbase_" + w_locale, w_qt_translations_path)

    # Returning the main translator
    return w_main_translator


# ------------------------------------------- #
# Main window (ptt_main)
# ------------------------------------------- #

ptt_main_ui_path = ptt_resource_path(ptt_resources.main_ui)
ptt_main_app = QtWidgets.QApplication([])
ptt_main_dlg = uic.loadUi(ptt_main_ui_path)

# ------------------------------------------- #
# Edit task window (ptt_edit_task)
# ------------------------------------------- #

ptt_edit_task_ui_path = ptt_resource_path(ptt_resources.edit_task_ui)
ptt_edit_task_app = QtWidgets.QApplication([])
ptt_edit_task_dlg = uic.loadUi(ptt_edit_task_ui_path)

# ------------------------------------------- #
# Global variables
# ------------------------------------------- #

# Retrieve external application information
glb_ptt_app_info = PttAppInfo()

# Global variables for intervals and others duration
glb_timer_ptt_lock_interval_in_msec = 30000
glb_timer_interval_in_msec = 60000
glb_default_added_duration_in_sec = 60
glb_max_task_duration_in_sec = 28800

# Active task timer management
glb_active_task_timer = QtCore.QTimer()
glb_active_task_timer.start(glb_timer_interval_in_msec)

# ptt.lock timer management
glb_ptt_lock_timer = QtCore.QTimer()
glb_ptt_lock_timer.start(glb_timer_ptt_lock_interval_in_msec)

# Date/time string format displayed
glb_dd_MM_yyyy_hh_mm_string_format = "dd/MM/yyyy hh:mm"

# Time string format displayed
glb_hh_mm_string_format = "hh:mm"

# Default time, used for durations = 00:00 (in hh:mm format)
glb_00_00_time = "00:00"

# Setting min/max tasks default values
glb_minimum_time_per_task = QTime()
glb_maximum_time_per_task = QTime()
glb_minimum_time_per_task.setHMS(0, 0, 0)
glb_maximum_time_per_task.setHMS(8, 0, 0)

# Important note : for now, only texts of the buttons are dynamically translated (fr_FR or default)
# Rest of the text errors are only in french for now in this version...

# Labels for "+" and "-"
glb_plus = "+"
glb_minus = "-"

# Default task name for the task automatically created, if none was found
glb_default_task_name = "Tâche créée automatiquement"

# Task name text when the application starts up AND if no tasks found
glb_new_task_at_startup = "Tâche créée au démarrage de l'application"

# Popup actions text displayed
glb_actionActivate_text = "Activer"
glb_actionEdit_text = "Modifier"
glb_actionMerge_text = "Fusionner"
glb_actionDelete_text = "Supprimer"
glb_actionDeleteAll_text = "Tout supprimer"

# Texts for the "About" popup
glb_about_title = "A propos de PTT"
glb_about_info = "PTT - Python Time Tracker\nVersion : {}\n\nAuteur : {}\nGithub : {}\n\nLibrairie(s) utilisée(s) : {}"\
    .format(glb_ptt_app_info.version, glb_ptt_app_info.author, glb_ptt_app_info.github, glb_ptt_app_info.dependencies)

# Miscellaneous texts (for message boxes etc...)
glb_popup_title_generic_error = "PTT - Python Time Tracker"
glb_popup_text_app_is_already_running = "PTT est déjà en cours d'exécution."
glb_popup_title_all_tasks_deletion = "ATTENTION !"
glb_popup_question_all_tasks_deletion = "Voulez-vous supprimer TOUTES les tâches ?"
glb_popup_title_deletion = "Suppression"
glb_popup_question_deletion = "Voulez-vous supprimer la ou les tâches sélectionnées ?"
glb_popup_title_merging = "Fusion"
glb_popup_question_merging = "Voulez-vous fusionner les tâches sélectionnées ?"
glb_popup_title_merging_error = "Fusion annulée"
glb_popup_text_merging_failed = "La durée totale excède {} heures.".format(str(int(glb_max_task_duration_in_sec/3600)))

# Last backup performed at
glb_last_backup_performed_at = "Dernière sauvegarde effectuée à"

# Variables related to the status bar
glb_status_bar_latest_backup = ""
glb_working_time_duration = "Durée travaillée"
glb_day = "jour"
glb_days = "jours"
glb_no_time_duration = "nulle"

# --------------------------------------------------- #
# Main window global variables (current row contents)
# --------------------------------------------------- #

z_curr_row = 0
z_curr_task_dth = ""
z_curr_task_duration = ""
z_curr_task_description = ""

# ------------------------------------------- #
# Popup menu actions
# ------------------------------------------- #

# Creating a separator
actionSeparator = QAction()
actionSeparator.setSeparator(True)

# Creating a bold font object
bold_font = QFont()
bold_font.setBold(True)

# Creating the actions with their texts
actionActivate = QAction(glb_actionActivate_text, None)
actionEdit = QAction(glb_actionEdit_text, None)
actionMerge = QAction(glb_actionMerge_text, None)
actionDelete = QAction(glb_actionDelete_text, None)
actionDeleteAll = QAction(glb_actionDeleteAll_text, None)

# Changing the activate text action to bold
actionActivate.setFont(bold_font)

# Adding the actions in the order wanted (no matter if they are visible or not)
ptt_main_dlg.lst_tasks.addAction(actionActivate)
ptt_main_dlg.lst_tasks.addAction(actionEdit)
ptt_main_dlg.lst_tasks.addAction(actionMerge)
ptt_main_dlg.lst_tasks.addAction(actionSeparator)
ptt_main_dlg.lst_tasks.addAction(actionDelete)
ptt_main_dlg.lst_tasks.addAction(actionDeleteAll)


# ----------------------------------------------- #
# Functions used for pseudo-mutex locking the app
# ----------------------------------------------- #

# Function check_ptt_lock_existence : checks if the ptt.lock file exists and returns a boolean and the 1st line found
def check_ptt_lock_existence():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()
    w_file_exists = False
    w_first_line = ""

    # Checking if the ptt.lock file can be found and retrieving 1st line of the file
    # Note : .rstrip() was added to remove the extra control characters at the end of the line

    try:
        with open(w_ptt_files.ptt_lock, "r") as file:
            w_file_exists = True
            w_first_line = file.readline().rstrip()
    except:
        print("check_ptt_lock_existence : file '{}' not found".format(w_ptt_files.ptt_lock))

    # Returning the file existence boolean and the string of the 1st line
    return w_file_exists, w_first_line


# Function write_ptt_lock : creates or overwrites the ptt.lock file
def write_ptt_lock():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()

    # Trying to overwrite the file with a timestamp
    try:
        with open(w_ptt_files.ptt_lock, "w") as file:
            file.write(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    except:
        print("write_ptt_lock : cannot write in the '{}' file".format(w_ptt_files.ptt_lock))


# Function remove_ptt_lock : removes the ptt.lock file
def remove_ptt_lock():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()

    # Trying to remove the file
    try:
        os.remove(w_ptt_files.ptt_lock)
    except:
        print("remove_ptt_lock : cannot remove the '{}' file".format(w_ptt_files.ptt_lock))


# Function ptt_start_allowed : checking if ptt is allowed to start with the help of ptt.lock
def ptt_start_allowed():

    # ----------------------------------------------------------------------------------- #
    # Important note :
    # ----------------------------------------------------------------------------------- #
    # We are allowed to run ptt if the timestamp (format %Y%m%d%H%M%S = YYYYMMDDHHMMSS)
    # found ptt.lock is older than 1 minute ago.
    # If the file doesn't exist or if the file contains crap, it's considered as invalid
    # and which means we can overwrite it with the current timestamp.
    # Note that the ptt.lock file is updated every 30 seconds with the help of a timer,
    # placed in another part of the code.
    # PS : Windows/DOS doesn't allow to really lock files like it's done in Unix/Posix...
    # ----------------------------------------------------------------------------------- #

    # Miscellaneous initializations
    w_ptt_files = PttFiles()
    w_ptt_start_allowed = False
    w_datetime_is_valid = False
    w_calculation_is_valid = False

    # Checking if the file is found and its contents
    w_file_exists, w_first_line = check_ptt_lock_existence()

    # If found...
    if w_file_exists is True:

        # Retrieving the 1st line which contains a timestamp
        try:
            w_datetime_in_file = datetime.datetime.strptime(w_first_line, "%Y%m%d%H%M%S")
            w_datetime_is_valid = True
        except:
            print("ptt_start_allowed : invalid data '{}' found in '{}' file".format(w_first_line, w_ptt_files.ptt_lock))

        # If the datetime found is OK...
        if w_datetime_is_valid is True:

            # Retrieving the current datetime in the format we need
            w_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            w_current_datetime = datetime.datetime.strptime(w_now, "%Y%m%d%H%M%S")

            # Trying to calculate the datetime difference between the current and the file one
            try:
                w_datetime_difference = w_current_datetime - w_datetime_in_file
                w_calculation_is_valid = True
            except:
                print("ptt_start_allowed : cannot calculate the datetime difference !")

            # If the calculation is OK and if we have at least a difference of 60 seconds, we can grant the access
            # Note : the tests 1) difference in days != 0 and 2) abs() are here to strengthen the test, just in case
            # there would be a gap of days or if a "future" datetime would be found in the file (= aka a "troll value")

            if w_calculation_is_valid is True:
                if w_datetime_difference.days != 0 or \
                        (w_datetime_difference.days == 0 and abs(w_datetime_difference.seconds) >= 60):
                    w_ptt_start_allowed = True

        else:
            # Otherwise, if the data isn't valid, we force the access anyway
            w_ptt_start_allowed = True

    else:
        # Otherwise, it means everything is clear and we can grant the access
        w_ptt_start_allowed = True

    # If we are allowed to start ptt, we can create/overwrite the "lock" file
    if w_ptt_start_allowed is True:
        write_ptt_lock()

    # Returning the boolean
    return w_ptt_start_allowed


# ------------------------------------------- #
# Functions of ptt_main window
# ------------------------------------------- #

# Function update_status_bar_message : displays the text received in parameter
def update_status_bar_message(p_message: str):
    ptt_main_dlg.ptt_statusbar.showMessage(p_message)


# Function update_status_bar_latest_backup : generates and updates the status bar with "Last backup performed at HH:MM."
def update_status_bar_latest_backup():

    # Retrieving the numbers of row currently selected
    w_nbr_rows_selected = len(ptt_main_dlg.lst_tasks.selectionModel().selectedRows())

    # Declaring glb_status_bar_latest_backup as global since we will update its contents
    global glb_status_bar_latest_backup

    # Generating the backup message
    glb_status_bar_latest_backup = glb_last_backup_performed_at + " " + datetime.datetime.now().strftime("%H:%M.")

    # We only update the status bar with the latest backup message if there are less than 2 rows selected
    # (= maybe the user wants to know the sum of the working duration only, so we don't loose the current status)
    # Otherwise, we refresh the duration of the selected tasks

    if w_nbr_rows_selected < 2:
        update_status_bar_message(glb_status_bar_latest_backup)
    else:
        update_status_bar_selected_tasks_duration()


# Function display_status_bar_latest_backup : displays the latest backup message performed in the status bar
def display_status_bar_latest_backup():
    update_status_bar_message(glb_status_bar_latest_backup)


# Function update_status_bar_selected_tasks_duration : generates and displays the working time of the selected tasks
def update_status_bar_selected_tasks_duration():

    # Miscellaneous initializations
    w_message = glb_working_time_duration + " :"
    w_txt_days = ""
    w_txt_hours = ""
    w_txt_mins = ""
    w_txt_secs = ""

    # Retrieving the selected tasks working duration in seconds in converting them into a class
    w_dhms = convert_task_duration_secs_to_dhms(sum_selected_tasks_duration(), glb_max_task_duration_in_sec)

    # Generating the "days" part of the text we need (with singular and plural)
    if w_dhms.days > 0:
        if w_dhms.days == 1:
            w_txt_days = "{} {}".format(w_dhms.days, glb_day)
        else:
            w_txt_days = "{} {}".format(w_dhms.days, glb_days)

    # Generating the "hours" part of the text we need
    if w_dhms.hours > 0:
        w_txt_hours = "{}h".format(w_dhms.hours)

    # Generating the "minutes" part of the text we need
    if w_dhms.minutes > 0:
        w_txt_mins = "{}min".format(w_dhms.minutes)

    # Generating the "seconds" part of the text we need
    if w_dhms.seconds > 0:
        w_txt_secs = "{}s".format(w_dhms.seconds)

    # Assembling the final message...
    if w_txt_days != "":
        w_message = w_message + " " + w_txt_days

    if w_txt_hours != "":
        w_message = w_message + " " + w_txt_hours

    if w_txt_mins != "":
        w_message = w_message + " " + w_txt_mins

    if w_txt_secs != "":
        w_message = w_message + " " + w_txt_secs

    # If we have no time duration, we need to say it
    if w_txt_days == "" and w_txt_hours == "" and w_txt_mins == "" and w_txt_secs == "":
        w_message = w_message + " " + glb_no_time_duration

    # Completing the sentence with a period
    w_message = w_message + "."

    # Finally, updating the status bar with the generated message
    update_status_bar_message(w_message)


# Function default_focus : puts the focus back on the entry input field
def default_focus():

    # Deselecting the task(s) and placing the focus back to the "task to add" text field
    ptt_main_dlg.lst_tasks.clearSelection()
    ptt_main_dlg.z_task_to_add.setFocus()


# Function error_popup_ok : generic display of an error popup with OK button
def error_popup_ok(p_popup_title: str, p_popup_text: str):

    # Creating a new message box with the application icon
    w_popup = QMessageBox()
    w_popup.setWindowIcon(QtGui.QIcon(ptt_resources.ptt_ico))

    # Setting up the critical icon
    w_popup.setIcon(QMessageBox.Critical)

    # Filling the title and the text and loading the OK standard button
    w_popup.setWindowTitle(p_popup_title)
    w_popup.setText(p_popup_text)
    w_popup.setStandardButtons(QMessageBox.Ok)

    # Displaying the message box
    w_popup.exec_()


# Function info_popup_ok : generic display of an info popup with OK button (french or default language)
def info_popup_ok(p_popup_title: str, p_popup_text: str):

    # Creating a new message box with the application icon
    w_popup = QMessageBox()
    w_popup.setWindowIcon(QtGui.QIcon(ptt_resources.ptt_ico))

    # Setting up the critical icon
    w_popup.setIcon(QMessageBox.Information)

    # Filling the title and the text and loading the OK standard button
    w_popup.setWindowTitle(p_popup_title)
    w_popup.setText(p_popup_text)
    w_popup.setStandardButtons(QMessageBox.Ok)

    # Displaying the message box
    w_popup.exec_()


# Function warning_popup_yes_no : generic display of a warning popup with yes/no choice (french or default language)
def warning_popup_yes_no(p_popup_title: str, p_popup_question: str):

    # Miscellaneous initializations
    p_btn_yes_pushed = False

    # Creating a new message box with the application icon
    w_popup = QMessageBox()
    w_popup.setWindowIcon(QtGui.QIcon(ptt_resources.ptt_ico))

    # Setting up the warning icon
    w_popup.setIcon(QMessageBox.Warning)

    # Filling the title and the question and loading the Yes/No standard buttons
    w_popup.setWindowTitle(p_popup_title)
    w_popup.setText(p_popup_question)
    w_popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    # Setting the value we need to intercept when Yes button is pushed
    # PS : no need to use anymore btn_yes.setText to change the text of the buttons when using translators
    btn_yes = w_popup.button(QMessageBox.Yes)

    # Displaying the message box
    w_popup.exec_()

    # Button Yes was pushed
    if w_popup.clickedButton() == btn_yes:
        p_btn_yes_pushed = True

    # Returning the value
    return p_btn_yes_pushed


# Function change_active_task : turns an existing task at p_row into the active one (alias the "1st row", row(0))
def change_active_task(p_row: int, p_column: int):

    # Note : no use yet for p_column
    # The parameter is kept cause it is sent by a signal which requires 2 parameters (like double clicking)

    # Making sure we have some rows at least...
    if ptt_main_dlg.lst_tasks.rowCount() > 0:

        # Restarting the global active task timer (only if we activate a task which is not the already activated one)
        if p_row > 0:
            glb_active_task_timer.start(glb_timer_interval_in_msec)

        # Retrieving the text of the 3 cells from the selected line
        w_cell0_selected, w_cell1_selected, w_cell2_selected = get_lst_tasks_row_cells(p_row)

        # If the task to be activated is not at row 0, inserting a new row at the top of the list
        if p_row > 0:
            ptt_main_dlg.lst_tasks.insertRow(0)

        # Fix to avoid the "yellow background" to be applied on the 2nd row (row 1) when inserting a new row
        if ptt_main_dlg.lst_tasks.rowCount() > 1:
            w_cell0_row1, w_cell1_row1, w_cell2_row1 = get_lst_tasks_row_cells(1)
            update_lst_tasks_row_cells(1, w_cell0_row1, w_cell1_row1, w_cell2_row1)

        # Updating the cells contents after creating the new row
        update_lst_tasks_row_cells(0, w_cell0_selected, w_cell1_selected, w_cell2_selected)

        # If the task to be activated is not at row 0, removing the original row at (row + 1)
        if p_row > 0:
            ptt_main_dlg.lst_tasks.removeRow(p_row + 1)

        # Replacing the focus at the top
        default_focus()

    # Saving my tasks on disk
    save_tasks_to_file()


# Function empty_lst_tasks : removes all rows by setting the counter of the lst_tasks to 0
def empty_lst_tasks():

    # Asking with a popup to confirm the deletion
    w_choice_confirmed = warning_popup_yes_no(glb_popup_title_all_tasks_deletion, glb_popup_question_all_tasks_deletion)

    # If confirming the deletion and if having some rows in the list
    if w_choice_confirmed is True:

        # Easiest way to destroy all rows and their attached items
        ptt_main_dlg.lst_tasks.setRowCount(0)

        # Showing/hiding the delete all action in the context menu
        show_action_delete_all()

        # Saving my tasks on disk
        save_tasks_to_file()


# Function get_lst_tasks_row_cells : retrieves the text of each cells from a row of the lst_tasks list
def get_lst_tasks_row_cells(p_row: int):

    # Miscellaneous initializations
    p_cell0_text = ""
    p_cell1_text = ""
    p_cell2_text = ""

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Retrieves each text
    if w_nbr_rows > 0:
        p_cell0_text = ptt_main_dlg.lst_tasks.item(p_row, 0).text()
        p_cell1_text = ptt_main_dlg.lst_tasks.item(p_row, 1).text()
        p_cell2_text = ptt_main_dlg.lst_tasks.item(p_row, 2).text()

    # Returning the values
    return p_cell0_text, p_cell1_text, p_cell2_text


# Function update_lst_tasks_row_cells : updates the text in each cell of a specified row
def update_lst_tasks_row_cells(p_row: int, p_cell0_text: str, p_cell1_text: str, p_cell2_text: str):

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Turning the texts received into QTableWidgetItem objects
        w_cell0_qtwi = QTableWidgetItem(p_cell0_text)
        w_cell1_qtwi = QTableWidgetItem(p_cell1_text)
        w_cell2_qtwi = QTableWidgetItem(p_cell2_text)

        # The 2 first cells contains text centered
        w_cell0_qtwi.setTextAlignment(QtCore.Qt.AlignCenter)
        w_cell1_qtwi.setTextAlignment(QtCore.Qt.AlignCenter)

        # If the row is 0, the 1st displayed row, the background of the cells is set to yellow color
        if p_row == 0:
            w_cell0_qtwi.setBackground(QtGui.QColor(255, 255, 0))
            w_cell1_qtwi.setBackground(QtGui.QColor(255, 255, 0))
            w_cell2_qtwi.setBackground(QtGui.QColor(255, 255, 0))

        # Putting the cells contents in the row
        ptt_main_dlg.lst_tasks.setItem(p_row, 0, QTableWidgetItem(w_cell0_qtwi))
        ptt_main_dlg.lst_tasks.setItem(p_row, 1, QTableWidgetItem(w_cell1_qtwi))
        ptt_main_dlg.lst_tasks.setItem(p_row, 2, QTableWidgetItem(w_cell2_qtwi))


# Function add_new_task : adds a new task with the text received
def add_new_task(p_text_task: str):

    # The text must be filled to add a new entry
    if p_text_task != "":

        # Getting the current datetime and formatting it
        w_now_dth = QtCore.QDateTime.currentDateTime()
        w_now_dth_string = w_now_dth.toString(glb_dd_MM_yyyy_hh_mm_string_format)

        # Inserting a new task at the 1st row of the list
        ptt_main_dlg.lst_tasks.insertRow(0)

        # Filling the text in each cells of the new row
        update_lst_tasks_row_cells(0, w_now_dth_string, glb_00_00_time, p_text_task)

        # Setting to blank the entry text
        ptt_main_dlg.z_task_to_add.setText("")

        # Turning the new task added into the active one
        change_active_task(0, 0)

        # Showing/hiding the delete all action in the context menu
        show_action_delete_all()


# Function enable_btn_task_add : enables or disables the button to add a task depending if z_task_to_add is filled
def enable_btn_task_add():
    if ptt_main_dlg.z_task_to_add.text() == "":
        ptt_main_dlg.btn_task_add.setEnabled(False)
    else:
        ptt_main_dlg.btn_task_add.setEnabled(True)


# Function show_action_delete_all : show/hide the actionDeleteAll in the context menu if there is at least 1 row
def show_action_delete_all():

    # Showing + displaying the action in the right context menu, otherwise, hiding it and forcing to no context menu
    if ptt_main_dlg.lst_tasks.rowCount() > 0:
        ptt_main_dlg.lst_tasks.setContextMenuPolicy(Qt.ActionsContextMenu)
        actionDeleteAll.setVisible(True)
    else:
        ptt_main_dlg.lst_tasks.setContextMenuPolicy(Qt.NoContextMenu)
        actionDeleteAll.setVisible(False)


# Function delete_selected_tasks : deletes all the selected tasks in the lst_tasks list
def delete_selected_tasks():

    # Asking with a popup to confirm the deletion
    w_choice_confirmed = warning_popup_yes_no(glb_popup_title_deletion, glb_popup_question_deletion)

    # Temporary list for deletions
    lst_rows_to_delete = []

    # Making sure we have some rows at least...
    nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # If confirming the deletion and if having some rows in the list
    if (w_choice_confirmed is True) and nbr_rows > 0:

        # Memorizing the rows to delete in a list
        # Reason : removing rows selected in a loop leads to delete wrong elements if more than 1...

        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in sorted(indexes):
            lst_rows_to_delete.append(index.row())

        # Sorting the list in order to get reversed sorting (to avoid loosing the index if ascendant deletion !)
        lst_rows_to_delete.sort(reverse=True)

        # Deleting the rows in the lst_tasks list with the row number of the temporary list
        for row_to_delete in lst_rows_to_delete:
            ptt_main_dlg.lst_tasks.removeRow(row_to_delete)

        # Forcing the 1st displayed row to become the active task
        change_active_task(0, 0)

        # Showing/hiding the delete all action in the context menu
        show_action_delete_all()


# Function add_duration_to_task_at_row : adds a duration to the task duration found at the row received
def add_duration_to_task_at_row(p_row: int, p_duration_to_add_in_secs: int):

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Retrieving the text of the 3 cells from the selected line (any row but fixed columns values)
        w_cell0_text, w_cell1_text, w_cell2_text = get_lst_tasks_row_cells(p_row)

        # Turning the text of cell1 in 'hh:mm' format into true Qtime format
        w_qt_task_duration = QtCore.QTime.fromString(w_cell1_text, glb_hh_mm_string_format)

        # Converting the Qtime into seconds (seconds from 00:00:00 to the Qtime value :p )
        w_task_duration_in_secs = QtCore.QTime(0, 0, 0).secsTo(w_qt_task_duration)

        # Checking if the task duration already exceeds the max task duration
        if w_task_duration_in_secs > glb_max_task_duration_in_sec:

            # If yes, we create a new task and add the duration
            add_new_task(w_cell2_text)
            add_duration_to_task_at_row(0, p_duration_to_add_in_secs)

        else:

            # Checking if we can add the duration to the existing task without going over the max task duration
            # If yes, updating the row to the max task duration and creating a new task
            # Else, we update like usual the row adding the duration received in parameter

            if (w_task_duration_in_secs + p_duration_to_add_in_secs) > glb_max_task_duration_in_sec:

                # Calculating the filler and remains value (filler is added to task, remains is for the new task)
                w_filler_in_secs = glb_max_task_duration_in_sec - w_task_duration_in_secs
                w_remains_in_secs = p_duration_to_add_in_secs - w_filler_in_secs

                # Updating the row adding the filler duration to max out the task duration
                w_task_duration = w_qt_task_duration.addSecs(w_filler_in_secs)
                w_cell1_text = w_task_duration.toString(glb_hh_mm_string_format)
                update_lst_tasks_row_cells(p_row, w_cell0_text, w_cell1_text, w_cell2_text)

                # Creating a new task with the remains in secs
                add_new_task(w_cell2_text)
                add_duration_to_task_at_row(0, w_remains_in_secs)

            else:

                # Adding the duration received to the current task duration
                w_task_duration = w_qt_task_duration.addSecs(p_duration_to_add_in_secs)

                # Turning the task duration back to string in 'hh:mm' format
                w_cell1_text = w_task_duration.toString(glb_hh_mm_string_format)

                # Putting back the row with the updated task duration
                update_lst_tasks_row_cells(p_row, w_cell0_text, w_cell1_text, w_cell2_text)

    # Saving my tasks on disk
    save_tasks_to_file()


# Function auto_increment_active_task : increments the duration of the current active task by XX seconds
def auto_increment_active_task():

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Creating a default task when none are found to avoid loosing the logged time
    if w_nbr_rows == 0:
        add_new_task(glb_default_task_name)

    # Adding XX seconds to the duration in the active task at row(0)
    add_duration_to_task_at_row(0, glb_default_added_duration_in_sec)


# Function sum_selected_tasks_duration : sums up the selected tasks duration and returns a result in secs
def sum_selected_tasks_duration():

    # Miscellaneous initializations
    w_selected_task_duration_in_secs = 0

    # Temporary list of tasks selected (tuples of (row, text0, text1, text2) )
    lst_selected_tasks = []

    # Making sure we have some rows at least...
    nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # If having some rows in the list
    if nbr_rows > 0:

        # Memorizing the selected tasks in a list
        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in sorted(indexes):

            # Retrieving the text of the 3 cells from the selected line (any row but fixed columns values)
            w_cell0_text, w_cell1_text, w_cell2_text = get_lst_tasks_row_cells(index.row())

            # Saving the tuple in the list
            lst_selected_tasks.append((index.row(), w_cell0_text, w_cell1_text, w_cell2_text))

        # Calculating the total duration in seconds for the selected tasks
        for w_row, w_text0, w_text1, w_text2 in lst_selected_tasks:

            # Turning the text of cell1 in 'hh:mm' format into true Qtime format
            w_qt_task_duration = QtCore.QTime.fromString(w_text1, glb_hh_mm_string_format)

            # Converting the Qtime into seconds (seconds from 00:00:00 to the Qtime value :p )
            w_task_duration_in_secs = QtCore.QTime(0, 0, 0).secsTo(w_qt_task_duration)

            # Adding the duration read to the total task duration
            w_selected_task_duration_in_secs = w_selected_task_duration_in_secs + w_task_duration_in_secs

        # Finally returning the duration
        return w_selected_task_duration_in_secs


# Function enable_lst_tasks_popup_actions : makes actions visible or not for the lst_tasks list
def enable_lst_tasks_popup_actions():

    # We need to check if we have tasks in the list before
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Hiding all actions by default
    actionActivate.setVisible(False)
    actionEdit.setVisible(False)
    actionMerge.setVisible(False)
    actionDelete.setVisible(False)
    actionDeleteAll.setVisible(False)

    # /!\ ContextMenuPolicy is set to None by default
    # -> Trick to avoid the "ghostly" square to be displayed with no option, when no row selected looking like this -> °

    ptt_main_dlg.lst_tasks.setContextMenuPolicy(Qt.NoContextMenu)

    # There must be at least some rows to display the actions
    if w_nbr_rows > 0:

        # Miscellaneous initializations
        w_nbr_rows_selected = 0
        w_last_index_selected = 0

        # Checking how many selected rows we have, counting them and saving the last index
        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in sorted(indexes):
            w_nbr_rows_selected = w_nbr_rows_selected + 1
            w_last_index_selected = index.row()

        # Setting the ContextMenuPolicy up if we have at least 1 row (because of the "delete all" option)
        ptt_main_dlg.lst_tasks.setContextMenuPolicy(Qt.ActionsContextMenu)

        # actionActivate is visible if only one row is selected and it can't be the row 0
        if w_nbr_rows_selected == 1 and w_last_index_selected > 0:
            actionActivate.setVisible(True)

        # actionEdit is visible if only one row is selected
        if w_nbr_rows_selected == 1:
            actionEdit.setVisible(True)

        # actionMerge is visible if at least 2 rows are selected
        if w_nbr_rows_selected > 1:
            actionMerge.setVisible(True)

        # actionDelete is visible if at least one row is selected
        if w_nbr_rows_selected > 0:
            actionDelete.setVisible(True)

        # actionDeleteAll is visible as long there are rows in the list
        actionDeleteAll.setVisible(True)

        # Depending on the rows selected, we display either the duration of the tasks selected or the latest backup time
        if w_nbr_rows_selected > 1:
            update_status_bar_selected_tasks_duration()
        else:
            display_status_bar_latest_backup()


# Function popup_change_active_task : activates a task through the appropriate popup action
def popup_change_active_task():

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Normally, the action is only reachable if one task is selected... so it should be enough
        # It's a fake loop in order to get the 1st selected row

        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in indexes:
            change_active_task(index.row(), 0)


# Function merge_selected_tasks : merges all the selected tasks in the lst_tasks list
def merge_selected_tasks():

    # Miscellaneous initializations
    w_total_duration_in_secs = 0
    w_nbr_of_tasks_to_delete = 0

    # Asking with a popup to confirm the merge
    w_choice_confirmed = warning_popup_yes_no(glb_popup_title_merging, glb_popup_question_merging)

    # Temporary list for merging (tuples of (row, text0, text1, text2) )
    lst_rows_to_merge = []

    # Making sure we have some rows at least...
    nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # If confirming the merge and if having some rows in the list
    if (w_choice_confirmed is True) and nbr_rows > 0:

        # Memorizing the rows (and their data) to merge, in a list
        # Reason : removing rows selected in a loop leads to delete wrong elements if more than 1...

        # Reading selected rows
        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in sorted(indexes):

            # Retrieving the text of the 3 cells from the selected line (any row but fixed columns values)
            w_cell0_text, w_cell1_text, w_cell2_text = get_lst_tasks_row_cells(index.row())

            # Saving the tuple in the list for the rows to merge
            lst_rows_to_merge.append((index.row(), w_cell0_text, w_cell1_text, w_cell2_text))

        # Sorting the list in order to get reversed sorting (to avoid loosing the index if ascendant deletion !)
        lst_rows_to_merge.sort(reverse=True)

        # Calculating the total duration in seconds for the merged tasks
        for w_row, w_text0, w_text1, w_text2 in lst_rows_to_merge:

            # Turning the text of cell1 in 'hh:mm' format into true Qtime format
            w_qt_task_duration = QtCore.QTime.fromString(w_text1, glb_hh_mm_string_format)

            # Converting the Qtime into seconds (seconds from 00:00:00 to the Qtime value :p )
            w_task_duration_in_secs = QtCore.QTime(0, 0, 0).secsTo(w_qt_task_duration)

            # Adding the duration read to the total task duration
            w_total_duration_in_secs = w_total_duration_in_secs + w_task_duration_in_secs

        # The merge is aborted if the total duration of merged tasks exceeds the max task duration !
        if w_total_duration_in_secs > glb_max_task_duration_in_sec:

            # Error popup message
            error_popup_ok(glb_popup_title_merging_error, glb_popup_text_merging_failed)

        else:

            # Deleting the tasks and updating the "upper" one (since the list of merges is sorted etc...)
            w_nbr_of_rows_to_merge = len(lst_rows_to_merge)

            # Initializing the merged tasks "text collector"
            w_merged_text_collector = ""

            for w_row, w_text0, w_text1, w_text2 in lst_rows_to_merge:

                # Concatenation of the tasks descriptions which will be merged
                # The final text will look like "1st line of text\n+ 2nd line of text\n+ 3rd line etc..."

                # Strings with trailing whitespaces won't be concatenated to avoid "+\n +\n +\n " etc...
                if w_text2.rstrip() != "":
                    if w_merged_text_collector == "":
                        w_merged_text_collector = w_text2
                    else:
                        w_merged_text_collector = w_merged_text_collector + "\n+ " + w_text2

                # All tasks must be deleted MINUS one
                w_nbr_of_tasks_to_delete = w_nbr_of_tasks_to_delete + 1

                # Deleting all except the latest tasks (which will keep its own label actually)
                if w_nbr_of_tasks_to_delete < w_nbr_of_rows_to_merge:
                    ptt_main_dlg.lst_tasks.removeRow(w_row)
                else:
                    # Updating the remaining task with the total in seconds ("00:00" ->QTime ->+total in secs ->string)
                    w_qt_task_duration = QtCore.QTime.fromString(glb_00_00_time, glb_hh_mm_string_format)
                    w_task_duration = w_qt_task_duration.addSecs(w_total_duration_in_secs)
                    w_text1 = w_task_duration.toString(glb_hh_mm_string_format)
                    update_lst_tasks_row_cells(w_row, w_text0, w_text1, w_merged_text_collector)

            # Forcing the 1st displayed row to become the active task
            change_active_task(0, 0)


# Function read_current_task : reads the current task (actually just one) and gets the text in the globals z_ variables
def read_current_task():

    # Saying the variables used here are in the global scope, not local !
    global z_curr_row, z_curr_task_dth, z_curr_task_duration, z_curr_task_description

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        indexes = ptt_main_dlg.lst_tasks.selectionModel().selectedRows()
        for index in indexes:

            # Retrieving the text of the 3 cells from the selected line
            z_curr_task_dth, z_curr_task_duration, z_curr_task_description = get_lst_tasks_row_cells(index.row())

            # Retrieving current row number
            z_curr_row = index.row()


# Function call_ptt_edit_task : loads and displays the ptt_edit_task window
def call_ptt_edit_task():

    # Sending parameters to the edit window with a signal emitted
    ptt_main_calling_edit.edit_task_signal.emit(z_curr_row, z_curr_task_dth, z_curr_task_duration,
                                                z_curr_task_description)

    # Putting the focus on the 1st button
    ptt_edit_task_dlg.btn_1min.setFocus()

    # Hiding the txt_row_number label (contents the row number edited)
    ptt_edit_task_dlg.txt_row_number.hide()

    # Setting the "toggle" button to checked state
    ptt_edit_task_dlg.btn_plus_minus.setChecked(True)
    ptt_edit_task_dlg.btn_plus_minus.setText(glb_plus)

    # Initializing and running the edit window
    ptt_edit_task_dlg.show()
    ptt_edit_task_app.exec()

    # Centering the edit task window (on the screen where edit window screen is called)
    ptt_edit_task_center_window()

    # Replacing the focus at the top
    default_focus()


# Function update_task_after_edit : updates a task after it was edited and saved in the edit window
def update_task_after_edit(p_curr_row: int, p_curr_task_dth: str, p_curr_task_duration: str,
                           p_curr_task_description: str):

    # Updating the row contents in the list
    update_lst_tasks_row_cells(p_curr_row, p_curr_task_dth, p_curr_task_duration, p_curr_task_description)

    # Replacing the focus at the top
    default_focus()

    # Saving my tasks on disk
    save_tasks_to_file()


# Function save_tasks_to_file : saves my tasks to the "my_tasks.json" file
def save_tasks_to_file():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()
    w_tasks = {"tasks": []}

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        w_index = 0

        # Reading all the rows in the list
        while w_index < w_nbr_rows:

            # Retrieving each cells contents
            w_cell0_text, w_cell1_text, w_cell2_text = get_lst_tasks_row_cells(w_index)

            # Incrementing the index
            w_index = w_index + 1

            # Creating our task record
            w_task_record = {
                "started_on": w_cell0_text,
                "duration": w_cell1_text,
                "description": w_cell2_text}

            # Appending the record in the JSON array
            w_tasks["tasks"].append(w_task_record)

    # Trying to open in write mode the "my_tasks.json" then saving the data
    try:
        with open(w_ptt_files.my_tasks_json, "w") as file:

            # indent=4 for pretty json output, unicode and no \u characters
            json.dump(w_tasks, file, indent=4, ensure_ascii=False)

            # Updating the status bar message when the backup is performed
            update_status_bar_latest_backup()

    except IOError:
        # For console debugging
        print("save_tasks_to_file : cannot write in the '{}' file".format(w_ptt_files.my_tasks_json))


# Function load_tasks_from_file : loads my tasks to the "my_tasks.json" file
def load_tasks_from_file():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()
    w_tasks = {"tasks": []}

    # Trying to open "my_tasks.json" and loading the data in the w_tasks variable
    try:
        with open(w_ptt_files.my_tasks_json, 'r') as file:
            try:
                w_tasks = json.load(file)
            except:
                # For console debugging
                print("load_tasks_from_file : error while reading json data in '{}'".format(w_ptt_files.my_tasks_json))

    except IOError:
        # For console debugging
        print("load_tasks_from_file : cannot open the '{}' file".format(w_ptt_files.my_tasks_json))

    # For each task record found in w_tasks, loading retrieving the text
    for w_task_record in w_tasks["tasks"]:

        # Getting the numbers of rows and inserting a new one (at the row_count position = at the end)
        w_row_count = ptt_main_dlg.lst_tasks.rowCount()
        ptt_main_dlg.lst_tasks.insertRow(w_row_count)

        # Filling the text in each cells of the new row
        update_lst_tasks_row_cells(
            w_row_count, w_task_record["started_on"], w_task_record["duration"], w_task_record["description"])


# Function create_tasks_backup : creates a backup file of the "my_tasks.json" file
def create_tasks_backup():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()

    # Creating a backup of the file if it exists
    try:
        copyfile(w_ptt_files.my_tasks_json, w_ptt_files.my_tasks_backup)
    except FileNotFoundError:
        print("create_tasks_backup : file '{}' not found".format(w_ptt_files.my_tasks_json))


# ------------------------------------------- #
# Functions of ptt_edit_task window
# ------------------------------------------- #

# ptt_edit_task / Function ptt_edit_task_center_window : centers the edit task window on the right monitor
def ptt_edit_task_center_window():

    # Retrieving 1st the frame geometry of the edit task ptt window (in order to get the QRect class)
    w_edit_task_dlg_frame_geometry = ptt_edit_task_dlg.frameGeometry()

    # Retrieving the current cursor location to get the RIGHT screen number we need
    w_screen_number = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())

    # Retrieving the center point of the availableGeometry (= the actual screen geometry we can use, w/o task bar...)
    w_center_point = QtWidgets.QApplication.desktop().availableGeometry(w_screen_number).center()

    # Centering/moving the temp frame geometry based from the MAIN window to the center point
    w_edit_task_dlg_frame_geometry.moveCenter(w_center_point)

    # Finally moving the edit task location on the top left of the QRect placed in the middle of the right screen
    ptt_edit_task_dlg.move(w_edit_task_dlg_frame_geometry.topLeft())


# ptt_edit_task / Function ptt_edit_task_duration_reset : resets the duration value in the modal window
def ptt_edit_task_duration_reset():
    w_qt_reset = QtCore.QTime.fromString(glb_00_00_time, glb_hh_mm_string_format)
    ptt_edit_task_dlg.z_task_duration.setTime(w_qt_reset)


# ptt_edit_task / Function ptt_edit_task_add_duration : adds/subtracts the value sent by buttons to the duration field
def ptt_edit_task_add_duration(p_value_in_min: int):

    # Miscellaneous initializations
    w_multiplier = 1

    # Checking the state of the "toggle" button +/-. Note : if it's checked, it means "+".
    if ptt_edit_task_dlg.btn_plus_minus.isChecked() is False:
        w_multiplier = -1

    # For now, forcing min/max values for the duration (see globals at the top)
    ptt_edit_task_dlg.z_task_duration.setMinimumTime(glb_minimum_time_per_task)
    ptt_edit_task_dlg.z_task_duration.setMaximumTime(glb_maximum_time_per_task)

    # Adding / subtracting the duration to the field
    w_time = ptt_edit_task_dlg.z_task_duration.time()
    w_result = w_time.addSecs(w_multiplier*p_value_in_min*60)
    ptt_edit_task_dlg.z_task_duration.setTime(w_result)


# ptt_edit_task / Function ptt_edit_task_update_btn_plus_minus_text : changes the text of the +/- toggle button
def ptt_edit_task_update_btn_plus_minus_text():

    if ptt_edit_task_dlg.btn_plus_minus.isChecked() is True:
        ptt_edit_task_dlg.btn_plus_minus.setText(glb_plus)
    else:
        ptt_edit_task_dlg.btn_plus_minus.setText(glb_minus)


# ------------------------------------------- #
# Functions I/O for ptt_edit_task window
# ------------------------------------------- #

# ptt_edit_task / Function ptt_edit_task_get_data : gets signal parameters to initialize the edit window fields
def ptt_edit_task_get_data(p_curr_row: int, p_curr_task_dth: str, p_curr_task_duration: str, p_curr_task_description: str):

    # Getting the row number (hidden text field)
    ptt_edit_task_dlg.txt_row_number.setText(str(p_curr_row))

    # Getting the starting datetime
    w_qt_task_dth = QtCore.QDateTime.fromString(p_curr_task_dth, glb_dd_MM_yyyy_hh_mm_string_format)
    ptt_edit_task_dlg.z_task_dth.setDateTime(w_qt_task_dth)

    # Getting the task duration
    w_qt_duration = QtCore.QTime.fromString(p_curr_task_duration, glb_hh_mm_string_format)
    ptt_edit_task_dlg.z_task_duration.setTime(w_qt_duration)

    # Getting the task description
    ptt_edit_task_dlg.z_task_description.setPlainText(p_curr_task_description)


# ptt_edit_task / Function ptt_edit_task_send_data : sends signal parameters from the edit window fields to the main one
def ptt_edit_task_send_data():

    # Retrieving the row number (hidden text field)
    p_curr_row = int(ptt_edit_task_dlg.txt_row_number.text())

    # Retrieving the starting datetime
    w_qt_task_dth = ptt_edit_task_dlg.z_task_dth.dateTime()
    p_curr_task_dth = QtCore.QDateTime.toString(w_qt_task_dth, glb_dd_MM_yyyy_hh_mm_string_format)

    # Retrieving the task duration
    w_qt_duration = ptt_edit_task_dlg.z_task_duration.time()
    p_curr_task_duration = QtCore.QTime.toString(w_qt_duration, glb_hh_mm_string_format)

    # Retrieving the task description
    p_curr_task_description = ptt_edit_task_dlg.z_task_description.toPlainText()

    # Sending parameters to the main window with a signal emitted
    ptt_edit_task_saving.edit_task_signal.emit(p_curr_row, p_curr_task_dth, p_curr_task_duration,
                                               p_curr_task_description)

    # Closing the edit window
    ptt_edit_task_dlg.close()


# ------------------------------------------- #
# Checking if we can start PTT (pseudo mutex)
# ------------------------------------------- #

w_is_ptt_start_allowed = ptt_start_allowed()

# ------------------------------------------- #
# Main loop
# ------------------------------------------- #
if __name__ == "__main__" and (w_is_ptt_start_allowed is True):

    # Trying to create a backup of the "my_tasks.json" file (at application startup only)
    create_tasks_backup()

    # Forcing the list to accept the focus only with click
    # Reason : signals not working well with QTableWidget about selecting rows with the keyboard tabbing ! (= bug ?)
    ptt_main_dlg.lst_tasks.setFocusPolicy(Qt.ClickFocus)

    # Emptying the list of tasks
    ptt_main_dlg.lst_tasks.setRowCount(0)

    # Loading my tasks
    load_tasks_from_file()

    # Create a new task at startup
    add_new_task(glb_new_task_at_startup)

    # Showing/hiding the delete all action in the context menu
    show_action_delete_all()

    # Replacing the focus at the top
    default_focus()

    # Auto resize of columns
    ptt_main_dlg.lst_tasks.resizeColumnsToContents()

    # Refreshing the task button activation
    enable_btn_task_add()

    # Refreshing the actions of the popup menu of the list
    enable_lst_tasks_popup_actions()


# ------------------------------------------- #
# Signals and connections (ptt_main)
# ------------------------------------------- #

if w_is_ptt_start_allowed is True:

    # Enabling or not the button to add a task
    ptt_main_dlg.z_task_to_add.textChanged.connect(enable_btn_task_add)

    # Adding a new task to the lst_tasks list with the appropriate button
    ptt_main_dlg.btn_task_add.clicked.connect(lambda: add_new_task(ptt_main_dlg.z_task_to_add.text()))

    # Adding a new task to the lst_tasks list when Enter key is pressed
    ptt_main_dlg.z_task_to_add.returnPressed.connect(lambda: add_new_task(ptt_main_dlg.z_task_to_add.text()))

    # Turning a double clicked row as the active task on the 1st row
    ptt_main_dlg.lst_tasks.cellDoubleClicked.connect(change_active_task)

    # Reading the cells contents of a row selected and saves the info in the z_ global variables
    ptt_main_dlg.lst_tasks.cellPressed.connect(read_current_task)

    # Refreshing the popup actions of the list
    ptt_main_dlg.lst_tasks.itemSelectionChanged.connect(enable_lst_tasks_popup_actions)

    # Timer signal to manage the time logged on the active task
    glb_active_task_timer.timeout.connect(auto_increment_active_task)

    # Timer signal to manage the ptt.lock (works like a heartbeat)
    glb_ptt_lock_timer.timeout.connect(write_ptt_lock)

    # Popup / actionActivate : activating the task selected
    actionActivate.triggered.connect(popup_change_active_task)

    # Popup / actionEdit : editing the task (datetime started on, duration, description)
    actionEdit.triggered.connect(call_ptt_edit_task)

    # Popup / actionMerge : merging the selected tasks (so at least 2)
    actionMerge.triggered.connect(merge_selected_tasks)

    # Popup / actionDelete : deleting the selected tasks
    actionDelete.triggered.connect(delete_selected_tasks)

    # Popup / actionDeleteAll : empty the list/deletes ALL the tasks
    actionDeleteAll.triggered.connect(empty_lst_tasks)

    # Menu bar, menu PTT / actionQuit : closing the application
    ptt_main_dlg.actionQuit.triggered.connect(ptt_main_dlg.close)

    # Menu bar, menu PTT / actionAbout : display the "About" information popup
    ptt_main_dlg.actionAbout.triggered.connect(lambda: info_popup_ok(glb_about_title, glb_about_info))

# ------------------------------------------- #
# Signals and connections (ptt_edit_task)
# ------------------------------------------- #

if w_is_ptt_start_allowed is True:

    # Resetting the duration displayed in the ptt_edit_task modal window
    ptt_edit_task_dlg.btn_reset.clicked.connect(ptt_edit_task_duration_reset)

    # Adding duration to the QTimeEdit field
    ptt_edit_task_dlg.btn_1min.clicked.connect(lambda: ptt_edit_task_add_duration(1))
    ptt_edit_task_dlg.btn_5min.clicked.connect(lambda: ptt_edit_task_add_duration(5))
    ptt_edit_task_dlg.btn_15min.clicked.connect(lambda: ptt_edit_task_add_duration(15))
    ptt_edit_task_dlg.btn_30min.clicked.connect(lambda: ptt_edit_task_add_duration(30))
    ptt_edit_task_dlg.btn_1h.clicked.connect(lambda: ptt_edit_task_add_duration(60))
    ptt_edit_task_dlg.btn_2h.clicked.connect(lambda: ptt_edit_task_add_duration(120))
    ptt_edit_task_dlg.btn_4h.clicked.connect(lambda: ptt_edit_task_add_duration(240))
    ptt_edit_task_dlg.btn_8h.clicked.connect(lambda: ptt_edit_task_add_duration(480))

    # Changing the text of the toggle button "+/-"
    ptt_edit_task_dlg.btn_plus_minus.toggled.connect(lambda: ptt_edit_task_update_btn_plus_minus_text())

    # Navigation management between ptt_main <-> ptt_edit_task (calls, I/O parameters...)
    ptt_main_calling_edit.edit_task_signal.connect(ptt_edit_task_get_data)
    ptt_edit_task_dlg.btn_save.clicked.connect(ptt_edit_task_send_data)
    ptt_edit_task_saving.edit_task_signal.connect(update_task_after_edit)

# ------------------------------------------- #
# Initializing and running the main window
# ------------------------------------------- #

if w_is_ptt_start_allowed is True:

    # Installing translators
    # Weird behaviour : for some strange reason, i can't seem to use installTranslator on a QtWidgets.QApplication
    # INSIDE a function, even through an entry parameter or access/alter the QtWidgets.QApplication through "Global" !
    # -> for now, i will just return the translator and install it here...

    w_ptt_main_translator = ptt_load_translators()
    ptt_main_app.installTranslator(w_ptt_main_translator)

    # Initializing and running the main window
    ptt_main_dlg.show()
    ptt_main_app.exec()

    # Removing the ptt.lock file
    # Note : even if the file isn't removed (ex: app crash), it becomes obsolete if not refreshed within 1 min

    remove_ptt_lock()

else:
    # The application is already running
    error_popup_ok(glb_popup_title_generic_error, glb_popup_text_app_is_already_running)
