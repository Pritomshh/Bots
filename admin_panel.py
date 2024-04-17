import json
from datetime import datetime
import telethon
from telethon import events, Button
from read_variables import *
from TempClient import TempClient
from Bot import Bot
from telethon.sync import TelegramClient
from dotenv import set_key
from pathlib import Path
from telethon.events import newmessage
import os, zipfile

bot_object = Bot()
bot = bot_object.bot
current_users = {}
def write_json_file(filename: str, content: dict) -> None:
    # Serializing json
    json_object = json.dumps(content, indent=4)

    # Writing to sample.json
    with open(f"{filename}.json", "w") as outfile:
        outfile.write(json_object)

def read_json_file(filename: str) -> dict:
    # Opening JSON file
    f = open(f'{filename}.json')

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    return data

def read_users() -> list[str]:
    with open('users.txt', 'r') as file:
        users = file.read().split('\n')
        return users


try:
    country_status = read_json_file('country_status')
except FileNotFoundError:
    country_status = {}

try:
    country_time = read_json_file('country_time')
except FileNotFoundError:
    country_time = {}




async def handle_admin_panel(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    user_id = user.id

    if not is_admin(user_id):
        await event.reply('You cannot access this options.')
        return
    

    current_users[user_id] = {}
    current_users[user_id]['stage'] = ''

    markup = event.client.build_reply_markup([
        [Button.text('Welcome'), Button.text('Admin')],
        [Button.text('Block | Unblock'), Button.text('Accounts')],
        [Button.text('Country - status'), Button.text('Show Country Status')],
        [Button.text('Broadcast'), Button.text('Send Message')],
        [Button.text('Acc Zip'), Button.text('Delete Acc From Bot')],
        [Button.text('Join Channel'), Button.text('Session Channel')],
        [Button.text('Remove User Info'), Button.text('Set Time')],

    ])

    message = 'Welcome back choose an option:'

    await event.respond(message, buttons=markup)


def is_admin(id: str) -> bool:

    admins = read_admins()

    return str(id) in admins
    

def read_admins() -> list[str]:
    with open('admins.txt', 'r') as file:

        admins = file.read().split('\n')

        return admins


@bot.on(events.NewMessage(pattern='Welcome', from_users=list(map(lambda id: int(id), read_admins()))))
async def welcome_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'welcome'

    await event.reply('Send your new welcome message: ')

@bot.on(events.NewMessage(pattern='Admin', from_users=list(map(lambda id: int(id), read_admins()))))
async def admin_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'admin'

    await event.reply('Send new admin user id: ')


@bot.on(events.NewMessage(pattern='Block | Unblock', from_users=list(map(lambda id: int(id), read_admins()))))
async def bock_or_unblock_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'block_or_unblock'

    await event.reply('Send user id to block or unblock: ')


@bot.on(events.NewMessage(pattern='Accounts', from_users=list(map(lambda id: int(id), read_admins()))))
async def account_handler(event: newmessage.NewMessage.Event) -> None:

    accounts = get_accounts()

    accounts_numbers = get_account_numbers(accounts)

    message = '\n'.join(accounts_numbers)

    await event.reply(message)

# get all available accounts
def get_accounts() -> list[str]:

    accounts = os.listdir('accounts')

    return accounts

# send all accounts number to the user
def get_account_numbers(accounts: list[str]) -> list[str]:

    accounts_numbers = []

    for i in range(0, len(accounts), 2):
        account = accounts[i]
        accounts_numbers.append(account.split('.')[0])
    
    return accounts_numbers


@bot.on(events.NewMessage(pattern='Country - status', from_users=list(map(lambda id: int(id), read_admins()))))
async def country_status_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'country_code'

    await event.reply('Send the country code: ')


@bot.on(events.NewMessage(pattern='Broadcast', from_users=list(map(lambda id: int(id), read_admins()))))
async def broadcast_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'broadcast'

    await event.reply('Forward your message here: ')


@bot.on(events.NewMessage(pattern='Send Message', from_users=list(map(lambda id: int(id), read_admins()))))
async def broadcast_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'send_message'

    await event.reply('Send your message here: ')


@bot.on(events.NewMessage(pattern='Acc Zip', from_users=list(map(lambda id: int(id), read_admins()))))
async def zip_accounts_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users
    
    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'zip_accounts'

    await event.reply('How many accounts do you want: ')


@bot.on(events.NewMessage(pattern='Delete Acc From Bot', from_users=list(map(lambda id: int(id), read_admins()))))
async def delete_accounts_handler(event: newmessage.NewMessage.Event) -> None:
    
    delete_all_accounts()

    await event.reply('All accounts has been deleted.')

def delete_all_accounts() -> None:

    for file in os.listdir('accounts'):

        os.remove(f'accounts/{file}')



@bot.on(events.NewMessage(pattern='Show Country Status', from_users=list(map(lambda id: int(id), read_admins()))))
async def show_country_status_handler(event: newmessage.NewMessage.Event) -> None:

    country_status = read_json_file('country_status')
    
    message = ''

    for code, capacity in country_status.items():
        message += f'{code}: {capacity}\n'

    await event.reply(message) 

@bot.on(events.NewMessage(pattern='Join Channel', from_users=list(map(lambda id: int(id), read_admins()))))
async def join_channel_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users

    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'public_channel_link'

    await event.reply('Send channel public link(e.g @test): ')

@bot.on(events.NewMessage(pattern='Set Time', from_users=list(map(lambda id: int(id), read_admins()))))
async def set_time_handler(event: newmessage.NewMessage.Event) -> None:
    global current_users

    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'set_time'

    await event.reply('Send country code which you have added before: ')


@bot.on(events.NewMessage(pattern='Remove User Info', from_users=list(map(lambda id: int(id), read_admins()))))
async def remove_users_information_handler(event: newmessage.NewMessage.Event) -> None:
    try:
        os.remove('users_info.json')
        await event.reply('All users information has been deleted.')
    except FileNotFoundError:
        pass


@bot.on(events.NewMessage(pattern='Session Channel', from_users=list(map(lambda id: int(id), read_admins()))))
async def join_channel_handler(event: newmessage.NewMessage.Event) -> None:

    global current_users

    user = await event.get_chat()

    current_users[user.id] = {}
    current_users[user.id]['stage'] = 'private_channel_id'

    await event.reply('Send channel private id(e.g -10013123123): ')

@bot.on(events.NewMessage)
async def handle_message(event: newmessage.NewMessage.Event) -> None:

    global current_users, country_status, country_time

    user = await event.get_chat()

    try:

        current_user = current_users[user.id]

    except KeyError:

        current_users[user.id] = {}
        current_users[user.id]['stage'] = ''
        current_user = current_users[user.id]


    stage = current_user.get('stage', '')

    # Get the message text
    message = event.message.text
    print(message)

    if stage == 'welcome' and message != 'Welcome':

        await write_env('welcome_message', message)
        
        await event.reply('It\'s has changed successfully.')

        current_users[user.id]['stage'] = ''
    
    elif stage == 'admin' and message.isnumeric():

        await add_new_admin(message)

        await event.reply('New admin was set')

        current_users[user.id]['stage'] = ''
    
    elif stage == 'block_or_unblock' and message.isnumeric():

        blocked_users = read_blocks_file()

        if message in read_blocks_file():

            # unblock the user
            blocked_users.remove(message)
            write_blocks(blocked_users, 'w')
            await event.reply(f'{message} was unblocked')

        else:

            # block the user
            write_blocks([message], 'a')
            await event.reply(f'{message} was blocked')
        
        current_users[user.id]['stage'] = ''

    elif stage == 'country_code' and is_country_code(message):

        if not message in country_status.keys():
        
            country_status[message] = ''

            await event.reply('Enter capacity: ')

            current_users[user.id]['stage'] = 'capacity'
        
        else:

            await event.reply('This country code is off now.')
            
            current_users[user.id]['stage'] = ''

            remove_country_code(message)

    elif stage == 'capacity' and message.isnumeric():

        add_new_country_code(message)

        await event.reply('Country code with its capacity is on now.')

        current_users[user.id]['stage'] = ''
    
    elif stage == 'broadcast' and message != 'Broadcast':

        await send_message_all(event, message)

        current_users[user.id]['stage'] = ''
    
    elif stage == 'send_message' and message != 'Send Message':

        await send_message_all(event, message)

        current_users[user.id]['stage'] = ''

    elif stage == 'zip_accounts' and message.isnumeric():

        current_users[user.id]['stage'] = ''

        zip_accounts(int(message))

        await bot.send_file(user.id, f'accounts.zip')

        os.remove('accounts.zip')

    elif stage == 'public_channel_link' and message[0] == '@':

        public_link = message[1:]

        await toggle_public_channel_link(public_link, event)

        current_users[user.id]['stage'] = ''

    elif stage == 'private_channel_id' and message[1:].isnumeric() and message[0] == '-':

        await toggle_private_channel_id(message, event)

        current_users[user.id]['stage'] = ''

    elif stage == 'set_time' and is_country_code(message):

        if is_country_code_exist(message):
            country_time[message] = ''
            current_users[user.id]['stage'] = 'set_minutes'
            await event.reply('Perfect, now send me the time in minutes: ')
        
        else:
            current_users[user.id]['stage'] = ''
            await event.reply('First, you need to add this country code.')

    elif stage == 'set_minutes' and message.isnumeric():

        add_new_time(message)

        await event.reply('The time was set successfully.')

        current_users[user.id]['stage'] = ''

def is_country_code_exist(country_code: str) -> bool:

    country_status = read_json_file('country_status')

    return country_code in country_status.keys()

async def toggle_private_channel_id(private_id: str, event: newmessage.NewMessage.Event) -> None:

    all_private_ids = read_private_channel_ids()

    if private_id in all_private_ids:
        
        all_private_ids.remove(private_id)
        await event.reply('The private id has been deleted.')
        write_private_channel_ids(all_private_ids)
    
    else:

        all_private_ids.append(private_id)
        await event.reply('The private id has been added.')
        write_private_channel_ids(all_private_ids)


def read_private_channel_ids() -> list[str]:

    try:
        with open('private_channel_ids.txt', 'r') as file:
            return file.read().split('\n')
        
    except FileNotFoundError:
        return []

def write_private_channel_ids(private_ids: list[str]) -> None:

    with open('private_channel_ids.txt', 'w') as file:

        file.write('\n'.join(private_ids))

async def toggle_public_channel_link(public_link: str, event: newmessage.NewMessage.Event) -> None:
        
        all_public_links = read_public_channel_links()
        
        if public_link in all_public_links:

            all_public_links.remove(public_link)

            await event.reply('The public link has been deleted.')
        
        else:

            all_public_links.append(public_link)

            await event.reply('The public link has been added.')

        
        write_public_channel_links(all_public_links)

def read_public_channel_links() -> list[str]:
    try:
        with open('public_channel_links.txt', 'r') as file:
            return file.read().split('\n')
    except FileNotFoundError:
        return []
    
def write_public_channel_links(links: list[str]) -> None:

    with open('public_channel_links.txt', 'w') as file:

        file.write('\n'.join(links))

def zip_accounts(number_of_accounts: int) -> None:

    base_path = os.getcwd()
    # create a file with zip format
    zip = zipfile.ZipFile("accounts.zip", "w", zipfile.ZIP_DEFLATED)

    counter = 0

    os.chdir('accounts')

    files = os.listdir()

    # add account files to zip file with number limit 
    for i in range(0, len(files), 2):
        
        json_file = files[i]
        sessions_file = files[i+1]

        zip.write(json_file)
        zip.write(sessions_file)

        counter += 1

        if counter == number_of_accounts:
            break
    
    zip.close()

    os.chdir(base_path)

async def send_message_all(event: newmessage.NewMessage.Event, message: str) -> None:
        users = get_users()
        if users:
            for user in users:
                try:
                    await event.client.send_message(int(user), message)
                except:
                    pass
        else:
            await event.reply('No users found')
    
def get_users() -> set[str]:

    try:
        users = set(read_users())
    
    except FileNotFoundError:
        users = set()

    return users

def is_country_code(text: str) -> bool:

    return text[0] == '+' and text[1:].isnumeric()

def add_new_country_code(capacity: str) -> None:
        
    global country_status

    last_added_country_code = list(country_status.keys())[-1]

    country_status[last_added_country_code] = capacity

    write_json_file('country_status', country_status)

def remove_country_code(country_code: str) -> None:
    
    global country_status

    country_status.pop(country_code)

    write_json_file('country_status', country_status)

def add_new_time(time: str) -> None:

    global country_time

    last_added_country_code = list(country_time.keys())[-1]

    country_time[last_added_country_code] = time

    write_json_file('country_time', country_time)


async def write_env(key: str, value: str) -> None:

    from read_variables import load_env

    load_env()

    os.environ[key] = value

    # load .env 
    env_file_path = Path(".env")

    # Save some values to the file.
    set_key(dotenv_path=env_file_path, key_to_set=key, value_to_set=value)

async def add_new_admin(user_id: str) -> None:

    user_id = str(user_id)

    await write_admins_file(user_id)

async def write_admins_file(id: str) -> None:

    with open('admins.txt', 'a') as file:

        file.write('\n' + id)

def read_blocks_file() -> list[str]:

    with open('blocks.txt', 'r') as file:

        blocked_users = file.read().split('\n')

        return blocked_users

def write_blocks(blocked_users: list[str], write_type: str) -> None:

    with open('blocks.txt', write_type) as file:

        file.write('\n'.join(blocked_users))

