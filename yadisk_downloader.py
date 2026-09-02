import requests
from urllib.parse import urlencode
import csv
import os
import zipfile
from urllib.parse import unquote

from cli import parse_args


def get_href(public_link):
    """
    Получение ссылки для скачивания
    """
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
    final_url = base_url + urlencode(dict(public_key=public_link))
    response = requests.get(final_url)
    parse_href = response.json()['href']
    return parse_href


def get_type(public_link):
    """
    Получает тип файла: файл или папка.
    """
    resources = "https://cloud-api.yandex.net/v1/disk/public/resources?"
    requests_url = resources + urlencode(dict(public_key=public_link))
    r = requests.get(requests_url)
    type_file = r.json()['type']
    info = r.json()
    items = info['_embedded']['items']
    return type_file


def get_valid_files(public_link):
    resources = "https://cloud-api.yandex.net/v1/disk/public/resources?"
    requests_url = resources + urlencode(dict(public_key=public_link))
    r = requests.get(requests_url)
    json_string = r.json()
    if 'error' in json_string.keys():
        print(json_string['message'])
        return '', []
    type_file = r.json()['type']
    info = r.json()
    try:
        items = info['_embedded']['items']
    except:
        items = []
    return info['name'], items

def download_files(url, name_folder):
    currient_folder = os.getcwd()
    destination_folder = os.path.join(currient_folder, "download_files", name_folder)
    destination_folder = destination_folder.replace("\"", "'")
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    start_filename = url.find('filename=')
    end_filename = url[start_filename:].find('&')
    end_name = start_filename + end_filename
    filename = url[start_filename:end_name][9:]


    filename = unquote(filename, 'cp1251')
    try:
        filename = filename.encode('cp1251').decode('utf-8')
    except:
        pass
    download_url = requests.get(url)
    final_link = os.path.join(destination_folder, filename)
    with open(final_link, 'wb') as ff:
        ff.write(download_url.content)

    print("Скачан файл: ", name_folder)


    return final_link


def unzip_files(path_to_zip):
    """
    Распаковывает файлы в папку unzip_files
    """
    cur_path = os.getcwd()
    dest_unzip = 'unzip_files'
    path_to_folder, filename = os.path.split(path_to_zip)
    name, extention = os.path.splitext(filename)

    name = unquote(name, 'cp1251')
    name = name.encode('cp1251').decode('utf-8')

    with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
        zip_ref.extractall(dest_unzip)

    return [
        os.path.join(cur_path, dest_unzip, name, file)
        for file in os.listdir(os.path.join(dest_unzip, name))
    ]


def read_file(file_path):
    """
    Чтение ссылок из файла csv.
    """

    list_urls = list()

    try:
        with open(file_path, 'r', encoding='utf-8', newline="") as read_file:
            reading = csv.reader(read_file)
            for row in reading:
                list_urls.append(str(*row).strip())
        return list_urls

    except FileNotFoundError:
        print("Файл не найден!")


def main():
    file_result = 'result_data.csv'

    if os.path.exists(file_result):
        os.remove(file_result)

    for href in read_file(parse_args()):
        with open(file_result, 'a', encoding="utf-8", newline="") as csv_write:
            writer = csv.writer(csv_write, delimiter=",")

            items = get_valid_files(href)
            if len(items) > 0:
                for item in items[1]:
                    if '.pdf' in item['name'] or '.doc' in item['name'] or '.docx' in item['name'] or \
                            '.jpg' in item['name'] or '.png' in item['name']:
                        download_files(item['file'], items[0])

    print("Well Done!")


if __name__ == "__main__":
    main()

