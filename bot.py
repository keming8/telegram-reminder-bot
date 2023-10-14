import telebot, datetime, time, schedule, dateutil.parser, threading
from datetime import datetime, timedelta
from flask import Flask,request


"""
TODO:
- List active reminders (DONE)
- Cancel reminders? (CANCEL ALL DONE, CANCEL LAST DEFINED DONE - maybe use a queue?)
- Deal with inaccurate input (DONE?)
- Use natural language
- Schedule reminders for fixed intervals (/remindmeevery) (DONE for days and times (s, m, h etc), not enough support for longer gaps)
- Add limit to recurring reminders (DONE)
- Add to Google Calendar
- On top of calendar, add as tasks
- Change data structure for storing messages?
- Change timezones (DONE)
"""

API_TOKEN = ""



all_reminders_dict = dict() # Dict of chat IDs to dict of message : reminder time

jobs = dict() # Dict of jobs for cancelling

timezones = dict() # Dict of user timezones

bot = telebot.TeleBot(API_TOKEN)
bot.set_webhook()
"""bot.remove_webhook()
bot.set_webhook(url="")"""



def send_reminder(chat_id, msg):
	# remove it from the dict
	all_reminders_dict[chat_id].pop(msg)
	bot.send_message(chat_id, text = msg)

	# make it a one-time job
	return schedule.CancelJob  

def day_to_number(day):
	if (day in ['mon', 'Mon', 'MON', 'monday', 'Monday', 'MONDAY']):
		return 0
	elif (day in ['tue', 'Tue', 'TUE', 'Tuesday', 'tuesday', 'TUESDAY']):
		return 1
	elif (day in ['wed', 'Wed', 'WED', 'Wednesday', 'wednesday', 'WEDNESDAY']):
		return 2
	elif (day in ['thu', 'Thu', 'THU', 'Thursday', 'thursday', 'THURSDAY']):
		return 3
	elif (day in ['fri', 'Fri', 'FRI', 'Friday', 'friday', 'FRIDAY']):
		return 4
	elif (day in ['sat', 'Sat', 'SAT', 'Saturday', 'saturday', 'SATURDAY']):
		return 5
	elif (day in ['sun', 'Sun', 'SUN', 'Sunday', 'sunday', 'SUNDAY']):
		return 6
	else:
		return -1

def send_confirmation(original_message, message, date):
	bot.reply_to(original_message, "Okay! \nReminder: "+ message + " \nis scheduled for: " + date)

def send_reminder_every(chat_id, msg):
	
	bot.send_message(chat_id, text = msg)

	return

@bot.message_handler(commands=['start'])
def start_message(message):
	bot.reply_to(message, "Hello! Use /remindme <time> or /remindmeevery <time> to set a reminder! You will then be prompted to enter your reminder message. Use /help for more information about the different reminder options!")

@bot.message_handler(commands=['help'])
def help_message(message):
	bot.reply_to(message, 
	      "/remindme <time>: set a fixed reminder \n\n" +
	      "Examples: /remindme in 5s , /remindme at 10pm, /remindme on 1 Jan \n\n\n" + 
	      "/remindmeevery <time>: set a recurring reminder \n\n" +
	      "Examples: /remindmeevery 5s, /remindmeevery Monday, /remindmeevery 5min \n\n\n" +
	      "/cancel : cancels the last-defined reminder \n\n\n" +
	      "/clear : cancels all reminders \n\n\n" +
	      "/list : see all scheduled reminders \n\n\n" + 
	      "/set_timezone <+/- HH:MM> : set timezone with respect to UTC \n\n" + 
	      "Examples: /set_timezone +01:00, /set_timezone -08:00 \n\n\n" +
	      "/check_timezone : Check timezone that has been set \n\n\n" +
              "/help : List of all commands")
	  
@bot.message_handler(commands=['list'])
def list_reminders(message):
	chatid = message.chat.id
	if (chatid in all_reminders_dict):
		if (bool(all_reminders_dict[chatid])):
			#sort the dictionary
			sorted_reminders = dict(sorted(all_reminders_dict[chatid].items(), key = lambda x : x[1]))

			for k, v in sorted_reminders.items():
				bot.send_message(chatid, text = v + '\nMessage: '+ k)
			
		else:
			bot.reply_to(message, "There are no scheduled reminders currently set.")
	else:
		bot.reply_to(message, "There are no scheduled reminders currently set.")

@bot.message_handler(commands=['clear'])
def clear_all(message):
	chatid = message.chat.id

	# clear all jobs
	while(jobs[chatid] != []):
		schedule.cancel_job(jobs[chatid][len(jobs[chatid]) - 1])
		jobs[chatid].pop()
	
	# deleting the keys from the respective dictionaries
	if chatid in all_reminders_dict: 
		del all_reminders_dict[chatid]
	if chatid in jobs: 
		del jobs[chatid]
	#schedule.clear()
	bot.reply_to(message, "All scheduled reminders have been cleared. \n \n" + "Use /remindme or /remindmeevery to set a new reminder." )
	return

@bot.message_handler(commands=['cancel'])
def cancel(message):
	# Cancels the most recently defined job. Can be used multiple times. 
	chatid = message.chat.id
	if chatid in all_reminders_dict and chatid in jobs:
		if (bool(all_reminders_dict[chatid]) and bool(jobs[chatid])):
			schedule.cancel_job(jobs[chatid][len(jobs[chatid]) - 1])
			popped = all_reminders_dict[chatid].popitem()
			jobs[chatid].pop()
			#jobs[chatid].append(None
			bot.reply_to(message, "Okay!\nMessage: " + popped[0] + "\nScheduled for " + popped[1][0].lower() + popped[1][1:] + " \nhas been cancelled." )
		else:
			bot.reply_to(message, "All scheduled reminders have been cleared. \n \n" + "Use /remindme or /remindmeevery to set a new reminder.")
	else:
		bot.reply_to(message, "All scheduled reminders have been cleared. \n \n" + "Use /remindme or /remindmeevery to set a new reminder.")
	return

@bot.message_handler(commands=['set_timezone'])
def set_timezone(message):
	chatid = message.chat.id
	try:
		mess = message.text.split(" ")[1:]
		sign = mess[0]
		hours = mess[1][0:2]
		minutes = mess[1][3:5]
		if sign == '+':
            		offset = int(hours) * 3600 + int(minutes) * 60
		else:
            		offset = -(int(hours) * 3600 + int(minutes) * 60)
		timezones[chatid] = offset
		bot.reply_to(message, "Your timezone has been changed to UTC" + sign + str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ".")
	except:
		bot.reply_to(message, "Please enter your timezone offset with respect to UTC. \n \nFor example, for Singapore, use /set_timezone + 08:00 \n \nUsage: /set_timezone <+/- HH:MM>")
	return


@bot.message_handler(commands=['check_timezone'])
def check_timezone(message):
	chat_id = message.chat.id
	offset = timezones.get(chat_id, 0)
	hours = offset // 3600
	minutes = offset % 60
	if offset < 0:
            		sign = '-'
	else:
            		sign = '+'
	bot.reply_to(message, "Your current timezone set is UTC" + sign + str(hours).zfill(2) + ':'  + str(minutes).zfill(2) + ". You may use /set_timezone to change your timezone.")


@bot.message_handler(commands=['remindme'])
def remindme_message(message):
	try:
		start = message.text.split(" ")[1]
		check = len(message.text.split(" "))
		if (start in ['in', 'on', 'at']):
				if (start == 'in' and check > 4):
					bot.reply_to(message, "Please try again. \n \nUsage: /remindme in <time> ")
					return
				elif (start == 'at' and check > 3):
					bot.reply_to(message, "Please try again. \n \nUsage: /remindme at <time>")
					return
				remindertime = message.text.split(' ', 1)[1]
				msg = bot.reply_to(message, "Please enter the reminder message.")
				
				bot.register_next_step_handler(msg, remindertime_message, remindertime = remindertime)
		else:
			bot.reply_to(message, "Usage: /remindme at/in/on <time> ")
	except:
		bot.reply_to(message, "Usage: /remindme at/in/on <time> ")

	return
	
def remindertime_message(message, remindertime):
	
	
	remindermessage_to_send = message.text
	chatid = message.chat.id
	offset = timezones.get(chatid, 0)

	if not(chatid in all_reminders_dict):
		all_reminders_dict[chatid] = dict()
	if not(chatid in jobs):
		jobs[chatid] = []
	try:
		message_timestamp = message.date + offset
		start = (remindertime.split(" ")[0]).lower()
		mess = remindertime.split(" ")
		
			
		# (AT) for a specific time on same day / next day
		if (start == 'at'):
			try:
				ret_datetime = dateutil.parser.parse(mess[1].replace('.', ':'))
				
			except:
				bot.reply_to(message, "Invalid date, please try again.")
				bot.register_next_step_handler(message, remindertime_message, remindermessage_to_send)
				return
			
			ret_timestamp = time.mktime(ret_datetime.timetuple())
			#If time indicated < current time, set it to the next day
			if (message_timestamp > ret_timestamp):
				ret_datetime = datetime.fromtimestamp(ret_timestamp) + timedelta(days = 1)
				ret_timestamp = time.mktime(ret_datetime.timetuple())

			ret_datetime = datetime.fromtimestamp(ret_timestamp)

			jobs[chatid].append(schedule.every(ret_timestamp - message_timestamp).seconds.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))

			ret_datetime = ret_datetime.strftime("%d %B %Y, %H:%M:%S")
			send_confirmation(message, remindermessage_to_send, ret_datetime)
			all_reminders_dict[chatid][remindermessage_to_send] = ret_datetime
			#current_reminders[remindermessage_to_send] = ret_datetime
		
		
		# (ON) for specific day/date
		elif (start == 'on'):
			if ('at' in mess or 'AT' in mess or 'At' in mess):
				reminder_date = ' '.join(mess[1:len(mess) -2]) # extracting the date
				reminder_time = mess[-1]
			else:
				reminder_date = ' '.join(mess[1:])
				reminder_time = '12pm' #if time is not specified, set to noon
			
			ret_time = dateutil.parser.parse(reminder_time) 
			#If day specified is a day of the week and not specific date
			if (day_to_number(reminder_date) != -1):
				today_day_number = day_to_number(datetime.fromtimestamp(message_timestamp/1000).strftime('%A'))
				reminder_day_number = day_to_number(reminder_date)
				if (today_day_number - reminder_day_number == 0):
					reminder_day_number += 7
				
				ret_date = datetime.date(datetime.fromtimestamp(message_timestamp) + timedelta(days = abs(reminder_day_number) - today_day_number))
				
			else:
				try:
					ret_date = dateutil.parser.parse(reminder_date, dayfirst=True) 
				except:
					bot.reply_to(message, "Invalid date, please try again.")
					bot.register_next_step_handler(message, remindertime_message, remindermessage_to_send)
					return
				
			ret_datetime = datetime.combine(ret_date, ret_time.time())
			ret_timestamp = datetime.timestamp(ret_datetime)
				
			jobs[chatid].append(schedule.every(ret_timestamp - message_timestamp).seconds.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))	

			ret_datetime = ret_datetime.strftime("%d %B %Y, %H:%M:%S")
			send_confirmation(message, remindermessage_to_send, ret_datetime)
			all_reminders_dict[chatid][remindermessage_to_send] = ret_datetime

				
		# (IN) for a time delta from current time
		elif (start == 'in'):
			# If amount and quantifier not one word
			if (len(mess) == 3):
				amt = int(mess[1])
				quantifier = (mess[-1]).lower()
			elif (len(mess) == 2):
				quantifier = str(list(mess[-1])[-1]).lower()
				amt = int(mess[-1][:-1])

			if (quantifier in ['s', 'sec', 'secs', 'second', 'seconds']):
				ret_datetime = datetime.fromtimestamp(message_timestamp) + timedelta(seconds = amt)
				jobs[chatid].append(schedule.every(amt).seconds.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))
			elif (quantifier in ['m', 'min', 'mins', 'minute', 'minutes']):
				ret_datetime = datetime.fromtimestamp(message_timestamp) + timedelta(minutes = amt)
				jobs[chatid].append(schedule.every(amt).minutes.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))
			elif (quantifier in ['h', 'hr', 'hrs', 'hours', 'hour']):
				ret_datetime = datetime.fromtimestamp(message_timestamp) + timedelta(hours = amt)
				jobs[chatid].append(schedule.every(amt).hours.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))
			elif (quantifier in ['d', 'day', 'days']):
				ret_datetime = datetime.fromtimestamp(message_timestamp) + timedelta(days = amt)
				jobs[chatid].append(schedule.every(amt).days.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))
			elif (quantifier in ['w', 'week', 'weeks', 'wk', 'wks']):
				ret_datetime = datetime.fromtimestamp(message_timestamp) + timedelta(weeks = amt)
				jobs[chatid].append(schedule.every(amt).weeks.do(send_reminder, chat_id = chatid, msg = remindermessage_to_send))
			"""else:
				bot.register_next_step_handler(message, remindertime_message, remindermessage_to_send)
				bot.reply_to(message, "Please input either: <time>s, <time>m, <time>h, <time>d or <time>w.")
				return"""

			ret_datetime = ret_datetime.strftime("%d %B %Y, %H:%M:%S")
			send_confirmation(message, remindermessage_to_send, ret_datetime)
			all_reminders_dict[chatid][remindermessage_to_send] = ret_datetime

		"""else: #message does not start with 'at', 'in' or 'on'
			bot.reply_to(message, "Please input either: at <time>, on <time> or in <time>")
			bot.register_next_step_handler(message, remindertime_message, remindermessage_to_send)"""
	except:
		bot.reply_to(message, "Please try again.")
		bot.register_next_step_handler(message, remindertime_message, remindermessage_to_send)
		
	return

@bot.message_handler(commands=['remindmeevery'])
def remindme_message_every(message):

	chatid = message.chat.id
	offset = timezones.get(chatid, 0)
	message_timestamp = message.date + offset
	mess = message.text.split(" ")

	reminder_until = '6 months' #if until date is not specified, set to 6 months later
	reminder_time = '12pm' #if time is not specified, set to noon
	if (len(mess) > 1):
		# with 'until
		reminder_date = mess[1]
		#if ('until' in mess or 'Until' in mess or 'UNTIL' in mess):
		if ('until' in mess):
			reminder_until = ' '.join(mess[mess.index('until') + 1:])
		elif ('Until' in mess):
			reminder_until = ' '.join(mess[mess.index('Until') + 1:])
		elif ('UNTIL' in mess):
			reminder_until = ' '.join(mess[mess.index('UNTIL') + 1:])
			#reminder_until = mess[-1]
			# with 'until' and 'at'
			if ('at' in mess or 'AT' in mess or 'At' in mess):
				reminder_time = str(mess[3])
			
		# no 'until'
		elif ('at' in mess or 'AT' in mess or 'At' in mess):
				# If time uses decimal instead of colon
				reminder_time = mess[1].replace('.', ':')
		if (reminder_until == '6 months'):
			reminder_until = (datetime.date(datetime.fromtimestamp(message_timestamp)) + timedelta(weeks=26))
			reminder_until = datetime.combine(reminder_until, datetime.fromtimestamp(message_timestamp).time())
			reminder_until_str = reminder_until.strftime("%d %B %Y, %H:%M:%S")
		else:	
			reminder_until = dateutil.parser.parse(reminder_until, dayfirst=True)
		reminder_until_str = reminder_until.strftime("%d %B %Y, %H:%M:%S")
		#reminder_until = reminder_until.strftime("%d %B %Y, %H:%M:%S")
		if (day_to_number(reminder_date) != -1):
			msg = bot.reply_to(message, "What message would you like me to send every " + reminder_date.capitalize() + " at " + reminder_time + " until " + reminder_until_str + "?")
		else:
			msg = bot.reply_to(message, "What message would you like me to send every " + reminder_date.capitalize() + " until " + reminder_until_str + "?")
		bot.register_next_step_handler(msg, remindertime_message_every, reminder_date = reminder_date, reminder_time = reminder_time, reminder_until = reminder_until, reminder_until_str = reminder_until_str)
	else:
		bot.reply_to(message, "Usage: /remindmeevery <reminder message>")
	return
		
def remindertime_message_every(message, reminder_date, reminder_time, reminder_until, reminder_until_str):

	reminder_time = str((dateutil.parser.parse(reminder_time)).time())
	mess = message.text
	chatid = message.chat.id
	if not(chatid in all_reminders_dict):
		all_reminders_dict[chatid] = dict()
	# Dealing with specific day of the week
	if (day_to_number(reminder_date) != -1):
		day = day_to_number(reminder_date)
		if (day == 0):
			jobs[chatid].append(schedule.every().monday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id=chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Monday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Monday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 1):
			jobs[chatid].append(schedule.every().tuesday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id=chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Tuesdsay at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Tuesday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 2):
			jobs[chatid].append(schedule.every().wednesday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id=chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Wednesday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Wednesday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 3):
			jobs[chatid].append(schedule.every().thursday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Thursday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Thursday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 4):
			jobs[chatid].append(schedule.every().friday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Friday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Friday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 5):
			jobs[chatid].append(schedule.every().saturday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Saturday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Saturday at ' + reminder_time + ' until ' + reminder_until_str
		elif (day == 6):
			jobs[chatid].append(schedule.every().sunday.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every Sunday at ' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every Sunday at ' + reminder_time + ' until ' + reminder_until_str
	else:
		quantifier = str(list(reminder_date)[-1]).lower()
		amt = int(reminder_date[:-1])
		amt_str = str(amt)
		
	# Dealing with seconds, minutes, hours, days, weeks		
		if (quantifier == 's'):
			jobs[chatid].append(schedule.every(amt).seconds.until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every ' + amt_str + ' seconds' + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every ' + amt_str + ' seconds' + ' until ' + reminder_until_str
		elif (quantifier == 'm'):
			jobs[chatid].append(schedule.every(amt).minutes.until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every ' + amt_str + ' minutes' + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every ' + amt_str + ' minutes' + ' until ' + reminder_until_str
		elif (quantifier == 'h'):
			jobs[chatid].append(schedule.every(amt).hours.until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every ' + amt_str + ' hours' + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every ' + amt_str + ' hours' + ' until ' + reminder_until_str
		elif (quantifier == 'd'):
			jobs[chatid].append(schedule.every(amt).days.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every ' + amt_str + ' days at' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every ' + amt_str + ' days at '  + reminder_time + ' until ' + reminder_until_str
		elif (quantifier == 'w'):
			jobs[chatid].append(schedule.every(amt).weeks.at(reminder_time).until(reminder_until).do(send_reminder_every,chat_id = chatid, msg = mess))
			all_reminders_dict[chatid][mess] = 'Every ' + amt_str + ' weeks at' + reminder_time + ' until ' + reminder_until_str
			#current_reminders[mess] = 'Every ' + amt_str + ' weeks at ' + reminder_time + ' until ' + reminder_until_str
		else:
			bot.reply_to(message, "Invalid date, please try again.")
			bot.register_next_step_handler(message, remindertime_message_every, reminder_date = reminder_date, reminder_time = reminder_time, reminder_until = reminder_until, reminder_until_str = reminder_until_str)
			return
		
	send_confirmation(message, mess, 'Every ' + reminder_date + ' until ' + reminder_until_str)


	return


@bot.message_handler(content_types=['text'])
def misc_text(message):
	bot.reply_to(message, "Hello! Use /remindme <reminder message> to set a fixed reminder, or /remindmeevery to set a recurring reminder!")

if __name__ == '__main__':
	threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
	while True:
		schedule.run_pending()
		#time.sleep(1)

"""app = Flask(__name__)

@app.route('/', methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200"""
