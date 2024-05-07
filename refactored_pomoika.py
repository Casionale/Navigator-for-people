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
                             QMessageBox, QCheckBox, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import sys


class NavigatorClient:

    def __init__(self):
        self.groups = None
        url = "https://booking.dop29.ru/api/user/login"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"

        directory = os.getcwd()

        file_login = open(directory + '\\login.ini', 'r')
        str_login = file_login.read().split('\n')
        email = str_login[0]
        password = str_login[1]
        self.YEAR = str_login[2]

        self.session = requests.Session()
        r = self.session.post(url, headers={
            'Host': 'booking.dop29.ru',
            'User-Agent': self.user_agent,
            'Accept': '*\\/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Length': '63',
            'Origin': 'https://booking.dop29.ru',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://booking.dop29.ru/admin/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers',
        }, data='{"email": "' + email + '", "password": "' + password + '"}')

        self.session.headers.update({'Referer': 'https://booking.dop29.ru/admin/'})
        self.session.headers.update({'User-Agent': self.user_agent})

        text_buf = r.text
        json_string = json.loads(text_buf)

        self.access_token = json_string['data']['access_token']
        self.expired_at = json_string['data']['expired_at']
        self.refresh_token = json_string['data']['refresh_token']

        self.user = json_string['data']['user']

        self.MAX_GROUPS_COUNT = 500

        self.headers = {
            'Host': 'booking.dop29.ru',
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': 'Bearer ' + self.access_token,
            'X-REQUEST-ID': '7bd411c3-54ce-4bba-9ee1-7c5091da6d1a',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://booking.dop29.ru/admin/',
            'Cookie': 'io=lVluIaMvSTa4ImFmB5C9',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }
        self.get_groups()

    def get_groups(self):
        new_url = ('https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25'
                   '&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},'
                   '{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length=') + str(
            self.MAX_GROUPS_COUNT)
        r = self.session.get(new_url, headers=self.headers)

        b = json.loads(r.text)
        self.groups = b['data']

        if int(b['recordsFiltered']) > len(self.groups):
            print("Загружено {0} из {1}".format(len(self.groups), int(b['recordsFiltered'])))

            new_url = (('https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25'
                        '&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},'
                        '{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length=') +
                       str(
                           self.MAX_GROUPS_COUNT) + '&page=2&start=' + str(len(self.groups)))
            r = self.session.get(new_url, headers=self.headers)

            b = json.loads(r.text)
            self.groups.extend(b['data'])

            print("Загружено {0} из {1}".format(len(self.groups), int(b['recordsFiltered'])))

        return "Загружено {0} из {1}".format(len(self.groups), int(b['recordsFiltered']))

    def print_children_from_many_groups(self, list_group_id):
        list_children = []
        for group_id in list_group_id:
            list_children.extend(self.print_children(group_id))
        return list_children

    def print_children(self, group_id):
        list_children = self.get_children(group_id)

        returned_list = []

        for c in list_children:
            returned_list.append([c['kid_last_name'] + " " + c['kid_first_name'] + " " + c['kid_patro_name'],
                                  c['kid_birthday'], c['kid_age']])

        return returned_list

    def get_children(self, group_id):
        new_url = (('https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25'
                    '&extFilters=[{"property":"group_id","value":"') + str(
            group_id) + '"},{"property":"academic_year_id","value":"' + str(
            self.YEAR) + '"},{"property":"dateStart","value":"' + self.YEAR + ('-12-01 00:00:00"},'
                                                                               '{"property":"dateEnd","value":"') +
                   self.YEAR + '-12-31 23:59:59"}]')
        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        list_children = b['data']
        new_list_children = []
        for i in range(0, len(list_children)):
            if list_children[i]['type_active'] == 1:
                new_list_children.append(list_children[i])
        return new_list_children


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
        self.nc = NavigatorClient()
        #self.fill_checkboxes()
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
        groups_groupby_teacher = {x : [y for y in self.nc.groups if y['teacher'] == x] for x in values}
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


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()
