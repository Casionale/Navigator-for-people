import os, requests, json

class NavigatorClient:
    list_children = None

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
        self.list_children = list_children
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

    def stat_of_ages(self, progress_signal, progress_signal2, filename,  unique=False, by_program_name=False, negative_groups=[]):
        ages = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0,
                17: 0, 18: 0, 19: 0, 20: 0, 21: 0}
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

            progress_signal2.emit(i, len(self.groups) - 1, self.groups[i][
                'program_name'] + ' ' + self.groups[i]['name'])

            if len(negative_groups) > 0:
                negative_check = [ind for ind in negative_groups if ind in self.groups[i]['name'].lower()]
                if len(negative_check) != 0:
                    print('\r Проигнорированна группа ' + self.groups[i]['name'] + '\n')
                    continue

            event_id = self.groups[i]['event_id']

            list_childrens = self.get_children(self.groups[i]['id'])
            if by_program_name:
                section = self.groups[i]['program_name']
            else:
                section = self.get_section(event_id)

            if section not in ages_of_sections:
                ages_of_sections[section] = [0], [0], {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0,
                                                       11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0,
                                                       21: 0}  # Мальчики, девочки

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
                    else:
                        ages_of_sections[section][0][0] += 1
                except:
                    error_sex += 1
                    error_child.append(
                        "{0} {1} {2} {3}".format(c['kid_last_name'], c['kid_first_name'], c['kid_patro_name'],
                                                 c['kid_birthday']))

                iterator_childrens += 1
                progress_signal.emit(iterator_childrens, len(list_childrens))

        if not unique:
            f = open(filename, "w")
        else:
            f = open(filename, "w")
        for i in range(0, 19):
            if ages[i] == 0:
                continue
            else:
                f.write(str(i) + " лет " + str(ages[i]) + " человек\n")

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

        progress_signal2.emit(1, 1, 'ГОТОВО!')

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

    def getListChildrensFromOrder(self, id_group):

        g = [g for g in self.groups if g['id'] == id_group][0]
        event_id = g['event_id']

        new_url = 'https://booking.dop29.ru/api/rest/order?_dc=1695285515100&page=1&start=0&length=25&extFilters=[{"property":"fact_academic_year_id","value":' + self.YEAR + ',"comparison":"eq"},{"property":"event_id","value":' + \
                  event_id + ',"comparison":"eq"},{"property":"fact_group_id","value":"' + str(
            id_group) + '","comparison":"eq"},{"property":"state","value":["approve"],"comparison":"in"}]'

        r = self.session.get(new_url, headers=self.headers)
        b = json.loads(r.text)
        list_childrens = b['data']
        list_names = []
        for i in range(len(list_childrens)):
            url_child = 'https://booking.dop29.ru/api/rest/kid/' + list_childrens[i]['kid_id']
            r = self.session.get(url_child, headers=self.headers)
            child = json.loads(r.text)['data'][0]
            list_names.append(child['last_name'] + " " + child['first_name'] + " " + child['patro_name'])

        return g['program_name'] + ' ' + g['name'], list_names

