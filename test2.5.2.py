import json
import requests
import random
import file


org_id = file.cfg.org_id
space = file.cfg.space
file_name = file.cfg.file_name
token = {
    'Authorization': file.cfg.token
}


def open_file(file_name):
    """Открываем файл в json формате с пользователями, с которыми нужно сделать действия"""
    with open(file_name, 'r', encoding='utf-8') as f:
        file_json = json.load(f)
    return file_json


def create_password():
    """ Создаем 10-ти значный пароль, в котором обязательно есть одна цифра, строчная и заглавные буквы """
    password = str('')
    g = (random.randint(1, 3), random.randint(4, 6), random.randint(7, 10))
    '''Cоздаем лист из 3 случайных цифр, на месте которых по счету будет стоять
    заглавная или строчная буквы и цифра. Это нужно, чтобы удовлетворить минимальную сложность
    пароля для корпоративной почты яндекса'''
    for i in range(1, 11):
        if i == g[0]:
            password += chr(random.randint(48, 57))  # случайная цифра от 0 до 9 с 1 символа до 3 в пароле
        elif i == g[1]:
            password += chr(random.randint(65, 90))  # случайная заглавная буква с 4 по 6 символ в пароле
        elif i == g[2]:
            password += chr(random.randint(97, 122))  # случайная строчная буква с 7 по 10 символ в пароле
        else:
            # аналогичный механизм с остальными 7 символами пароля
            a = random.randint(1, 3)
            if a == 1:
                password += chr(random.randint(65, 90))
            elif a == 2:
                password += chr(random.randint(97, 122))
            elif a == 3:
                password += chr(random.randint(48, 57))
        i += 1
    return password


def create_user(token, body_requests, org_id):
    """ Запрос на создания пользователя """
    url = f'https://api360.yandex.net/directory/v1/org/{org_id}/users'
    responce = requests.post(url, headers=token, json=body_requests)
    return responce.status_code


def show_users(token, org_id):
    """ Запрос на перечень логина и id пользователя """
    url = f'https://api360.yandex.net/directory/v1/org/{org_id}/users'
    list_name = dict()
    body = {
        'perPage': 1000,
    }
    responce = requests.get(url, headers=token, params=body).json()  # тестовый запрос, чтобы узнать кол-во страниц
    last_page = responce['pages']  # в этом ключе хранится информация о кол-ве страниц запроса
    for i in range(1, last_page + 1):
        body['page'] = i  # создаем ключ с значением страниц
        responce = requests.get(url, headers=token, params=body).json()
        for users in responce['users']:
            list_name[users['nickname']] = users['id']
        del body['page']  # удаляем ключ с значением страниц
    return list_name


def show_departament(token, org_id):
    """ запрашиваем департаменты и их id """
    url = f'https://api360.yandex.net/directory/v1/org/{org_id}/departments'
    info_departaments = dict()
    body = {
        'perPage': 1000,
        'type_sort': 'id'
    }
    responce = requests.get(url, headers=token, params=body).json()
    last_page = responce['pages']
    # реализация перелистывания страниц аналогична функции show_users
    for i in range(1, last_page + 1):
        body['page'] = i
        responce = requests.get(url, headers=token, params=body).json()
        for id_name in responce['departments']:
            info_departaments[id_name['name']] = id_name['id']
        del body['page']
    return info_departaments


def dismissal_user(token, id_user, org_id):
    url = f'https://api360.yandex.net/directory/v1/org/{org_id}/users/{id_user}'
    body_requests = {
    'isEnabled': 'true'
    }
    # ключ isEnabled отвечает за блокировку учетки корп. почты яндекса
    responce = requests.patch(url, headers=token, params=body_requests)
    return int(responce.status_code)


def generate_quests(file_json, token):
    info_dep = show_departament(token=token, org_id=org_id)
    list_name = show_users(token=token, org_id=org_id)
    for user in file_json:
        error = False
        if user.get('action') == None:  # проверка на содержание ключа action, если нет - ошибка
            print(f'ОШИБКА ACTION !!! ОШИБКА ACTION !!! ОШИБКА ACTION\n{user}')
            error = True
        if user.get('login') != None:  # проверка на содержание ключа login, если нет - ошибка
            login_user = user['login']
        else:
            print(f'ОШИБКА ЛОГИНА !!! ОШИБКА ЛОГИНА !!! ОШИБКА ЛОГИНА\n{user}')
            error = True
        if user.get('login') == '':  # проверка на пустое поле, если будет пустым - ошибка
            error = True
            print(f'Поле логина пустое, нет возможности добавить или уволить сотрудника\n{user}')
        if user.get('employee_name') != None\
            and user.get('employee_surname') != None\
            and user.get('employee_patronymic') != None:  # проверка на содержание ключей связаных с ФИО
            employee_name = user['employee_name']
            employee_surname = user['employee_surname']
            employee_patronymic = user['employee_patronymic']
        else:
            print(f'ОШИБКА ФИО !!! ОШИБКА ФИО !!! ОШИБКА ФИО\n{user}')
            error = True
        '''Проверяется сразу наличие ключа subdivision, а также содержание значения этого ключа в 
        списке всех департаментов. Если отсутствует - ошибка'''
        if info_dep.get(user.get('subdivision')) != None:
            dep_name_json = user['subdivision']
            departament_ID = info_dep[dep_name_json]
        else:
            error = True
            print(f'ОШИБКА ДЕПАРТАМЕНТА !!! ОШИБКА ДЕПАРТАМЕНТА !!! ОШИБКА ДЕПАРТАМЕНТА\n{user}')
        if not error:
            if user['action'] == 'dismissal':  # увольняем сотрудника
                responce = dismissal_user(token=token, id_user=list_name[login_user], org_id=org_id)
                if responce == 200:
                    print(f'УСПЕХ ув !!! УСПЕХ ув !!! УСПЕХ ув\n{user}')
                else:
                    print(f'ОШИБКА ЗАПРОСА ув !!! ОШИБКА ЗАПРОСА ув!!! ОШИБКА ЗАПРОСА ув\n{user}\n{responce}')

            elif user['action'] == 'recruitment':  # добавляем сотрудника
                user_password = create_password()
                body_requests = {
                    "departmentId": departament_ID,
                    "name": {
                        "first": employee_name,
                        "last": employee_surname,
                        "middle": employee_patronymic
                    },
                    "nickname": login_user,
                    "password": user_password
                }
                responce = create_user(token=token, body_requests=body_requests, org_id=org_id)
                if responce == 200:
                    print(f'УСПЕХ доб !!! УСПЕХ доб !!! УСПЕХ доб\n{user}\nЛогин: {login_user} Пароль: {user_password}')
                else:
                    print(f'ОШИБКА ЗАПРОСА доб !!! ОШИБКА ЗАПРОСА доб !!! ОШИБКА ЗАПРОСА доб\n{user}\n{responce}')
            else:
                print(f'ОШИБКА ключа action !!! ОШИБКА ключа action !!! ОШИБКА ключа action\n{user}')
        print('\n **************************** \n')
    return





if __name__ == '__main__':
    generate_quests(token=token, file_json=open_file(file_name))

'''Возможно в будущем пригодится'''

# def create_departament(token, body, org_id):
#     """Создаем запрос для создания департамента (подразделения)"""
#     url = f'https://api360.yandex.net/directory/v1/org/{org_id}/departments'
#     responce = requests.post(url, headers=token, json=body)
#     return responce.status_code

