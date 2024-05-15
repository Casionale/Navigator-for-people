import codecs
import datetime
import os
import random

import pandas
import requests
import json
import time

from docx.shared import Pt
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import pdfkit
from docx import Document

import pandas as pd
import numpy

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QMessageBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import sys


from PomoikaUtils import NavigatorClient


class WorkerThread(QThread):
    progress = pyqtSignal(int, int)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(self.progress, *self.args, **self.kwargs)


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, columns):
        super(TableModel, self).__init__()
        self._data = data
        self._columns = columns

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._columns[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statesCheckboxes = None
        self.list_checkbox = None
        uic.loadUi("pomoikadesign.ui", self)
        self.pushButton_2.clicked.connect(lambda: self.child_info())
        self.pushButton.clicked.connect(lambda: self.print_stat_of_ages())
        self.btnPrintChildren.clicked.connect(lambda: self.print_children())
        self.nc = NavigatorClient()
        # self.fill_checkboxes()
        self.fill_tree_checkboxes()

        filemenu = self.menubar.addMenu('Дебаг')
        filemenu.addAction('Точка останова!', self.action_clicked)
        self.menuBar()

    @QtCore.pyqtSlot()
    def action_clicked(self):
        action = self.sender()
        st = self.statesCheckboxes
        print('Action: ', action.text())

    def child_info(self):
        if self.statesCheckboxes is not None:
            if len(self.statesCheckboxes) == 1:
                group_id = self.statesCheckboxes[0]
                self.nc.print_children(group_id)
            if len(self.statesCheckboxes) == 0:
                QMessageBox.about(self, "Ой", "Вы не выбрали группу")
                return
            else:
                list_children = self.nc.print_children_from_many_groups(self.statesCheckboxes)

            self.set_model_in_table_view(list_children)
            if len(self.statesCheckboxes) == 1:
                group_name = [g['program_name'] + " " + g['name'] for g in self.nc.groups if g['id'] == group_id][0]
            else:
                group_names = []
                group_names.extend(
                    [g['program_name'] + " " + g['name'] for g in self.nc.groups if g['id'] in self.statesCheckboxes])
                group_name = ' '.join(group_names)
                self.label_over_table.setToolTip('\n'.join(group_names))
            self.label_over_table.setText(group_name)
        else:
            QMessageBox.about(self, "Ой", "Вы не выбрали группу")
            return

    def fill_checkboxes(self):
        groups = self.nc.groups
        self.list_checkbox = []
        self.statesCheckboxes = []

        widget = QWidget()
        vbox = QVBoxLayout()

        for g in groups:
            self.list_checkbox.append(f"{g['program_name']} {g['name']}")
            c_b = QCheckBox(f"{g['program_name']} {g['name']}")
            c_b.group_id = g['id']
            c_b.stateChanged.connect(self.on_state_changed)
            vbox.addWidget(c_b)

        widget.setLayout(vbox)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(widget)

    def fill_tree_checkboxes(self):
        values = set(map(lambda x: x['teacher'], self.nc.groups))
        groups_groupby_teacher = {x: [y for y in self.nc.groups if y['teacher'] == x] for x in values}
        tree = QTreeWidget()
        for key in groups_groupby_teacher.keys():
            parent = QTreeWidgetItem(tree)
            parent.setText(0, "Педагог {}".format(key))
            for x in groups_groupby_teacher[key]:
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, "{}".format(f"{x['program_name']} {x['name']}"))
                child.setCheckState(0, Qt.Unchecked)
                child.group_id = x['id']
        tree.itemClicked.connect(self.onItemClicked)

        tree.show()
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(tree)

    def on_state_changed(self):
        sender = self.sender()
        if sender.isChecked():
            self.statesCheckboxes.append(sender.group_id)
        else:
            self.statesCheckboxes.remove(sender.group_id)

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def onItemClicked(self, it, column):

        try:
            if it.checkState(column) == Qt.Checked:
                if self.statesCheckboxes is None:
                    self.statesCheckboxes = [it.group_id]
                    return
                if it.group_id not in self.statesCheckboxes:
                    self.statesCheckboxes.append(it.group_id)
            else:
                if self.statesCheckboxes is not None or len(self.statesCheckboxes):
                    if it.group_id in self.statesCheckboxes:
                        self.statesCheckboxes.remove(it.group_id)
        except AttributeError:
            return
        except TypeError:
            return

    def set_model_in_table_view(self, model):

        if len(model) == 0:
            QMessageBox.about(self, "Ой", "Группа пуста.")
            return
        model = TableModel(model, columns=['ФИО', 'Дата рождения', 'Возраст'])
        self.tableView.setModel(model)

    def save_file_dialog(self, title, filter):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, title, "",
                                                  filter, options=options)
        return fileName, _

    def print_children(self):
        fileName, _ = self.save_file_dialog("Список обучающихся",
                                                  "Text Files (*.txt)")
        try:
            f = open(fileName + '.txt', 'w', encoding='utf-8')
            for c in self.nc.list_children:
                f.write(c['kid_last_name'] + " " + c['kid_first_name'] + " " + c['kid_patro_name'] + "\t" +
                        c['kid_birthday'] + "\t" + str(c['kid_age']) + "\n")
            f.close()

        except Exception as e:
            os.remove(fileName + '.txt')
            print(e)

    def print_stat_of_ages(self):
        fileName, _ = self.save_file_dialog("Статистика по возрастам",
                                            "Text Files (*.txt)")
        fileName = fileName + '.txt'
        #self.nc.stat_of_ages(fileName)

        self.thread = WorkerThread(self.nc.stat_of_ages, fileName)
        self.thread.finished.connect(self.on_finished)
        self.thread.progress.connect(self.update_progress)
        self.thread.start()

    def update_progress(self, value, maximum):
        self.progressBar.setMaximum(maximum)
        self.progressBar.setValue(value)
        print(value, maximum)


    def on_finished(self):
        print('Process finished!')

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()
