import logging
import os
import sys
import requests
import time
from http import HTTPStatus

from telebot import TeleBot
from dotenv import load_dotenv

from exceptions import EmptyKeyOrValue, StatusAccessError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
formatter = ('%(asctime)s, %(levelname)s, %(message)s')
handler = logging.StreamHandler(sys.stdout)
level = logger.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """
    Проверяет доступность переменных окружения.
    которые необходимы для работы программы.
    """
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    for token in tokens:
        if not token:
            token_error = 'Отсутствуют необходимые токены.\
                Программа завершена.'
            logger.critical(token_error)
            return False
    return True


def send_message(bot, message):
    """Отправка сообщений в телеграмм."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(
            chat_id=chat_id,
            text=message,
        )
        logger.debug('Сообщение успешно отправлено.')
    except Exception as error:
        msg = 'Ошибка при отправке, сообщение не было отправлено'
        logger.error(f'{msg}{error}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {'form_data': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logger.error(
            f'Ошибка при запросе к единственному эндпоинту API: {error}'
        )
        return None
    if response.status_code != HTTPStatus.OK:
        logger.error(f'Ошибка: Неожиданный статус-код {response.status_code}\
            при запросе к API')
        raise StatusAccessError('Проблема с доступом к ENDPOINT.')
    return response.json()


def check_response(response):
    """Проверяет ответ API."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        msg = 'Ошибка, api не содержит ключа "homeworks".'
        logger.error(msg)
        raise KeyError
    if not isinstance(homeworks, list):
        logger.error('Ошибка, тип данных не соответствуют ожидаемому.')
        raise TypeError
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None:
        homework_error = 'Ошибка, homework_name не найден!'
        logger.error(homework_error)
        raise EmptyKeyOrValue
    if status is None:
        status_error = 'Ошибка, status не найден!'
        logger.error(status_error)
        raise EmptyKeyOrValue
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        message = 'Ошибка, неизвестный  статус.'
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        return
    bot = TeleBot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text='Бот успешно запущен!'
        )
    except Exception as error:
        message = f'Ошибка при отправке уведомления о запуске бота: {error}'
        logger.error(message)

    timestamp = 1716110891
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                if homework is not None:
                    message = parse_status(homework)
                    if message:
                        send_message(bot, message)
            logger.debug('Никаких обновлений нет.')
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
