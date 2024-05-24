import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

import exceptions as ex


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
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }

    missing_tokens = [
        name for name, token in tokens.items() if not token
    ]
    if missing_tokens:
        msg = f'Отсутствуют необходимые токены:{", ".join(missing_tokens)}'
        logger.critical(msg)
        return False
    logger.debug('Все токены на месте.')
    return True


def send_message(bot, message):
    """Отправка сообщений в телеграмм."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        logger.debug('Начало отправки сообщение.')
        bot.send_message(
            chat_id=chat_id,
            text=message,
        )
        logger.debug('Сообщение успешно отправлено.')
    except ApiException as error:
        msg = 'Ошибка при отправке, сообщение не было отправлено'
        logger.error(f'{msg}{error}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logger.debug(
        'Начало запроса к API: '
        'URL={url}, Headers={headers}, Params={params}'.format(
            **request_params
        )
    )
    try:
        response = requests.get(**request_params)
    except requests.RequestException:
        raise ex.EndpointAccessError
    if response.status_code != HTTPStatus.OK:
        raise ex.UnexpectedStatusCodeError
    return response.json()


def check_response(response):
    """Проверяет ответ API."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise ex.EmptyResponseAPI('Ошибка, некорректный формат данных.')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный тип данных. Ожидался List.')
    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных.Ожидался Dict.')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None:
        raise ex.EmptyKeyOrValue('Ошибка, пустое homework_name.')
    if status is None:
        raise ex.EmptyKeyOrValue('Ошибка, пустой status.')
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        message = 'Ошибка, неизвестный  статус.'
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Отсутствуют необходимые токены')
    bot = TeleBot(token=TELEGRAM_TOKEN)
    send_message(bot, 'Успешный запуск бота.')
    timestamp = 0
    old_status = None

    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date', timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                new_status = parse_status(homework)
                message = new_status
            else:
                message = 'Никаких обновлений нет.'

            if old_status != message:
                send_message(bot, message)
                old_status = message
                logger.debug('Проверка успешно завершена.')

        except ex.APIError as error:
            msg = f'Сбой в работе программы:{error}'
            logger.error(msg)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
