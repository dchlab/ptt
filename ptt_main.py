#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* --------------------------------------------------------------------------------- *
* Application name : PTT (Python Time Tracker)
* Created by DCH (June / December 2019)
* --------------------------------------------------------------------------------- *
* Modified by XXX on the DD/MM/YYYY
* --------------------------------------------------------------------------------- *
* Notes :
* - Requires PyQT5 to run and be compiled
* - Note that the .ui files are loaded dynamically (for now)
* --------------------------------------------------------------------------------- *
* Source files required :
* - ptt_main.py
* - ptt_info.py
* Resources and UI files required :
* - /ui/ptt_main.ui
* - /ui/ptt_edit_task.ui
* - /ui/ptt.ico
* User data files used :
* - /data/my_tasks.json
* - /data/my_tasks.backup
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


# ------------------------------------------- #
# Miscellaneous / Specific functions
# ------------------------------------------- #

# Function ptt_resource_path : get absolute path to resource, works for dev and for PyInstaller (if files added in .exe)
def ptt_resource_path(p_relative_path: str):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        w_base_path = sys._MEIPASS
    except:
        w_base_path = os.path.abspath(".")

    return os.path.join(w_base_path, p_relative_path)


# ------------------------------------------- #
# Main window (ptt_main)
# ------------------------------------------- #

ptt_main_ui_path = ptt_resource_path("ui/ptt_main.ui")
ptt_main_app = QtWidgets.QApplication([])
ptt_main_dlg = uic.loadUi(ptt_main_ui_path)

# ------------------------------------------- #
# Edit task window (ptt_edit_task)
# ------------------------------------------- #

ptt_edit_task_ui_path = ptt_resource_path("ui/ptt_edit_task.ui")
ptt_edit_task_app = QtWidgets.QApplication([])
ptt_edit_task_dlg = uic.loadUi(ptt_edit_task_ui_path)

# ------------------------------------------- #
# Global variables
# ------------------------------------------- #

# Retrieve external application information
glb_ptt_app_info = PttAppInfo()

# Global variables for intervals and others duration
glb_timer_interval_in_msec = 60000
glb_default_added_duration_in_sec = 60
glb_max_task_duration_in_sec = 28800

# Active task timer management
glb_active_task_timer = QtCore.QTimer()
glb_active_task_timer.start(glb_timer_interval_in_msec)

# Empty string
glb_empty_str = ""

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

# Default task name for the task automatically created, if none was found
glb_default_task_name = "Tâche créée automatiquement"

# Popup actions text displayed
glb_actionActivate_text = "Activer"
glb_actionEdit_text = "Modifier"
glb_actionMerge_text = "Fusionner"
glb_actionDelete_text = "Supprimer"

# Texts for the "About" popup
glb_about_title = "A propos de PTT"
glb_about_info = "PTT - Python Time Tracker\nVersion : {}\n\nAuteur : {}\nGithub : {}\n\nLibrairie(s) utilisée(s) : {}"\
    .format(glb_ptt_app_info.version, glb_ptt_app_info.author, glb_ptt_app_info.github, glb_ptt_app_info.dependencies)

# Locale for french language/country
glb_locale_fr_FR = "fr_FR"

# Miscellaneous texts (for message boxes etc...)
glb_popup_title_all_tasks_deletion = "ATTENTION !"
glb_popup_question_all_tasks_deletion = "Voulez-vous supprimer TOUTES les tâches ?"
glb_popup_title_deletion = "Suppression"
glb_popup_question_deletion = "Voulez-vous supprimer la ou les tâches sélectionnées ?"
glb_popup_title_merging = "Fusion"
glb_popup_question_merging = "Voulez-vous fusionner les tâches sélectionnées ?"
glb_popup_title_merging_error = "Fusion annulée"
glb_popup_text_merging_failed = "La durée totale excède {} heures.".format(str(int(glb_max_task_duration_in_sec/3600)))
glb_Yes_text = "Oui"
glb_No_text = "Non"
glb_Ok_text = "OK"

# ------------------------------------------- #
# Main window global variables (cells read)
# ------------------------------------------- #

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

# Changing the activate text action to bold
actionActivate.setFont(bold_font)

# Adding the actions in the order wanted (no matter if they are visible or not)
ptt_main_dlg.lst_tasks.addAction(actionActivate)
ptt_main_dlg.lst_tasks.addAction(actionEdit)
ptt_main_dlg.lst_tasks.addAction(actionMerge)
ptt_main_dlg.lst_tasks.addAction(actionSeparator)
ptt_main_dlg.lst_tasks.addAction(actionDelete)


# ------------------------------------------- #
# Classes
# ------------------------------------------- #

# Class PttFiles : contents the file names used in the application
class PttFiles:
    def __init__(self):
        self.my_tasks_json = "data/my_tasks.json"
        self.my_tasks_backup = "data/my_tasks.backup"


# Object for edit_task_signal calling parameters between windows
class PttEditObject(QObject):
    edit_task_signal = QtCore.pyqtSignal(int, str, str, str)


# Classes initializations
ptt_main_calling_edit = PttEditObject()
ptt_edit_task_saving = PttEditObject()


# ------------------------------------------- #
# Functions of ptt_main window
# ------------------------------------------- #

# Function default_focus : puts focus back on the entry input field
def default_focus():

    # Clearing the selected/clicked task and placing the focus back to the "task to add" text field
    ptt_main_dlg.lst_tasks.clearSelection()
    ptt_main_dlg.z_task_to_add.setFocus()


# Function error_popup_ok : generic display of an error popup with OK button (french or default language)
def error_popup_ok(p_popup_title: str, p_popup_text: str):

    # Retrieving the locale system value
    w_locale = QtCore.QLocale.system().name()

    # Creating a new message box
    w_popup = QMessageBox()

    # If the locale says it's french and french UI
    if w_locale == glb_locale_fr_FR:

        # Setting up the critical icon
        w_popup.setIcon(QMessageBox.Critical)

        # Filling the title and the text and loading the OK standard button
        w_popup.setWindowTitle(p_popup_title)
        w_popup.setText(p_popup_text)
        w_popup.setStandardButtons(QMessageBox.Ok)

        # Changing the text of the standard buttons
        btn_ok = w_popup.button(QMessageBox.Ok)
        btn_ok.setText(glb_Ok_text)

        # Displaying the message box
        w_popup.exec_()

    else:
        # Else, if it's not french, displaying the error popup directly...
        w_popup.critical(None, p_popup_title, p_popup_text, w_popup.Ok)


# Function info_popup_ok : generic display of an info popup with OK button (french or default language)
def info_popup_ok(p_popup_title: str, p_popup_text: str):

    # Retrieving the locale system value
    w_locale = QtCore.QLocale.system().name()

    # Creating a new message box
    w_popup = QMessageBox()

    # If the locale says it's french and french UI
    if w_locale == glb_locale_fr_FR:

        # Setting up the critical icon
        w_popup.setIcon(QMessageBox.Information)

        # Filling the title and the text and loading the OK standard button
        w_popup.setWindowTitle(p_popup_title)
        w_popup.setText(p_popup_text)
        w_popup.setStandardButtons(QMessageBox.Ok)

        # Changing the text of the standard buttons
        btn_ok = w_popup.button(QMessageBox.Ok)
        btn_ok.setText(glb_Ok_text)

        # Displaying the message box
        w_popup.exec_()

    else:
        # Else, if it's not french, displaying the info popup directly...
        w_popup.information(None, p_popup_title, p_popup_text, w_popup.Ok)


# Function warning_popup_yes_no : generic display of a warning popup with yes/no choice (french or default language)
def warning_popup_yes_no(p_popup_title: str, p_popup_question: str):

    # Miscellaneous initializations
    p_btn_yes_pushed = False

    # Retrieving the locale system value
    w_locale = QtCore.QLocale.system().name()

    # Creating a new message box
    w_popup = QMessageBox()

    # If the locale says it's french and french UI
    if w_locale == glb_locale_fr_FR:

        # Setting up the warning icon
        w_popup.setIcon(QMessageBox.Warning)

        # Filling the title and the question and loading the Yes/No standard buttons
        w_popup.setWindowTitle(p_popup_title)
        w_popup.setText(p_popup_question)
        w_popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        # Changing the text of the standard buttons
        btn_yes = w_popup.button(QMessageBox.Yes)
        btn_yes.setText(glb_Yes_text)
        btn_no = w_popup.button(QMessageBox.No)
        btn_no.setText(glb_No_text)

        # Displaying the message box
        w_popup.exec_()

        # Button yes was pushed
        if w_popup.clickedButton() == btn_yes:
            p_btn_yes_pushed = True

    else:
        # Else, if it's not french, displaying the warning popup directly...
        w_popup_result = w_popup.warning(None, p_popup_title, p_popup_question, w_popup.Yes | w_popup.No)

        # Button yes was pushed
        if w_popup_result == w_popup.Yes:
            p_btn_yes_pushed = True

    # Returning the value
    return p_btn_yes_pushed


# Function change_active_task : turns an existing task at p_row into the active one (alias the "1st row", row(0))
def change_active_task(p_row: int, p_column: int):

    # Note : no use yet for p_column
    # The parameter is kept cause it's sent by a signal (like double clicking)

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Restart the global active task timer (only if we activate a task which is not the already activated one)
        if p_row > 0:
            glb_active_task_timer.start(glb_timer_interval_in_msec)

        # Retrieves the text of the 3 cells from the selected line (any row but fixed columns values)
        w_cell0_selected, w_cell1_selected, w_cell2_selected = get_lst_tasks_row_cells(p_row)

        # Retrieves the text of the 3 cells from the 1st row (the row 0 alias the active task but fixed columns values)
        w_cell0_1st_row, w_cell1_1st_row, w_cell2_1st_row = get_lst_tasks_row_cells(0)

        # /!\ Swapping the cells CONTENTS between the 1st row displayed and the selected one
        update_lst_tasks_row_cells(p_row, w_cell0_1st_row, w_cell1_1st_row, w_cell2_1st_row)
        update_lst_tasks_row_cells(0, w_cell0_selected, w_cell1_selected, w_cell2_selected)

        # Replacing the focus at the top
        default_focus()

        # Save my tasks on disk
        save_tasks_to_file()


# Function empty_lst_tasks : removes all rows by setting the counter of the lst_tasks to 0
def empty_lst_tasks():

    # Asking with a popup to confirm the deletion
    w_choice_confirmed = warning_popup_yes_no(glb_popup_title_all_tasks_deletion, glb_popup_question_all_tasks_deletion)

    # If confirming the deletion and if having some rows in the list
    if w_choice_confirmed is True:

        # Easiest way to destroy all rows and their attached items
        ptt_main_dlg.lst_tasks.setRowCount(0)

        # Refreshing the empty tasks button activation
        enable_btn_lst_tasks_empty()

        # Save my tasks on disk
        save_tasks_to_file()


# Function get_lst_tasks_row_cells : retrieves the text of each cells from a row of the lst_tasks list
def get_lst_tasks_row_cells(p_row: int):

    # Miscellaneous initializations
    p_cell0_text = glb_empty_str
    p_cell1_text = glb_empty_str
    p_cell2_text = glb_empty_str

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Retrieves each text
    if w_nbr_rows > 0:
        p_cell0_text = ptt_main_dlg.lst_tasks.item(p_row, 0).text()
        p_cell1_text = ptt_main_dlg.lst_tasks.item(p_row, 1).text()
        p_cell2_text = ptt_main_dlg.lst_tasks.item(p_row, 2).text()

    # Returns the values
    return p_cell0_text, p_cell1_text, p_cell2_text


# Function update_lst_tasks_row_cells : fills the text in each cell of a specified row
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

        # If the row is 0 aka the 1st displayed row, the background of the cells are yellow
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
    if p_text_task != glb_empty_str:

        # Getting the current datetime and formatting it
        w_now_dth = QtCore.QDateTime.currentDateTime()
        w_now_dth_string = w_now_dth.toString(glb_dd_MM_yyyy_hh_mm_string_format)

        # Getting the numbers of rows and inserting a new one (at the row_count position = at the end)
        w_row_count = ptt_main_dlg.lst_tasks.rowCount()
        ptt_main_dlg.lst_tasks.insertRow(w_row_count)

        # Filling the text in each cells of the new row
        update_lst_tasks_row_cells(w_row_count, w_now_dth_string, glb_00_00_time, p_text_task)

        # Setting to blank the entry text
        ptt_main_dlg.z_task_to_add.setText(glb_empty_str)

        # Turning the new task added into the active one
        change_active_task(w_row_count, 0)

        # Refreshing the empty tasks button activation
        enable_btn_lst_tasks_empty()


# Function enable_btn_task_add : enables or disables the button to add a task depending if z_task_to_add is filled
def enable_btn_task_add():
    if ptt_main_dlg.z_task_to_add.text() == glb_empty_str:
        ptt_main_dlg.btn_task_add.setEnabled(False)
    else:
        ptt_main_dlg.btn_task_add.setEnabled(True)


# Function enable_btn_lst_tasks_empty : enables or disables the button depending if the list has elements or not
def enable_btn_lst_tasks_empty():
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()
    if w_nbr_rows > 0:
        ptt_main_dlg.btn_lst_tasks_empty.setEnabled(True)
    else:
        ptt_main_dlg.btn_lst_tasks_empty.setEnabled(False)


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

        # Deleting the rows in the lst_tasks list with the row number of the temp list
        for row_to_delete in lst_rows_to_delete:
            ptt_main_dlg.lst_tasks.removeRow(row_to_delete)

        # Forcing the 1st displayed row to become the active task
        change_active_task(0, 0)

        # Refreshing the empty tasks button activation
        enable_btn_lst_tasks_empty()


# Function add_duration_to_task_at_row : adds a duration to the task duration found at the row received
def add_duration_to_task_at_row(p_row: int, p_duration_to_add_in_secs: int):

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Retrieves the text of the 3 cells from the selected line (any row but fixed columns values)
        w_cell0_text, w_cell1_text, w_cell2_text = get_lst_tasks_row_cells(p_row)

        # Turning the text of cell1 in 'hh:mm' format into true Qtime format
        w_qt_task_duration = QtCore.QTime.fromString(w_cell1_text, glb_hh_mm_string_format)

        # Converting the Qtime into seconds (seconds from 00:00:00 to the Qtime value :p )
        w_task_duration_in_secs = QtCore.QTime(0, 0, 0).secsTo(w_qt_task_duration)

        # Checking if the task duration already exceeds the max task duration
        if w_task_duration_in_secs >= glb_max_task_duration_in_sec:

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

                # Create a new task with the remains in secs
                add_new_task(w_cell2_text)
                add_duration_to_task_at_row(0, w_remains_in_secs)

            else:

                # Add the duration received to the current task duration
                w_task_duration = w_qt_task_duration.addSecs(p_duration_to_add_in_secs)

                # Turning the task duration back to string in 'hh:mm' format
                w_cell1_text = w_task_duration.toString(glb_hh_mm_string_format)

                # Putting back the row with the updated task duration
                update_lst_tasks_row_cells(p_row, w_cell0_text, w_cell1_text, w_cell2_text)

    # Save my tasks on disk
    save_tasks_to_file()


# Function auto_increment_active_task : increments the duration of the current active task by XX seconds
def auto_increment_active_task():

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Creating a default task when none are found to avoid loosing the logged time
    if w_nbr_rows == 0:
        add_new_task(glb_default_task_name)

    # Add XX seconds to the duration in the active task at row(0)
    add_duration_to_task_at_row(0, glb_default_added_duration_in_sec)


# Function enable_lst_tasks_popup_actions : makes actions visible or not for the lst_tasks list
def enable_lst_tasks_popup_actions():

    # Need to check if we have tasks in the list before
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    # Hiding all actions by default
    actionActivate.setVisible(False)
    actionEdit.setVisible(False)
    actionMerge.setVisible(False)
    actionDelete.setVisible(False)

    # ContextMenuPolicy is set to None by default
    # Trick to avoid the "ghostly" square with no option when no row selected looking -> °
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

        # If at least one row selected, forcing the ContextMenuPolicy in order to have the actions available
        if w_nbr_rows_selected > 0:
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


# Function popup_change_active_task : activates a task through the appropriate popup action
def popup_change_active_task():

    # Making sure we have some rows at least...
    w_nbr_rows = ptt_main_dlg.lst_tasks.rowCount()

    if w_nbr_rows > 0:

        # Normally, the action is only reachable if one task is selected... so should be enough
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

            # Retrieves the text of the 3 cells from the selected line (any row but fixed columns values)
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

            # Add the duration read to the total task duration
            w_total_duration_in_secs = w_total_duration_in_secs + w_task_duration_in_secs

        # Merge is aborted if the total duration of merged tasks exceeds (or is equal) to the max task duration !
        if w_total_duration_in_secs >= glb_max_task_duration_in_sec:

            # Error popup message
            error_popup_ok(glb_popup_title_merging_error, glb_popup_text_merging_failed)

        else:

            # Deleting the tasks and updating the "upper" one (since the list of merges is sorted etc...)
            w_nbr_of_rows_to_merge = len(lst_rows_to_merge)

            for w_row, w_text0, w_text1, w_text2 in lst_rows_to_merge:

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
                    update_lst_tasks_row_cells(w_row, w_text0, w_text1, w_text2)

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

            # Retrieves the text of the 3 cells from the selected line
            z_curr_task_dth, z_curr_task_duration, z_curr_task_description = get_lst_tasks_row_cells(index.row())

            # Retrieves current row number
            z_curr_row = index.row()


# Function call_ptt_edit_task : loads and displays the ptt_edit_task window
def call_ptt_edit_task():

    # Sending parameters to the edit window with a signal emitted
    ptt_main_calling_edit.edit_task_signal.emit(z_curr_row, z_curr_task_dth, z_curr_task_duration, z_curr_task_description)

    # Putting the focus on the 1st button
    ptt_edit_task_dlg.btn_1min.setFocus()

    # Hiding the txt_row_number label (contents the row number edited)
    ptt_edit_task_dlg.txt_row_number.hide()

    # Initializing and running the edit window
    ptt_edit_task_dlg.show()
    ptt_edit_task_app.exec()

    # Replacing the focus at the top
    default_focus()


# Function update_task_after_edit : updates a task after it was edited and saved in the edit window
def update_task_after_edit(p_curr_row: int, p_curr_task_dth: str, p_curr_task_duration: str, p_curr_task_description: str):

    # Updating the row contents in the list
    update_lst_tasks_row_cells(p_curr_row, p_curr_task_dth, p_curr_task_duration, p_curr_task_description)

    # Replacing the focus at the top
    default_focus()

    # Save my tasks on disk
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

    except IOError:
        # For console debugging
        print("Cannot write in the '{}' file".format(w_ptt_files.my_tasks_json))


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
                print("Error while reading json data in '{}'".format(w_ptt_files.my_tasks_json))

    except IOError:
        # For console debugging
        print("Cannot open the '{}' file".format(w_ptt_files.my_tasks_json))

    # For each task record found in w_tasks, loading retrieving the text
    for w_task_record in w_tasks["tasks"]:

        # Getting the numbers of rows and inserting a new one (at the row_count position = at the end)
        w_row_count = ptt_main_dlg.lst_tasks.rowCount()
        ptt_main_dlg.lst_tasks.insertRow(w_row_count)

        # Filling the text in each cells of the new row
        update_lst_tasks_row_cells(w_row_count, w_task_record["started_on"], w_task_record["duration"], w_task_record["description"])

    # Forcing the 1st displayed row to become the active task if at least one record loaded
    w_row_count = ptt_main_dlg.lst_tasks.rowCount()
    if w_row_count > 0:
        change_active_task(0, 0)


# Function create_tasks_backup : creates a backup file of the "my_tasks.json" file
def create_tasks_backup():

    # Miscellaneous initializations
    w_ptt_files = PttFiles()

    # Creating a backup of the file if it exists
    try:
        copyfile(w_ptt_files.my_tasks_json, w_ptt_files.my_tasks_backup)
    except FileNotFoundError:
        print("File'{}' not found".format(w_ptt_files.my_tasks_json))


# ------------------------------------------- #
# Functions of ptt_edit_task window
# ------------------------------------------- #

# ptt_edit_task / Function ptt_edit_task_duration_reset : resets the duration value in the modal window
def ptt_edit_task_duration_reset():
    w_qt_reset = QtCore.QTime.fromString(glb_00_00_time, glb_hh_mm_string_format)
    ptt_edit_task_dlg.z_task_duration.setTime(w_qt_reset)


# ptt_edit_task / Function ptt_edit_task_add_duration : adds the value sent by buttons to the duration field
def ptt_edit_task_add_duration(p_value_in_min: int):

    # For now, forcing min/max values for the duration (see globals at the top)
    ptt_edit_task_dlg.z_task_duration.setMinimumTime(glb_minimum_time_per_task)
    ptt_edit_task_dlg.z_task_duration.setMaximumTime(glb_maximum_time_per_task)

    # Adding the duration to the field
    w_time = ptt_edit_task_dlg.z_task_duration.time()
    w_result = w_time.addSecs(p_value_in_min*60)
    ptt_edit_task_dlg.z_task_duration.setTime(w_result)


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
    ptt_edit_task_saving.edit_task_signal.emit(p_curr_row, p_curr_task_dth, p_curr_task_duration, p_curr_task_description)

    # Closing the edit window
    ptt_edit_task_dlg.close()


# ------------------------------------------- #
# Main loop
# ------------------------------------------- #
if __name__ == "__main__":

    # Trying to create a backup of the "my_tasks.json" file (at application startup only)
    create_tasks_backup()

    # Forcing the list to accept the focus only with click
    # Reason : signals not working well with QTableWidget about selecting rows with the keyboard tabbing ! (= bug ?)
    ptt_main_dlg.lst_tasks.setFocusPolicy(Qt.ClickFocus)

    # Emptying the list of tasks
    ptt_main_dlg.lst_tasks.setRowCount(0)

    # Loading my tasks
    load_tasks_from_file()

    # Refreshing the empty tasks button activation
    enable_btn_lst_tasks_empty()

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

# Enabling or not the button to add a task
ptt_main_dlg.z_task_to_add.textChanged.connect(enable_btn_task_add)

# Adding a new task to the lst_tasks list with the appropriate button
ptt_main_dlg.btn_task_add.clicked.connect(lambda: add_new_task(ptt_main_dlg.z_task_to_add.text()))

# Adding a new task to the lst_tasks list when Enter key is pressed
ptt_main_dlg.z_task_to_add.returnPressed.connect(lambda: add_new_task(ptt_main_dlg.z_task_to_add.text()))

# Emptying the lst_tasks list of all of its rows
ptt_main_dlg.btn_lst_tasks_empty.clicked.connect(empty_lst_tasks)

# Turning a double clicked row as the active task on the 1st row
ptt_main_dlg.lst_tasks.cellDoubleClicked.connect(change_active_task)

# Reading the cells contents of a row selected and saves the info in the z_ global variables
ptt_main_dlg.lst_tasks.cellPressed.connect(read_current_task)

# Refreshing the popup actions of the list
ptt_main_dlg.lst_tasks.itemSelectionChanged.connect(enable_lst_tasks_popup_actions)

# Timer signal to manage the time logged on the active task
glb_active_task_timer.timeout.connect(auto_increment_active_task)

# Popup / actionActivate : activating the task selected
actionActivate.triggered.connect(popup_change_active_task)

# Popup / actionEdit : editing the task (datetime started on, duration, description)
actionEdit.triggered.connect(call_ptt_edit_task)

# Popup / actionMerge : merging the selected tasks (so at least 2)
actionMerge.triggered.connect(merge_selected_tasks)

# Popup / actionDelete : deleting the selected tasks
actionDelete.triggered.connect(delete_selected_tasks)

# Menu bar, menu PTT / actionQuit : closing the application
ptt_main_dlg.actionQuit.triggered.connect(ptt_main_dlg.close)

# Menu bar, menu PTT / actionAbout : display the "About" information popup
ptt_main_dlg.actionAbout.triggered.connect(lambda: info_popup_ok(glb_about_title, glb_about_info))

# ------------------------------------------- #
# Signals and connections (ptt_edit_task)
# ------------------------------------------- #

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

# Navigation management between ptt_main <-> ptt_edit_task (calls, I/O parameters...)
ptt_main_calling_edit.edit_task_signal.connect(ptt_edit_task_get_data)
ptt_edit_task_dlg.btn_save.clicked.connect(ptt_edit_task_send_data)
ptt_edit_task_saving.edit_task_signal.connect(update_task_after_edit)

# ------------------------------------------- #
# Initializing and running the main window
# ------------------------------------------- #

ptt_main_dlg.show()
ptt_main_app.exec()
