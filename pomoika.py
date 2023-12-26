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

url = "https://booking.dop29.ru/api/user/login"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"

dir = os.getcwd()

email = 'kirill.bagrow@yandex.ru'
password = 'CasioTitanium1'

# email = input("Введите email\n")
# password = input("Введите password\n")
file_login = open(dir + '\\login.ini', 'r')
str_login = file_login.read().split('\n')
email = str_login[0]
password = str_login[1]
YEAR = str_login[2]

session = requests.Session()
r = session.post(url, headers={
    'Host': 'booking.dop29.ru',
    'User-Agent': user_agent,
    'Accept': '*\/*',
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

print('Авторизация удалась походу')

session.headers.update({'Referer': 'https://booking.dop29.ru/admin/'})
session.headers.update({'User-Agent': user_agent})

text_buf = r.text
json_string = json.loads(text_buf)

access_token = json_string['data']['access_token']
expired_at = json_string['data']['expired_at']
refresh_token = json_string['data']['refresh_token']

user = json_string['data']['user']

MAX_GROUPS_COUNT = 500

new_url = 'https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length='+str(MAX_GROUPS_COUNT)
r = session.get(new_url, headers={
    'Host': 'booking.dop29.ru',
    'User-Agent': user_agent,
    'Accept': '*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Authorization': 'Bearer ' + access_token,
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
})

b = json.loads(r.text)
groups = b['data']

if int(b['recordsFiltered']) > len(groups):
    print("Загружено {0} из {1}".format(len(groups), int(b['recordsFiltered'])))

    new_url = 'https://booking.dop29.ru/api/rest/eventGroups?_dc=1641896017213&page=1&start=0&length=25&extFilters=[{"property":"is_deleted","value":"0","comparison":"eq"},{"property":"event.is_deleted","value":"N","comparison":"eq"}]&format=attendance&length=' + str(
        MAX_GROUPS_COUNT)+'&page=2&start='+str(len(groups))
    r = session.get(new_url, headers={
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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
    })

    b = json.loads(r.text)
    groups.extend(b['data'])

    print("Загружено {0} из {1}".format(len(groups), int(b['recordsFiltered'])))

i = -1


def printChildren():
    global new_url, r, b, i
    print('Выбрана группа ' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'])
    year = YEAR
    new_url = 'https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25&extFilters=[{"property":"group_id","value":"' + group_id_val + '"},{"property":"academic_year_id","value":"' + YEAR + '"},{"property":"dateStart","value":"'+str(int(YEAR)+1)+'-09-01 00:00:00"},{"property":"dateEnd","value":"'+YEAR+'-05-31 23:59:59"}]'
    buf = new_url
    r = session.get(new_url, headers={
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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
    })
    b = json.loads(r.text)
    list_childrens = b['data']
    new_list_childrens = []
    for i in range(0, len(list_childrens)):
        if list_childrens[i]['type_active'] == 1:
            new_list_childrens.append(list_childrens[i])
    list_childrens = new_list_childrens
    f = open('Список группы ' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + ".txt", 'w')
    for c in list_childrens:
        f.write(c['kid_last_name'] + " " + c['kid_first_name'] + " " + c['kid_patro_name'] + '\t' +
                str(c['kid_birthday']).replace('-', '.') + '\t' + str(c['kid_age']) + '\n')
    f.close()
    return 'Список группы ' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + ".txt"

def stat_of_ages():
    global new_url, r, b, i
    ages = {0:0, 1:0, 2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,20:0,21:0}
    for i in range(0, len(groups)):
        g_inp = i
        group_id_val = groups[i]['id']

        print('Выбрана группа ' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'])
        year = YEAR
        new_url = 'https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25&extFilters=[{"property":"group_id","value":"' + str(
            group_id_val) + '"},{"property":"academic_year_id","value":"' + str(
            YEAR) + '"},{"property":"dateStart","value":"'+YEAR+'-12-01 00:00:00"},{"property":"dateEnd","value":"'+YEAR+'-12-31 23:59:59"}]'
        r = session.get(new_url, headers={
            'Host': 'booking.dop29.ru',
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': 'Bearer ' + access_token,
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
        })
        b = json.loads(r.text)
        list_childrens = b['data']
        new_list_childrens = []
        for i in range(0, len(list_childrens)):
            if list_childrens[i]['type_active'] == 1:
                new_list_childrens.append(list_childrens[i])
        list_childrens = new_list_childrens
        for c in list_childrens:
            ages[c['kid_age']] += 1

    f = open("Статистика по возрастам.txt", "w")
    for i in range(0, 19):
        if ages[i] == 0:
            continue
        else:
            f.write(str(i) + " лет " + str(ages[i]) + " человек\n")
    f.close()

def get_childrens():
    new_url = 'https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25&extFilters=[{"property":"group_id","value":"' + str(
        group_id_val) + '"},{"property":"academic_year_id","value":"' + str(
        YEAR) + '"},{"property":"dateStart","value":"' + YEAR + '-12-01 00:00:00"},{"property":"dateEnd","value":"' + YEAR + '-12-31 23:59:59"}]'
    r = session.get(new_url, headers={
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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
    })
    b = json.loads(r.text)
    list_childrens = b['data']
    new_list_childrens = []
    for i in range(0, len(list_childrens)):
        if list_childrens[i]['type_active'] == 1:
            new_list_childrens.append(list_childrens[i])
    return new_list_childrens

def printGroup():
    global new_url, r, b, i
    print('Выбрана группа ' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'])
    new_url = 'https://booking.dop29.ru/api/attendance/members/get?_dc=1641896197594&page=1&start=0&length=25&extFilters=[{"property":"group_id","value":"' + str(
        group_id_val) + '"},{"property":"academic_year_id","value":"' + str(YEAR) + '"}]'
    r = session.get(new_url, headers={
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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
    })
    b = json.loads(r.text)
    list_childrens = b['data']
    new_list_childrens = []
    for i in range(0, len(list_childrens)):
        if list_childrens[i]['type_active'] == 1:
            new_list_childrens.append(list_childrens[i])
    list_childrens = new_list_childrens
    # lc = []
    # for i in range(0, len(list_childrens)-1):
    #    lc.append({k: str(v).encode("utf-8") for k,v in list_childrens[i].items()})
    for i in range(len(list_childrens)):
        cursor = list_childrens[i]
        pos = i

        while pos > 0 and list_childrens[pos - 1]['kid_last_name'] > cursor['kid_last_name']:
            # Меняем местами число, продвигая по списку
            list_childrens[pos] = list_childrens[pos - 1]
            pos = pos - 1
        # Остановимся и сделаем последний обмен
        list_childrens[pos] = cursor
    example_date = datetime.date(2021, 9, 1) # ДАТЫ!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    keys = [], [], []
    start_date = datetime.date(2021, 9, 1)
    end_date = datetime.date(2022, 6, 10)
    while start_date < end_date:
        keys[0].append(start_date)
        keys[1].append('a' + str(start_date.year) + '_' + str(start_date.month) + '_' + str(start_date.day))
        start_date = start_date + datetime.timedelta(days=1)
    days = []
    list = {}
    for c in list_childrens:
        for str_date in keys[1]:
            if str_date in c:
                if c[str_date] == 1 or c[str_date] == 0:  # Все дети, маркер 0 или 1
                    if str_date in list:
                        list[str_date].append(c)
                    else:
                        list[str_date] = []
                        list[str_date].append(c)
    new_list = {}
    for str_date in list:
        buf = list[str_date]
        zero_count = 0
        for i in buf:
            if i[str_date] == 0:
                zero_count += 1
        if zero_count != len(buf):
            new_list[str_date] = buf
    list = new_list
    env = Environment(
        loader=FileSystemLoader(dir + '\\templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')
    new_list = [], [], []  # месяц, день недели, день
    monthNames = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь",
                  "Ноябрь", "Декабрь"]
    dnNames = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    spans = []
    j = 0
    for i in range(0, len(keys[0]) - 1):
        if keys[1][i] in list:
            d = keys[0][i]
            m = d.month
            dn = d.weekday()
            dday = d.day
            new_list[0].append(monthNames[m])
            new_list[1].append(dnNames[dn])
            new_list[2].append(dday)
    beforeMonth = ''
    monthcount = 0
    spans = []
    mouthNames = []
    spansCount = 0
    for m in new_list[0]:
        if beforeMonth == m:
            spansCount += 1
        else:
            beforeMonth = m
            monthcount += 1
            if spansCount != 0:
                spans.append(spansCount)
            mouthNames.append(m)
            spansCount = 1
    spans.append(spansCount)
    rowsChildrens = []
    for i in range(0, len(list_childrens)):
        rowsChildrens.append([])
        for j in range(0, len(keys[0])):
            if keys[1][j] in list:
                try:
                    rowsChildrens[i].append(list[keys[1][j]][i][keys[1][j]])
                except:
                    print("Ошибка из-за дня" + str(keys[1][j]))
    maxSpans = 2
    for i in spans:
        maxSpans += i
    title = ["Группа: " + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + "   Педагог " + groups[g_inp][
        'teacher'], maxSpans]

    html = template.render(keys=keys, list=list, childrens=list_childrens, new_list=new_list,
                           mouthNames=mouthNames, spans=spans, rowsChildrens=rowsChildrens, title=title)
    file = open(dir + '\\' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + '.html', 'w',
                encoding="utf-8")
    file.write(html)
    file.close()

    config = pdfkit.configuration(wkhtmltopdf=bytes(dir + '\\wkhtmltopdf\\bin\\wkhtmltopdf.exe', 'utf-8'))
    pdfkit.from_file(dir + '\\' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + '.html',
                     dir + '\\' + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + '.pdf',
                     configuration=config, options={'--orientation': 'landscape'})
    print("Готово")


def getListOrganisingGroups(group):
    global g_inp, group_id_val
    template = "Список организованных групп ШАБЛОН.docx"
    doc = Document(template)
    g_inp = int(group)
    group_id_val = groups[int(group)]['id']
    filePath = printChildren()
    f = open(filePath, "r")
    file = f.readlines()
    f.close()
    table = doc.tables[1]

    nums = ""
    names = ""
    ages = ""

    iterator = 1
    for child in file:
        c = child.replace('\n', '').split('\t')
        nums += str(iterator) + ('\n' if iterator < len(file) else '')
        names += c[0] + ('\n' if iterator < len(file) else '')
        ages += 'Да' + ('\n' if iterator < len(file) else '')
        iterator+=1

    style = table.style
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    table.style = style

    numCell = table.cell(1, 0)
    numCell.text = nums
    nameCell = table.cell(1, 1)
    nameCell.text = names
    ageCell = table.cell(1,2)
    ageCell.text = ages
    filename = filePath.replace('группы', 'огранизованных групп').replace('.txt', '.docx')
    doc.save(filename.replace('Список огранизованных групп', 'СОГ'))
    os.remove(filePath)

def getListOrganisingGroupsAnyGroup(groups):
    if ' ' in groups:
        groups = groups.split[' ']
        for group in groups:
            getListOrganisingGroups(int(group))
    else:
        getListOrganisingGroups(int(groups))

def getListChildrensFromOrder(group):
    global g_inp, group_id_val
    g_inp = group

    group_id_val = groups[int(group)]['id']

    new_url = 'https://booking.dop29.ru/api/rest/order?_dc=1695285515100&page=1&start=0&length=25&extFilters=[{"property":"fact_academic_year_id","value":'+YEAR+',"comparison":"eq"},{"property":"event_id","value":'+ groups[g_inp]['event_id'] +',"comparison":"eq"},{"property":"fact_group_id","value":"' + str(group_id_val) + '","comparison":"eq"},{"property":"state","value":["approve"],"comparison":"in"}]'

    r = session.get(new_url, headers={
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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
    })
    b = json.loads(r.text)
    list_childrens = b['data']
    list_names = []
    for children in list_childrens:
        url_child = 'https://booking.dop29.ru/api/rest/kid/'+children['kid_id']
        r = session.get(url_child, headers={
            'Host': 'booking.dop29.ru',
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': 'Bearer ' + access_token,
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
        })
        child = json.loads(r.text)['data'][0]
        list_names.append(child['last_name'] + " " + child['first_name'] + " " + child['patro_name'])

    file = open(dir + '\\' + "Подтверждённые заявки " + groups[g_inp]['program_name'] + ' ' + groups[g_inp]['name'] + '.txt', 'w',
                encoding="utf-8")
    file.write("\n".join(list_names))
    file.close()

def getListChildrensFromOrderAnyGroups(groups):
    groups = groups.split(" ")
    for group in groups:
        getListChildrensFromOrder(int(group))


#Типы занятий
#Практическая работа 9732
#Учебное 7198
#Дистанционное 3022
#
def close_day(date, theme, type, description):
    percentagevisits = 80
    global g_inp, group_id_val
    group_id_val = groups[int(g_inp)]['id']
    group_id = groups[int(g_inp)]['id']

    childrens = get_childrens()

    headers = {
        'Host': 'booking.dop29.ru',
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + access_token,
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

    for c in childrens:
        visit = random.randint(0, 100)
        if visit < percentagevisits:
            visit = True
        else:
            visit = False
        kid_id = c['kid_id']
        day_url_POST = "https://booking.dop29.ru/api/attendance/save" #date group_id kid_id value:true
        payload = {'date':date,'group_id':group_id, 'kid_id':kid_id, 'value':visit}
        r = session.post(url=day_url_POST, headers=headers, data=json.dumps(payload))
        b = json.loads(r.text)
        #print(b["success"])

    KTP_url_POST = "https://booking.dop29.ru/api/event-group-lessons/upsert"# date group_id types:list description

    payload = json.loads(json.dumps({'data':{'date':date + ' 00:00:00', 'group_id': group_id,'theme': theme ,'types': [str(int(type))], 'description': description}}))
    #payload = '{"data":{"group_id":"25849","date":"2023-09-05 00:00:00","types":["9732"]}}'
    r = session.post(url=KTP_url_POST, headers=headers, json=payload)
    b = json.loads(r.text)
    #print(b["success"])
    pass


FILTER = False

filter_choise = int(input("Режим фильтра 0 - нет, 1 - да: "))

if filter_choise == 1:
    f = open("groups.ini")
    id_filters = f.read().splitlines()
    f.close()

    filtred_groups = []

    for g in groups:
        pass
        if g['id'] in id_filters:
            filtred_groups.append(g)
    groups = filtred_groups

    filter_teachers = int(input("Фильтр по педагогам 0 - нет, 1 - да: "))

    if filter_teachers == 1:
        teachers = {}
        for g in groups:
            if teachers.get(g["teacher"]) is not None:
                teachers[g["teacher"]].append(g)
            else:
                teachers[g["teacher"]] = []
                teachers[g["teacher"]].append(g)

        keys = []
        for t in teachers:
            keys.append(t)

        print("Список педагогов")
        for i in range(0, len(keys)):
            print("{0} {1}".format(i, keys[i]) )

        teacher_groups = input("Группы каких педагогов выбрать? Можно через пробел указать ").split(' ')

        groups = []

        for t in teacher_groups:
            groups.extend(teachers[keys[int(t)]])

        print("Выбраны {0} групп".format(len(groups)))

choose = input('0 Печать информации детей\n'
               '1 Печать журнала\n'
               '2 Печать списка организованных групп\n'
               '3 Печать статистики по возрастам\n'
               '4 Печать списка из заявок (Когда зачисления ещё нет, но хочется получить список)\n'
               '5 ! Внести в навигатор свои грязные буквы')

i = 0
if choose == '1':
    print('Группы')
    for g in groups:
        i = i + 1
        print(str(i) + ' ' + g['program_name'] + ' ' + g['id'] + " " + g['name'])
    print("-1 ПЕЧАТЬ ВСЕХ")
    print('Какую группу вывести на печать? ')
    g_inp = int(input())
    if g_inp != -1:
        group_id_val = groups[g_inp]['id']
        printGroup()
    else:
        for i in range(0, len(groups)):
            g_inp = i
            group_id_val = groups[i]['id']
            printGroup()
if choose == '0':
    print('Группы')
    for g in groups:
        i = i + 1
        print(str(i) + ' ' + g['program_name'] + ' ' + g['id'] + " " + g['name'])
    print('Какую группу вывести на печать? ')

    groupss = input().split(' ')

    group = int(groupss[0])
    if group != -1:
        for group in groupss:
            g_inp = int(group)
            group_id_val = groups[g_inp]['id']
            printChildren()
    else:
        for i in range(0, len(groups)):
            g_inp = i
            group_id_val = groups[i]['id']
            printChildren()

if choose == '2':
    print('Группы для генерации списка организованных групп: \n')
    for g in groups:
        i = i + 1
        print(str(i) + ' ' + g['program_name'] + ' ' + g['id'] + " " + g['name'])
    getListOrganisingGroupsAnyGroup(input('Выберите группу'))


if choose == '3':
    stat_of_ages()

if choose == '4':
    print('Группы')
    for g in groups:
        i = i + 1
        print(str(i) + ' ' + g['program_name'] + ' ' + g['id'] + " " + g['name'])
    print('Какую группу вывести на печать? ')
    getListChildrensFromOrderAnyGroups(input())

if choose == '5':
    filename = input("Введи название файла плес")
    df = pd.read_excel(filename) #25849.xlsx

    #for row in df.itertuples():
        #if not pandas.isnull(row[2]):
            #print("{0} {1} {2} {3}".format(row[2],row[3],row[4],row[5]))

    print('Группы')
    for g in groups:
        i = i + 1
        print(str(i) + ' ' + g['program_name'] + ' ' + g['id'] + " " + g['name'])

    g_inp = int(input("Выбери группу"))-1

    print("Статус:",end="")

    for row in df.itertuples():
        if not pandas.isnull(row[2]):
            close_day(row[2].strftime('%Y-%m-%d'), row[3], row[4], row[5])
            print("\rСтатус: {0}".format(str(row[2])), end="")
    pass