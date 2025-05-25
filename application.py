from pathlib import Path
import os
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
                MAX_GROUPS_COUNT) + '&page=2&start=' + str(len(groups))
            r = self.session.get(new_url, headers=headers)
            b = json.loads(r.text)
            self.groups.extend(b['data'])

        return "Загружено {0} из {1}".format(len(self.groups), int(b['recordsFiltered']))

    def get_teachers(self):
        self.teachers = {}
        for g in self.groups:
            if self.teachers.get(g["teacher"]) is not None:
                self.teachers[g["teacher"]].append(g)
            else:
                self.teachers[g["teacher"]] = []
                self.teachers[g["teacher"]].append(g)

        keys = []
        for t in self.teachers:
            keys.append(t)

        return keys

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





