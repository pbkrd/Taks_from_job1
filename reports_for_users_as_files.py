import os

import requests as rq

from datetime import datetime as dt

OUT_DIR = 'tasks'
PATH_TO_DIR = f'{os.getcwd()}/{OUT_DIR}'
API_BASE = 'https://json.medrocket.ru'
USERS_URL = API_BASE + '/users'
TASKS_URL = API_BASE + '/todos'
MAX_LEN_TITLE_TASK = 48


def get_data_from_api(url):
    try:
        response = rq.get(url)
        return response.json()
    except Exception as e:
        print(f'Ошибка при загрузке страницы: {str(e)}')


def check_user_bound_keys(user):
    for k in ('id', 'name', 'username', 'email', 'company'):
        if k not in user:
            return False
    return True


def check_task_bound_keys(task):
    for k in ('userId', 'title', 'completed'):
        if k not in task:
            return False
    return True


def check_len_title(title):
    if len(title) > MAX_LEN_TITLE_TASK:
        title = title[:MAX_LEN_TITLE_TASK] + '...'
    return title


def get_tasks_of_users(tasks):
    tasks_of_users = {}
    for task in tasks:
        if check_task_bound_keys(task):
            if task['completed']:
                tasks_of_users.setdefault(task['userId'], {}).setdefault('completed', []).append(task['title'])
            else:
                tasks_of_users.setdefault(task['userId'], {}).setdefault('uncompleted', []).append(task['title'])
    return tasks_of_users


def get_report_for_user(user, tasks_of_users):
    index = user['id']
    completed = uncompleted = []

    if tasks_of_users.get(index, None):  # Проверка на наличие задач у пользователя
        if tasks_of_users[index].get('completed', None):  # Проверка на наличие завершенных задач
            completed = list(map(check_len_title, tasks_of_users[index]['completed']))
        if tasks_of_users[index].get('uncompleted', None):  # Проверка на наличие оставшихся задач
            uncompleted = list(map(check_len_title, tasks_of_users[index]['uncompleted']))

    amount_completed, amount_uncompleted = len(completed), len(uncompleted)
    amount_all_tasks = amount_completed + amount_uncompleted
    line_break = '\n'
    report = (f"Отчёт для {user['company']['name']}.\n"
              f"{user['name']} <{user['email']}> {dt.now().strftime('%d.%m.%Y %H:%M')}\n"
              f"Всего задач: {amount_all_tasks} \n\n"
              f"Завершённые задачи ({amount_completed}):\n"
              f"{line_break.join(completed)}\n\n"
              f"Оставшиеся задачи ({amount_uncompleted}):\n"
              f"{line_break.join(uncompleted)}\n"
              )
    return report


def get_creation_time(user):
    try:
        with open(f"{PATH_TO_DIR}/{user['username']}.txt", encoding='utf-8') as file:
            creation_time = file.readlines()[1].strip('\n').split()[-2:]
        return ' '.join(creation_time)
    except (OSError, IOError):
        return


def rename_old_file(user, creation_time, file_name):
    # creation_time = dt.strptime(creation_time, '%d.%m.%Y %H:%M').strftime('%Y-%m-%dT%H&%M')   # Дата c "&" вместо ":" для тестирования на Windows
    creation_time = dt.strptime(creation_time, '%d.%m.%Y %H:%M').isoformat()[:-3]
    try:
        os.rename(f"{PATH_TO_DIR}/{file_name}",
                  f"{PATH_TO_DIR}/old_{user['username']}_{creation_time}.txt"
                  )
    except OSError:
        raise OSError('Can`t rename file')


def save_report_as_file(user, report, creation_time):
    file_name = f"{user['username']}.txt"

    if file_name in os.listdir(f'{PATH_TO_DIR}'):
        with open(f'{PATH_TO_DIR}/{file_name}.new', 'w', encoding='utf-8') as file:
            file.write(report)
        rename_old_file(user, creation_time, file_name)
        os.rename(f"{PATH_TO_DIR}/{file_name}.new",
                  f"{PATH_TO_DIR}/{file_name}"
                  )
    else:
        with open(f'{OUT_DIR}/{file_name}', 'w', encoding='utf-8') as file:
            file.write(report)


def get_reports_for_users_as_files(users, tasks):
    for user in users:
        if check_user_bound_keys(user):
            report = get_report_for_user(user, get_tasks_of_users(tasks))
            creation_time = get_creation_time(user)
            save_report_as_file(user, report, creation_time)


def main():
    users = get_data_from_api(USERS_URL)
    tasks = get_data_from_api(TASKS_URL)
    try:
        os.makedirs(PATH_TO_DIR, exist_ok=True)
    except OSError:
        raise OSError(f"Can`t make out directory '{OUT_DIR}'")
    get_reports_for_users_as_files(users, tasks)


if __name__ == '__main__':
    main()