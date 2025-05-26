from pathlib import Path
import os
import random

import pandas
import pandas as pd
import requests
import json
from datetime import datetime

class App:
    url = "https://booking.dop29.ru/api/user/login"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"
    dir = None
    email = None
    password = None
    YEAR = None
    OUTPUT_DIR = None
    session = None
    use_filter = False
    groups = None
    user = None
    refresh_token = None
    expired_at = None
    access_token = None
    teachers = {}
    selected_groups = None
    
    def __init__(self):
        self.dir = os.getcwd()
        file_login = open(self.dir + '\\login.ini', 'r')
        str_login = file_login.read().split('\n')
        self.email = str_login[0]
        self.password = str_login[1]
        self.YEAR = str_login[2]
        self.OUTPUT_DIR = Path(self.dir) / 'output'
        
        if not self.OUTPUT_DIR.exists():
            os.makedirs(self.OUTPUT_DIR)

        self.session = requests.Session()

    def get_save_path(self, filename):
        now = datetime.now()
        str_now = now.strftime('%m-%d-%y')

        folder_path = self.OUTPUT_DIR / str_now

        if not folder_path.exists():
            os.makedirs(folder_path)

        return folder_path / filename

    def auth(self):
        try:
            r = self.session.post(self.url, headers={
                'Host': 'booking.dop29.ru',
                'User-Agent': self.user_agent,
                'Accept': '*/*',
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
            }, data='{"email": "' + self.email + '", "password": "' + self.password + '"}')
            self.session.headers.update({'Referer': 'https://booking.dop29.ru/admin/'})
            self.session.headers.update({'User-Agent': self.user_agent})

            text_buf = r.text
            json_string = json.loads(text_buf)

            if json_string['err_code'] == 400:
                return json_string['errors'][0]['msg']
            else:
                self.access_token = json_string['data']['access_token']
                self.expired_at = json_string['data']['expired_at']
                self.refresh_token = json_string['data']['refresh_token']

                self.user = json_string['data']['user']

                return 0
        except Exception as e:
            return e

    def get_all_groups(self, max_groups_count=500):
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

        new_url = 'https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length=' + str(
            max_groups_count)
        r = self.session.get(new_url, headers=self.headers)

        b = json.loads(r.text)
        self.groups = b['data']

        if int(b['recordsFiltered']) > len(self.groups):

            new_url = 'https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length=' + str(
                max_groups_count) + '&page=2&start=' + str(len(self.groups))
            r = self.session.get(new_url, headers=self.headers)
            b = json.loads(r.text)
            self.groups.extend(b['data'])

        return "Загружено {0} из {1}".format(len(self.groups), int(b['recordsFiltered']))

    def get_teachers(self):
        self.teachers = {}
        groups_id = []
        with open(Path(self.dir) / 'groups.ini', 'r', encoding='utf-8') as f:
            groups_id = f.read().split('\n')

        if self.use_filter:
            for g in self.groups:
                if g['id'] not in groups_id:
                    self.groups.remove(g)

        for g in self.groups:
            if self.use_filter:
                if g['id'] in groups_id:

                    self.fill_teachers(g)
                else:
                    continue
            else:
                self.fill_teachers(g)

        keys = []
        for t in self.teachers:
            keys.append(t)

        return keys

    def fill_teachers(self, g):
        if self.teachers.get(g["teacher"]) is not None:
            self.teachers[g["teacher"]].append(g)
        else:
            self.teachers[g["teacher"]] = []
            self.teachers[g["teacher"]].append(g)

    def select_groups(self, teacher_groups):
        groups = []
        for t in teacher_groups:
            groups.extend(self.teachers[t])

        self.groups = groups

    def printChildren(self):
        ids = self.selected_groups.strip().split(' ')
        ids = [int(i) for i in ids]
        ret_msg = []
        for i in ids:
            group_id_val = self.groups[i]['id']
            print('Выбрана группа ' + self.groups[i]['program_name'] + ' ' + self.groups[i]['name'])
            list_childrens = self.get_childrens(group_id_val=group_id_val)
            f = open(self.get_save_path(f"Список группы {self.groups[i]['program_name']} {self.groups[i]['name']}.txt"), 'w',
                     encoding="utf-8")
            for c in list_childrens:
                line = (f'{c['kid_last_name']} {c['kid_first_name']} {c['kid_patro_name']}\t'
                        f'{c['kid_birthday'].replace('-', '.')}\t{c['kid_age']}\n')
                f.write(line)
            f.close()
            ret_msg.append(f"Созданы: {self.get_save_path(f"Список группы {self.groups[i]['program_name']} "
                                                          f"{self.groups[i]['name']}.txt")}\n")
        return ret_msg

    def get_childrens(self, group_id_val):
        new_url = 'https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25&extFilters=[{"property":"group_id","value":"' + str(
            group_id_val) + '"},{"property":"academic_year_id","value":"' + str(
            self.YEAR) + '"},{"property":"dateStart","value":"' + self.YEAR + '-12-01 00:00:00"},{"property":"dateEnd","value":"' + self.YEAR + '-12-31 23:59:59"}]'
        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        list_childrens = b['data']
        new_list_childrens = []
        for i in range(0, len(list_childrens)):
            if list_childrens[i]['type_active'] == 1:
                new_list_childrens.append(list_childrens[i])
        return new_list_childrens

    def stat_of_ages(self, unique=False, confirmed=False, by_program_name=False, negative_groups=[], status_wiget = None):
        ages = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0,
                16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
        stupid_girls_by_ages = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0,
                                14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
        sum_girls = 0
        sum_childs = 0
        error_sex = 0
        error_child = []

        unique_childs = set()
        repeated_childs = 0
        repeteds = 0
        repeated_childs_id = []

        ages_of_sections = {}  # секция: [мальчики, девочки]
        for i in range(0, len(self.groups)):

            if len(negative_groups) > 0:
                negative_check = [ind for ind in negative_groups if ind in self.groups[i]['name'].lower()]
                if len(negative_check) != 0:
                    print('\r Проигнорированна группа ' + self.groups[i]['name'] + '\n')
                    continue

            g_inp = i
            group_id_val = self.groups[i]['id']
            event_id = self.groups[i]['event_id']


            list_childrens = self.get_childrens(group_id_val=group_id_val)
            if by_program_name:
                section = self.groups[i]['program_name']
            else:
                section = self.get_section(event_id)

            if section not in ages_of_sections:
                ages_of_sections[section] = [0], [0], {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0,
                                                       10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0,
                                                       19: 0, 20: 0, 21: 0}  # Мальчики, девочки

            iterator_childrens = 0

            for c in list_childrens:
                if unique:
                    if c['kid_id'] in unique_childs:
                        repeteds += 1
                        if c['kid_id'] not in repeated_childs_id:
                            repeated_childs += 1
                            repeated_childs_id.append(c['kid_id'])
                        continue
                    else:
                        unique_childs.add(c['kid_id'])

                ages[c['kid_age']] += 1
                ages_of_sections[section][2][c['kid_age']] += 1
                c_info = self.get_all_info_child(c['kid_id'])
                sum_childs += 1

                try:
                    if c_info['sex'] == 'W':
                        sum_girls += 1
                        ages_of_sections[section][1][0] += 1
                        stupid_girls_by_ages[c['kid_age']] += 1
                    else:
                        ages_of_sections[section][0][0] += 1
                except:
                    error_sex += 1
                    error_child.append(
                        "{0} {1} {2} {3}".format(c['kid_last_name'], c['kid_first_name'], c['kid_patro_name'],
                                                 c['kid_birthday']))

                iterator_childrens += 1

                if status_wiget is not None:
                    status_wiget.values.add(f"Выбрана группа {self.groups[g_inp]['program_name']} {self.groups[g_inp]['name']}")

        if not unique:
            f = open(self.get_save_path("Статистика по возрастам.txt"), "w", encoding='utf-8')
        else:
            f = open(self.get_save_path("Статистика по возрастам УНИКАЛЬНЫЕ.txt"), "w", encoding='utf-8')
        for i in range(0, 19):
            if ages[i] == 0:
                continue
            else:
                f.write(str(i) + " лет " + str(ages[i]) + f" человек; {stupid_girls_by_ages[i]} из них девочек \n")

        f.write("Всего: {0}, из них девочек: {1}".format(sum_childs, sum_girls))
        f.write("\nНе удалось получить информацию у {0} человек:".format(error_sex))
        for l in error_child:
            f.write(l)
        for key, value in ages_of_sections.items():
            f.write("\n\nНаправленность: {0}, М {1}, Ж {2}\n\n".format(key, value[0][0], value[1][0]))

            for i in range(0, 19):
                if value[2][i] == 0:
                    continue
                else:
                    f.write(str(i) + " лет " + str(value[2][i]) + " человек\n")

        if unique:
            f.write("\nПовторов всего: " + str(repeteds))
            f.write("\nПовторов детей: " + str(repeated_childs))
            f.write('\n' + str(repeated_childs_id))

        f.close()
        if not unique:
            return [f"Файл {self.get_save_path("Статистика по возрастам.txt")} создан успешно!"]
        else:
            return [f"Файл {self.get_save_path("Статистика по возрастам УНИКАЛЬНЫЕ.txt")} создан успешно!"]

    def get_section(self, event_id):
        new_url = 'https://booking.dop29.ru/api/rest/events/{0}?_dc=1705994318220'.format(event_id)
        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        try:
            return b['data'][0]['section']
        except:
            return []

    def get_all_info_child(self, id):
        new_url = "https://booking.dop29.ru/api/rest/kid/{0}?_dc=1704971612231".format(id)
        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        try:
            child = b['data'][0]
            return child
        except:
            return []

    def getListChildrensFromOrderAnyGroups(self):
        ret_str = []
        ids = self.selected_groups.strip().split(' ')
        ids = [int(i) for i in ids]

        for i in ids:
            ret_str.append(self.getFileListChildrensFromOrder(self.groups[i]))

        return ret_str

    def getFileListChildrensFromOrder(self, group):
        group_id_val = group['id']

        new_url = 'https://booking.dop29.ru/api/rest/order?_dc=1695285515100&page=1&start=0&length=25&extFilters=[{"property":"fact_academic_year_id","value":' + self.YEAR + ',"comparison":"eq"},{"property":"event_id","value":' + \
                  group['event_id'] + ',"comparison":"eq"},{"property":"fact_group_id","value":"' + str(
            group_id_val) + '","comparison":"eq"},{"property":"state","value":["approve"],"comparison":"in"}]'

        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        list_childrens = b['data']
        list_names = []
        for children in list_childrens:
            url_child = 'https://booking.dop29.ru/api/rest/kid/' + children['kid_id']
            r = self.session.get(url_child, headers=self.headers)
            child = json.loads(r.text)['data'][0]
            list_names.append(child['last_name'] + " " + child['first_name'] + " " + child['patro_name'])

        filename = self.get_save_path(f"Подтверждённые заявки {group['program_name']} {group['name']}.txt")

        file = open(filename, 'w', encoding="utf-8")
        file.write("\n".join(list_names))
        file.close()

        return f"Файл {filename} создан!"

    def up_close_day(self, filename, group):
        df = pd.read_excel(filename)

        for row in df.itertuples():
            if not pandas.isnull(row[2]):
                self.close_day(row[2].strftime('%Y-%m-%d'), row[3], row[4], row[5], group)
        return ['Внесение информации завершено. Проверьте в навигаторе дни!']

    # Типы занятий
    # Практическая работа 9732
    # Учебное 7198
    # Дистанционное 3022
    #
    def close_day(self, date, theme, type, description, group):
        percentagevisits = 80
        group_id_val = group['id']
        group_id = group['id']

        childrens = self.get_childrens(group_id_val)

        for c in childrens:
            visit = random.randint(0, 100)
            if visit < percentagevisits:
                visit = True
            else:
                visit = False
            kid_id = c['kid_id']
            day_url_POST = "https://booking.dop29.ru/api/attendance/save"  # date group_id kid_id value:true
            payload = {'date': date, 'group_id': group_id, 'kid_id': kid_id, 'value': visit}
            r = self.session.post(url=day_url_POST, headers=self.headers, data=json.dumps(payload))

        KTP_url_POST = "https://booking.dop29.ru/api/event-group-lessons/upsert"  # date group_id types:list description

        payload = json.loads(json.dumps({'data': {'date': date + ' 00:00:00', 'group_id': group_id, 'theme': theme,
                                                  'types': [str(int(type))], 'description': description}}))
        r = self.session.post(url=KTP_url_POST, headers=self.headers, json=payload)
