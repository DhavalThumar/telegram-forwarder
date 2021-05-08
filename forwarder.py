''' A script to send all messages from one chat to another. '''

import asyncio
import logging

from telethon.tl.patched import MessageService
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import search_lst, exclude_lst
from settings import API_ID, API_HASH, REPLACEMENTS, forwards, get_forward, update_offset, STRING_SESSION
from datetime import datetime, timedelta
import pytz

utc = pytz.UTC

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

SENT_VIA = f'\n__Sent via__ `{str(__file__)}`'


def intify(string):
    try:
        return int(string)
    except:
        return string


def replace(message):
    for old, new in REPLACEMENTS.items():
        message.text = str(message.text).replace(old, new)
    return message


async def forward_job():
    ''' the function that does the job 😂 '''
    if STRING_SESSION:
        session = StringSession(STRING_SESSION)
    else:
        session = 'forwarder'

    async with TelegramClient(session, API_ID, API_HASH, auto_reconnect=True, connection_retries=None,
                              request_retries=None) as client:
        error_occured = False
        while True:
            for forward in forwards:
                from_chat, to_chat, offset = get_forward(forward)

                if not offset:
                    offset = 0

                last_id = 0
                previous_date = datetime.now() - timedelta(days=0)
                previous_date = datetime.strptime(previous_date.strftime('%d/%m/%y 00:00:00'), '%d/%m/%y 00:00:00')
                async for message in client.iter_messages(intify(from_chat), reverse=True, offset_id=offset):
                    if isinstance(message, MessageService):
                        continue
                    try:
                        # if datetime.strptime(message.date.strftime('%d/%m/%y 00:00:00'),'%d/%m/%y 00:00:00') > previous_date:
                        text = message.text.lower()

                        if any(word in text for word in search_lst) and (exclude_lst[0] not in text):
                            await client.send_message(intify(to_chat), replace(message))
                            logging.info('forwarding message with id = %s', str(message.id))
                        last_id = str(message.id)
                        update_offset(forward, last_id)
                    except FloodWaitError as fwe:
                        print(f'{fwe}')
                        await asyncio.sleep(delay=fwe.seconds)
                    except Exception as err:
                        logging.exception(err)
                        error_occured = True
                        break

                    # logging.info('Completed working with %s', forward)


if __name__ == "__main__":
    assert forwards
    asyncio.run(forward_job())
