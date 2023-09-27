from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks

from datetime import date, datetime, timedelta
from dateutil.parser import parse as date_parse

from googleapiclient.discovery import build

import os
import json

from twilio.rest import Client
import phonenumbers

load_dotenv()

allEvents: list[dict[str, str]] = [];
subOrgEvents: dict = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};

GOOGLE_CALENDAR_API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_VERIFY_SID = os.environ['TWILIO_VERIFY_SID']
DISCORD_AASU_BOT_TOKEN="MTE1MjQ0NzU0ODg3NTg3ODUzMA.GPfaPj.Zxe5da6XhgKkLxpiUtVcG8anh2RBow61xri_XE"


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = client.verify.v2.services(TWILIO_VERIFY_SID)
verifying_user: discord.User = None
verifying_number = ''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Activity(type=3, name="!help"), status=discord.Status.online)
bot.remove_command('help')

@tasks.loop(hours=24.0)
async def get_events():
    global allEvents
    global subOrgEvents

    newEvents = [];
    newSubOrgEvents = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};
    
    service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)

    today = datetime.utcnow()
    print(today)
    today.replace(hour=0, minute=0, second=0, microsecond=0)
    inOneMonth = today + timedelta(days=30)

    timeMin = today.isoformat() + 'Z'
    timeMax = inOneMonth.isoformat() + 'Z'
    
    events_result = service.events().list(calendarId='aasu.uf@gmail.com', timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        name = event['summary']
        start = event['start'].get('date')
        end = (date_parse(event['end'].get('date'))-timedelta(days=1)).strftime('%Y-%m-%d')
        newEvent = {'name': name, 'start': start, 'end': end}

        newEvents.append(newEvent)
        for org in newSubOrgEvents:
            if org in name:
                newSubOrgEvents[org].append(newEvent)

    allEvents = newEvents
    subOrgEvents = newSubOrgEvents

async def get_daily_sms():
    msg = "No events today!";
    tomorrow = date.today()+timedelta(days=1)
    eventList = [event for event in allEvents if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=tomorrow)]
    if len(eventList) > 0:
        msg = "IMMEDIATE EVENTS\n"
        for event in eventList:
            msg = msg+'\n'+event['start'][5:]
            if event['end']!=event['start']:
                msg = msg + " ➾ " + event['end'][5:]
            msg = msg + ": " + event['name']
    return msg


@tasks.loop(hours=24.0)
async def send_daily_sms():

    msg = await get_daily_sms()
    try:
        with open('numbers.json', 'r') as file:
            data = json.load(file)
            for number in data:
                client.messages \
                    .create(
                        body=msg,
                        from_ =  "8336331775",
                        to = number
                    )
    except:
        print("No SMS subscriptions :(")

async def get_daily_discord():
    msg = "No events today!";
    tomorrow = date.today()+timedelta(days=1)
    eventList = [event for event in allEvents if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=tomorrow)]
    if len(eventList) > 0:
        msg = "__**IMMEDIATE EVENTS**__\n"
        for event in eventList:
            msg = msg+'\n*'+event['start']
            if event['end']!=event['start']:
                msg = msg + " **-** " + event['end']
            msg = msg + f"* **{event['name']}**"
    return msg

@tasks.loop(hours=24.0)
async def send_daily_discord():
    msg = await get_daily_discord()
    try:
        with open('discord_users.json', 'r+') as file:
            data = json.load(file)
            for username in data['usernames']:
                user = discord.utils.get(bot.users, name=username)
                if user:
                    await user.send(msg)
                else:
                    print("User not found: " + username)
    except:
        print("No subscriptions :(")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}") 
    get_events.start()
    send_daily_sms.start()
    send_daily_discord.start()


@bot.command()
async def events(ctx, *args):
    eventList: list = [];
    heading = "EVENTS"

    args = list(args)
    for i in range(len(args)):
        args[i] = args[i].upper()
    print(args)

    for org in set(args) & set(subOrgEvents):
        eventList = eventList + subOrgEvents[org]
        heading = org+" "+heading

    eventList.sort(key=lambda x: x['start'])

    if len(eventList) == 0:
        eventList = allEvents
        heading = "ALL AASU EVENTS"


    timeframes = {"TODAY": date.today(), "TOMORROW": date.today()+timedelta(1), "WEEK": date.today()+timedelta(7)}
    numTimeFrames = 0;
    for timeframe in timeframes: 
        if timeframe in args:
            numTimeFrames+=1
            if numTimeFrames > 1:
                await ctx.send("Please only enter one timeframe!")
                break
            eventList = [event for event in eventList if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=timeframes[timeframe])]
            human_str = timeframe
            human_str = human_str.replace("WEEK", "THIS WEEK")
            if len(eventList) == 0:
                await ctx.send(f"No events {human_str.lower()}!")
            else:
                heading = heading + " " + human_str
        
    if len(eventList) > 0 and numTimeFrames<=1:
        msg = f"__**{heading}**__\n"
          
        for event in eventList:
            msg = msg+'\n*'+event['start']
            if event['end']!=event['start']:
                msg = msg + " **-** " + event['end']
            msg = msg + f"* **{event['name']}**"
        await ctx.send(msg)

@bot.command()
async def calendar(ctx):
    await ctx.send("[**UF AASU Calendar**](http://www.ufaasu.com/calendar/)")

@bot.command()
async def help(ctx):
    await ctx.send(
'''
**COMMANDS:**

- `!events [suborg] [timeframe]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - *Suborgs: AASU, CASA, HEAL, KUSA, FSA, FLP, VSO*
  - *Timeframes: today, tomorrow, week*

- `!calendar`: Get the link to AASU's calendar.

- `!subscribe [YOUR PHONE NUMBER]`: Subscribe to Discord or SMS reminders.
  - *Phone Number Format:* `+13525550000` *(MUST INCLUDE COUNTRY CODE, +1 FOR USA)*

- `!unsubscribe ['sms']`: Unsubscribe from Discord or SMS reminders.
''')
    
@bot.command()
async def verify(ctx, arg=''):
    global verifying_number
    global verifying_user
    user = ctx.author

    if verifying_number != '' and ctx.author==verifying_user:
        if arg.isnumeric() and len(arg) == 6:
            result = verify_service.verification_checks.create(to=verifying_number, code=arg)
            if result.status == 'approved':
                try:
                    with open("numbers.json", "r+") as file:
                        data = json.load(file)
                        if verifying_number not in data:
                            data[verifying_number] = user.name
                            
                except:
                    data = {verifying_number: user.name}
                
                await ctx.send("You are now subscribed via SMS!")
                with open("numbers.json", "w") as file:
                    json.dump(data, file, indent=4)
                
                
                verifying_number = ''
                verifying_user = None
        else:
            await ctx.send("Error: invalid code. Please try again.")




@bot.command()
async def subscribe(ctx, arg=''):
    global verifying_number
    global verifying_user

    user = ctx.author
    if len(arg) == 0:
        try:
            with open("discord_users.json", "r+") as file:
                data = json.load(file)
                if user.name not in data['usernames']:
                    data['usernames'].append(user.name)
                else:
                    await ctx.send("Error: you are already subscribed!")
                    return
        except:
            data = {'usernames': [user.name]}

        await ctx.send("You are now subscribed!")
        with open("discord_users.json", "w") as file:       
            json.dump(data, file, indent=4)

    else:
        try:    
            parsed_phone_number = phonenumbers.parse(arg)
            is_possible_phone_number = phonenumbers.is_possible_number(parsed_phone_number)
        except:
            is_possible_phone_number = False

        if is_possible_phone_number:
            if client.lookups.v2.phone_numbers(arg).fetch().valid:
                try:
                    with open("numbers.json", "r+") as file:
                        data = json.load(file)
                        if arg in data:
                            await ctx.send("Error: you are already subscribed via SMS.")
                except:
                    pass

                await ctx.send("Please enter the verification code sent to your phone number *(e.g. **!verify 123456**)*.")
                verify_service.verifications.create(
                    to=arg, channel='sms'
                )
                verifying_number = arg
                verifying_user = user
            else:
                ctx.send("Error: this phone number does not exist!")
        elif arg.isnumeric():
            if len(arg) == 10:
                await ctx.send("Error: invalid format. Remember to add the country code *(+1 for US)*.")
            else:
                await ctx.send("Error: invalid number.")
        else:
            await ctx.send("Error: invalid input.")



@bot.command()
async def unsubscribe(ctx, arg=''):
    user = ctx.author
    if len(arg) == 0:
        was_subscribed = False
        try:
            with open("discord_users.json", "r") as file:
                data = json.load(file)
                if user.name in data['usernames']:
                    data['usernames'].remove(user.name)
                    was_subscribed = True
                    await ctx.send("You are now unsubscribed.")
                    
            with open("discord_users.json", "w") as file:
                json.dump(data, file, indent=4)               
        except:
            pass
        if was_subscribed == False:
            await ctx.send("Error: you are already unsubscribed!")

    else:
        if arg == "sms":
            was_subscribed = False
            try:
                with open("numbers.json", "r") as file:
                    data = json.load(file)
                    for number in data:
                        if data[number] == user.name:
                            del data[number]
                            was_subscribed = True
                            break
                if was_subscribed:
                    with open("numbers.json", "w") as file:
                        json.dump(data, file, indent=4)
                    await ctx.send("You are now unsubscribed from SMS reminders.")
            except:
                pass
            if was_subscribed == False:
                await ctx.send("Error: you are already unsubscribed from SMS reminders.")
        else:
            await ctx.send("Error: please enter either **!unsubscribe** to unsubscribe from Discord reminders or **!unsubscribe sms** to unsubscribe from SMS reminders.")

bot.run(DISCORD_AASU_BOT_TOKEN)