import re
import pytz
import logging

from opsdroid.matchers import match_regex
from opsdroid.matchers import match_crontab
from opsdroid.message import Message

from datetime import datetime, timedelta, timezone


@match_regex(r'^Напомни в [0-9][0-9]:[0-9][0-9] .*')
async def remember_something(opsdroid, config, message):
    store = await opsdroid.memory.get("reminders")
    if store is None:
        future_reminders = []
    else:
        future_reminders = store['reminders']

    notification_text = re.sub('Напомни в [0-9][0-9]:[0-9][0-9] ', '', message.text)

    now = datetime.now(pytz.timezone('Europe/Moscow'))
    re_time = re.findall('[0-9][0-9]', message.text)
    hh_moscow = re_time[0]
    mm_moscow = re_time[1]
    if (now.hour > int(hh_moscow)) or (now.hour == int(hh_moscow) and (now.minute > int(mm_moscow))):
        await message.respond("Пока могу напоминать только в течение дня(")
    else:
        hh_mm_ss_moscow = f'{hh_moscow}:{mm_moscow}:00'
        today = datetime.today()
        future_timestamp = datetime.combine(today, datetime.strptime(hh_mm_ss_moscow, '%H:%M:%S').time())

        f_ts = (future_timestamp + timedelta(hours=-3)).timestamp()

        connector = message.connector.name

        future_reminders.append({
            'timestamp': f_ts,
            'message': f'Вы поставили напоминание сегодня в {now.hour}:{now.minute}. Напоминаю: {notification_text}',
            'user': message.user,
            'room': message.target,
            'connector': connector,
        })
        await opsdroid.memory.put('reminders', {
            'reminders': future_reminders,
            'last_updated': now.timestamp(),
        })
        await message.respond("ОК!")


@match_crontab('* * * * *')
async def send_reminders(opsdroid, config, message):
    now = datetime.now(timezone.utc)
    store = await opsdroid.memory.get("reminders")
    remaining_reminders = []
    if store is not None:
        for task in store['reminders']:
            try:
                reminder_timestamp = datetime.fromtimestamp(float(task['timestamp']), timezone.utc)
            except TypeError as e:
                logging.warning("Failed to convert timestamp: {}".format(task['timestamp']))
                continue
            if reminder_timestamp < now:
                try:
                    user = task['user']
                    room = task['room']
                    connector_name = task['connector']
                except KeyError as e:
                    logging.warning("Didn't find attributes expected in reminders memory: {}".format(e))
                    continue

                # Work out which connector to use
                connectors = [c for c in opsdroid.connectors if c.name == connector_name]
                if len(connectors) != 1:
                    logging.warning("Had trouble finding connector {}".format(connector_name))
                    continue

                connector = connectors[0]
                message = Message("", task['user'], task['room'], connector)
                await message.respond(task['message'])
            else:
                remaining_reminders.append(task)

        await opsdroid.memory.put('reminders', {
            'reminders': remaining_reminders,
            'last_updated': now.timestamp(),
        })
