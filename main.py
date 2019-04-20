# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pymysql.cursors

sys.path.insert(0, '../')

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import pyqiwi

import vk_api
from datetime import datetime
import random
import data
from datetime import datetime, timedelta
import random_code
import time
import vkcoin
# vk_session = vk_api.VkApi(login, password)
# vk_session.auth()

vk_session = vk_api.VkApi(token=data.token_group())

vk = vk_session.get_api()

longpoll = VkLongPoll(vk_session)
merchant = vkcoin.VKCoinApi(user_id=data.id_user(), key=data.token_coin())
print('мой балланс ' + str(merchant.get_my_balance()['response'][str(data.id_user())]))

status_buy = False
change_price = False
rate = 15000 # Сколько за 1 рубль
cost = 70 # Цена за 1кк



def connection():
    connect = pymysql.connect(host='localhost',
                              user='root',
                              password='',
                              db='db_bot',
                              charset='utf8mb4',
                              cursorclass=pymysql.cursors.DictCursor
                              )
    # with connect.cursor() as cursor:
    #     cursor.execute("""show tables""")
    #     print(cursor.fetchall())
    #     cursor.execute("""insert into users (some_text) value('Пример')""")
    # connect.commit()
    # with connect.cursor() as cursor:
    #     cursor.execute("""select * from users;""")
    #     print(cursor.fetchall())
    # connect.close()
    return connect

def success_pay(id, sum, txnid):
    print('Отправляю коины сюда' + str(id) + 'в кол-ве = ' + str(round(sum*rate*1000)))
    print(str(id))
    print(str(round(sum*rate*1000)))
    merchant.send_coins(int(id), round(sum*rate*1000))
    vk.messages.send(peer_id=id, random_id=random.randint(-2147483648, +2147483648),
                     message='Проверь свой баланс.')
    # change_transaction(connection(), txnid, 'coin', str(round(sum*rate*1000)))
    # change_transaction(connection(), txnid, 'amount', str(sum))
    connect = connection()
    with connect.cursor() as cursor:
        cursor.execute("""UPDATE all_transaction SET coin=%s WHERE (txnId=%s)""" % (str(round(sum*rate*1000)), txnid))
        cursor.execute("""UPDATE all_transaction SET amount=%s WHERE (txnId=%s)""" % (str(sum), txnid))
    connect.commit()


def check_pay(user_id, txnid):

    wallet = pyqiwi.Wallet(token=data.token_qiwi(), number='79515347276')
    history_pay = wallet.history(rows=10, operation='IN',
                                 start_date=datetime.now().replace(hour=datetime.now().hour - 1),
                                 end_date=datetime.now())
    for key in history_pay['transactions']:
        sum = key.raw['sum']['amount']
        number = key.raw['account'][1:]
        date_pay = key.raw['date']
        comment = key.raw['comment']

        print('=' * 100)
        print('Номер: ' + str(number))
        print('Сумма: ' + str(sum))
        print('txnId: ' + str(key.raw['txnId']))

        if (comment.lower() == 'auto' or comment.lower() == 'avto') and str(key.raw['txnId']) == txnid:
            if search_transaction(connection(), txnid) != () and search_transaction(connection(), txnid)[0]['status'] == False:
                success_transaction(connection(), key.raw['txnId'])
                success_pay(user_id, sum, txnid)
        print('=' * 100)
def show_pay():
    print('123')
    wallet = pyqiwi.Wallet(token=data.token_qiwi(), number='79515347276')
    history_pay = wallet.history(rows=10, operation='IN',
                                 start_date=datetime.now().replace(hour=datetime.now().hour - 6),
                                 end_date=datetime.now())

    for key in history_pay['transactions']:
        sum = key.raw['sum']['amount']
        number = key.raw['account']
        date_pay = key.raw['date']
        comment = key.raw['comment']

        print('Сумма платежа:     ' + str(sum))
        print('Номер отправителя: ' + str(number))
        print('Время: ' + str(date_pay[0:10]) + ' ' + str(date_pay[11:16]))
        print('TxnId: ' + str(key.raw['txnId']))
        print('Комментарий: ' + str(comment))
        print('=' * 30)

def add_user(connect, user_id):
    with connect.cursor() as cursor:
        gen = random_code.gen()
        sql = "INSERT INTO users (id, status_bot, status_buy) VALUES (%s, TRUE, FALSE)"
        val = (user_id)
        cursor.execute(sql, val)
        print('user add!')
    connect.commit()

def search_user(connect, id):
    user_id = id
    with connect.cursor() as cursor:
        cursor.execute("""SELECT * FROM users WHERE (id=%s)"""%user_id)
    return cursor.fetchall()

def return_user(connect, user_id):
    with connect.cursor() as cursor:
        cursor.execute("""SELECT * FROM users WHERE (id=%s)""" % user_id)
        connect.close()
    return cursor.fetchall()[0]

def change_user(connect, user_id, name_colomn, value):
    with connect.cursor() as cursor:
        cursor.execute("""UPDATE users SET %s=%s WHERE (id=%s)""" % (name_colomn, value, user_id))
    connect.commit()

def search_transaction(connect, txnId):
    with connect.cursor() as cursor:
        cursor.execute("""SELECT * FROM all_transaction WHERE (txnId=%s)""" % txnId)
    return cursor.fetchall()

def add_transaction(user_id, txnid):
    if search_transaction(connection(), txnid) == ():
        connect = connection()
        with connect.cursor() as cursor:
            sql = "INSERT INTO all_transaction (to_user, txnId) value (%s, %s)"
            val = (user_id, txnid)
            cursor.execute(sql, val)
            print('add transaction!')
            # time.sleep(1)
        connect.commit()
        check_pay(user_id, txnid)

    elif search_transaction(connection(), txnid) != () and search_transaction(connection(), txnid)[0]['status'] == 0:
        check_pay(user_id, txnid)




def success_transaction(connect, txnid):
    with connect.cursor() as cursor:
        cursor.execute("""UPDATE all_transaction SET status=TRUE WHERE (txnId=%s)""" % (txnid))
    connect.commit()

# def change_transaction(connect, txnid, name_colomn, value):
#     print('Меняю ' + str(name_colomn))
#     with connect.cursor() as cursor:
#         cursor.execute("""UPDATE all_transaction SET %s=%s WHERE (id=%s)""" % (name_colomn, value, txnid))
#     connect.commit()
#     print(str(search_transaction(connection(), txnid)))

# Изменение цены за 1кк


# Генератор клавиатуры
def create_keyboard(response, user_id):
    global status_buy
    keyboard = VkKeyboard(one_time=False)

    if response == "/help" or response == "!начать" or response == "!старт" or response == "старт" or response == "начать" or response == "/start" or response == "start" or response == "!start" or response == "команды" or response == "!команды" or response == "/команды":
        keyboard.add_button('Купить', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Продать', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Пруфы', color=VkKeyboardColor.POSITIVE)

        keyboard.add_line()

        keyboard.add_button('Отключить бота', color=VkKeyboardColor.NEGATIVE)

    if response == "назад" and return_user(connection(), user_id)['status_bot']:
        keyboard.add_button('Купить', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Продать', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Пруфы', color=VkKeyboardColor.POSITIVE)

        keyboard.add_line()

        keyboard.add_button('Отключить бота', color=VkKeyboardColor.NEGATIVE)

    elif response == 'купить':
        keyboard.add_button('100к', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('500к', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('1кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('5кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Другое', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)

    elif response == 'продать':
        keyboard.add_button('До 1кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('1кк-5кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('5кк-15кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('От 15кк', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)

    elif response == '/admin' and not status_buy and (
            user_id == 269593957 or user_id == 299405534 or user_id == 150297123):
        keyboard.add_button('Активировать закупку', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Изменить цену за 1кк', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    elif response == '/admin' and status_buy and (
            user_id == 269593957 or user_id == 299405534 or user_id == 150297123):
        keyboard.add_button('Дезактивировать закупку', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Изменить цену за 1кк', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)

    elif (response == '/admin' or response == 'дезактивировать закупку') and status_buy and (
            user_id == 269593957 or user_id == 299405534 or user_id == 150297123):
        if response == 'дезактивировать закупку':
            status_buy = False
        keyboard.add_button('Активировать закупку', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Изменить цену за 1кк', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    elif (response == '/admin' or response == 'активировать закупку') and not status_buy and (
            user_id == 269593957 or user_id == 299405534 or user_id == 150297123):
        if response == 'активировать закупку':
            status_buy = True
        keyboard.add_button('Дезактивировать закупку', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Изменить цену за 1кк', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)

    elif (response == 'отключить бота') or (response == 'назад' and not return_user(connection(), user_id)['status_bot']):
        return keyboard.get_empty_keyboard()


    keyboard = keyboard.get_keyboard()
    return keyboard

# Поиск событий
def event_listen():
    global rate, change_price, cost
    while True:
        # Поиск событий
        for event in longpoll.listen():
            # Событие - Новое сообщение
            if event.type == VkEventType.MESSAGE_NEW:
                tomorrow = datetime.strftime(datetime.now() + timedelta(days=1), "%d%m%Y")

                # Проверка, есть ли пользователь в базе
                if search_user(connection(), event.user_id) == ():
                    print('Adding')
                    add_user(connection(), event.user_id)

                # Проверка, первое ли сообщение
                if vk.messages.search(peer_id=event.user_id, date=tomorrow, count=1)['count'] == 1:
                    vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                     message='Здравствуй! Мы рады видеть тебя здесь. Скорее пиши "Старт", чтобы активировать бота.')
                else:

                    # print(return_user(connection(), event.user_id)['status_bot'])
                    # print('Сообщение пришло в: ' + str(datetime.strftime(datetime.now(), "%H:%M:%S")))
                    # print('Текст сообщения: ' + str(event.text))
                    # print(event.user_id)
                    response = event.text.lower()
                    keyboard = create_keyboard(response, event.user_id)

                    # Покупка
                    if event.from_user and not event.from_me:
                        print('Проверка на транзакцию')
                        if response[0:4] == "tran" and return_user(connection(), event.user_id)['status_bot'] and response[4:16].isdigit():
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Если все сделанно правильно, то тебе уже пришли коины.)')
                            add_transaction(event.user_id, response[4:16])

                    # Основные команды
                    if event.from_user and not event.from_me:
                        if response == "/help" or response == "!начать" or response == "!старт" or response == "старт" or response == "начать" or response == "/start" or response == "start" or response == "!start" or response == "команды" or response == "!команды" or response == "/команды":
                            change_user(connection(), event.user_id, 'status_bot', True)
                            change_user(connection(), event.user_id, 'status_buy', False)
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Другие доступные команды: \n\nКупить - Данная команда вызывает инструкцию для покупки VKCs.\n\nПродать - Данная подсказка вызывает инструкцию, которая помогает вам продать нам VKCs.\n\nПруфы - Данная команда предоставит вам доказательство, что мы не мошенники.\n\nСтатус - статус закупки.',
                                             keyboard=keyboard)

                        elif response == "купить" and return_user(connection(), event.user_id)['status_bot']:
                            change_user(connection(), event.user_id, 'status_buy', True)
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Отлично! \nКурс: 1р - 15к (1кк - 70р).\nИнструкция для покупки в автомотическом режиме(Через бота):\n1) Читай внимательно!\n2) Переводи на qiwi +79515347276 любую сумму начиная с 1р, указав комментарий - "auto". Без ковычек.\n3) Отправь сюда номер транзакции(квитанции) в формате: tran00000000000 . Пиши "/транзакция", если хочешь увидеть инструкцию, как найти номер транзакции.\n4) Проверь свой счет VKC.\nЕсли возникли какие-либо вопросы или вы хотите приобрести товар через администратора, пишите сюда: https://vk.com/chyika2015\n\nP.S \nЕсли вы перевели деньги на номер телефона, а не на qiwi - VKCs не прийдет. Будьте внимательнее! \nОплата на сбер, доступна только при покупке через администатора.',
                                             keyboard=keyboard)

                        elif response == "продать" and return_user(connection(), event.user_id)['status_bot']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Выберите сумму, которую хотите продать. Обязательно приложите скрин, доказывающий наличиe указанной суммы на вашем балансе.',
                                             keyboard=keyboard)

                        elif response == 'пруфы' and return_user(connection(), event.user_id)['status_bot']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Все пруфы можно найти в обсуждениях группы.\nОбсуждения - https://vk.com/board151512230')

                        elif response == '/транзакция' and return_user(connection(), event.user_id)['status_bot']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Для ПК:\n1) Перейти на сайт https://qiwi.com/main\n2) Авторизоваться\n3) Найти пункт "Последние платежи" на главной странице. (Опуститься чуть вниз)\n4) Кликнуть по нужнной транзакции и в ее описании найти пункт "Номер квитанции"\n5) Номер транзакции найден.\n\nДля мобильного приложения:\n1) Запустить приложение\n2) Перейти во вкладку "История" (Снизу экрана)\n3) Нажать по нужнной транзакции и в ее описании найти пункт "Номер транзакции"\n5) Номер транзакции найден.')

                        elif response == "статус" and return_user(connection(), event.user_id)['status_bot']:
                            if status_buy:
                                msg = 'Закупка активна'
                            else:
                                msg = 'Закупка приостановлена'

                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message=msg)

                        elif (response == 'отключить бота' and return_user(connection(), event.user_id)['status_bot']) or (response == 'назад' and not return_user(connection(), event.user_id)['status_bot']):
                            change_user(connection(), event.user_id, 'status_bot', False)
                            change_user(connection(), event.user_id, 'status_buy', False)
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Если вы хотите снова включить бота, напишите "Старт"',
                                             keyboard=keyboard)

                        elif response == 'назад' and return_user(connection(), event.user_id)['status_bot']:
                            change_user(connection(), event.user_id, 'status_buy', False)
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Выберите действие.', keyboard=keyboard)

                    # Товары
                    if event.from_user and not event.from_me:
                        if response == '100к' and return_user(connection(), event.user_id)['status_buy']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='https://vk.com/market-151512230?w=product-151512230_2423932')
                        elif response == '500к' and return_user(connection(), event.user_id)['status_buy']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='https://vk.com/market-151512230?w=product-151512230_2423937%2Fquery')
                        elif response == '1кк' and return_user(connection(), event.user_id)['status_buy']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='https://vk.com/market-151512230?w=product-151512230_2423940%2Fquery')
                        elif response == '5кк' and return_user(connection(), event.user_id)['status_buy']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='https://vk.com/market-151512230?w=product-151512230_2428516%2Fquery')
                        elif response == 'другое' and return_user(connection(), event.user_id)['status_buy']:
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message='Пиши сюда указав сумму, которую хочешь купить - https://vk.com/chyika2015')

                    # Ответ на товар
                    if event.from_user and not event.from_me:
                        if status_buy == True:
                            msg = 'Ожидайте ответа, я позвал администратора.'
                        else:
                            msg = 'Простите, но в данный момент скупка приостановлена.'
                        if response == 'до 1кк':
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message=msg)
                        elif response == '1кк-5кк':
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message=msg)
                        elif response == '5кк-15кк':
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message=msg)
                        elif response == 'от 15кк':
                            vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                             message=msg)

                    # Админ панель
                    try:
                        if event.from_user and not event.from_me and (
                                event.user_id == 269593957 or event.user_id == 299405534 or event.user_id == 150297123):
                            if response == '/admin':
                                vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                                 message='Админ-панель активирована.', keyboard=keyboard)
                            elif response == 'активировать закупку' and status_buy:
                                vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                                 message='Статус закупки успешно изменен.', keyboard=keyboard)
                            elif response == 'дезактивировать закупку' and not status_buy:
                                vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                                 message='Статус закупки успешно изменен.', keyboard=keyboard)
                            elif response == 'изменить цену за 1кк':
                                change_price = True
                                vk.messages.send(peer_id=event.user_id, random_id=random.randint(-2147483648, +2147483648),
                                                 message='Введите цену.')
                            elif change_price == True:
                                if response.isdigit():
                                    rate = round(1000000/int(response))
                                    cost = int(response)
                                    change_price = False

                    except:
                        print('Error!!!!')
                    print('-' * 30)

if __name__ == '__main__':

    connection()
    # show_pay()
    event_listen()
