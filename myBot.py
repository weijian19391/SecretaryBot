import telepot
from pprint import pprint
from pprint import pformat
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent
import datetime
from Calendar import GoogleCalendar
from State import State
import threading
import random
import Secret
import time
from Parsing import CommandParsing
from oauth2client.client import HttpAccessTokenRefreshError
from Database import UserDb
from googleapiclient.errors import HttpError
import json
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide
"""
Todo: add "what do i have on next thursday" and "when am i next free"
"""

class SecretaryBot(telepot.Bot): # this class is a child of the telepot.Bot class
	def __init__(self, *args, **kwargs):
		super(SecretaryBot, self).__init__(args[0], **kwargs) #here we call the parent class's __init__ method
		self._answerer = telepot.helper.Answerer(self)
		self._message_with_inline_keyboard = None
		self.prev_cmd = {}
		self.msg_to_replace = {}
		self.gCal = GoogleCalendar(args[1])
		self.parser = CommandParsing()
		self.userDb = UserDb()
		self.stateOfUser = {}

	def on_chat_message(self, msg):
		# pprint(msg)
		flavor = telepot.flavor(msg)
		print ('Chat message')
		content_type, chat_type, chat_id = telepot.glance(msg, flavor='chat')
		print (content_type, chat_type, chat_id)
		msg_arr = msg["text"].split(" ")
		command = msg_arr[0]
		print(msg["text"])

		if command == "/login":
			self.userDb.add_new_user(chat_id, msg["chat"]["first_name"], msg["chat"]["last_name"])
			auth_uri = self.gCal.get_auth_uri()
			self.sendMessage(chat_id, 'click link to sign in to google account:\n' + auth_uri)
		elif command =="/start":
			if len(msg_arr) > 1:
				code = msg_arr[1] + "=="
				self.gCal.add_credentials(chat_id, code)
				print str(msg["chat"]["first_name"]) + " login"
				self.sendMessage(chat_id, "Login successful!")
				self.bot_intro(chat_id)
			else:
				self.sendMessage(chat_id, "Welcome! To start using, type \"/login\" to authorise this bot to help you add events to your google calendar!")
		elif command == "/help":
			self.sendMessage(chat_id, self.send_help())
		elif command == "/upcomingevents":
			if len(msg_arr) == 1:
				markup = InlineKeyboardMarkup(inline_keyboard=[
						[dict(text='Nearest upcoming event', callback_data='nearest')],
						[dict(text='Events for tomorrow', callback_data='tomorrow')],
						[dict(text='Events for a week from now', callback_data='week')],
					 ])
				self._message_with_inline_keyboard = self.sendMessage(chat_id, "Choose type of upcoming events to show: ", reply_markup=markup)
		elif command == "/nextfreeday":
			self.sendMessage(chat_id, self.gCal.get_free_day(chat_id))
		elif command.lower() == "add":
			query_string = msg["text"]
			self.add_event(chat_id, query_string)
		elif command.lower() == "/add":
			self.stateOfUser[chat_id] = State()
			_ , questionToAsk = self.stateOfUser[chat_id].questionToAskNext()
			self.sendMessage(chat_id, questionToAsk)
		elif self.prev_cmd[chat_id] == "/add":
			userState = self.stateOfUser[chat_id]
			userState.populateAns(msg["text"])
			finishedAsking, questionToAsk = userState.questionToAskNext()
			if not finishedAsking:
				self.sendMessage(chat_id, questionToAsk)
			else:
				eventDetails = userState.eventToStringForUser()
				self.sendMessage(chat_id, eventDetails)
				self.add_event(chat_id, userState.eventToStringForGCal())
		if msg["text"][:1] == "/":
			self.prev_cmd[chat_id] = command
		else:
			if self.prev_cmd[chat_id] != "/add":
				self.prev_cmd[chat_id] = None

	def on_callback_query(self, msg):
		query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
		print('Callback query:', query_id, from_id, data)
		if data == "nearest" :
			try:
				events = self.gCal.get_upcoming_events(chat_id=from_id,  nearest=True)
			except HttpAccessTokenRefreshError, e:
				print "HttpAccessTokenRefreshError", e
				self.sendMessage(from_id, "Invalid Login! Enter \"/login\" to login to your Google account again")
		elif data == 'tomorrow':
			try:
				events = self.gCal.get_upcoming_events(chat_id=from_id, tomorrow=True)
			except HttpAccessTokenRefreshError, e:
				print "HttpAccessTokenRefreshError", e
				self.sendMessage(from_id, "Invalid Login! Enter \"/login\" to login to your Google account again")
		elif data == "week" :
			try:
				events = self.gCal.get_upcoming_events(chat_id=from_id, week=True)
			except HttpAccessTokenRefreshError, e:
				print "HttpAccessTokenRefreshError", e
				self.sendMessage(from_id, "Invalid Login! Enter \"/login\" to login to your Google account again")
		if from_id in self.prev_cmd and self.prev_cmd[from_id] == "/upcomingevents":
			if self._message_with_inline_keyboard and from_id in self.msg_to_replace:
				msgid = (from_id, self.msg_to_replace[from_id])
				try:
					self.editMessageText(msgid, events)
				except Exception, e:
					if e[0] == 'Bad Request: message is not modified':
						self.editMessageText(msgid, 'Still ' + events)
			else:
				self.sendMessage(from_id, events)
		else:
			self.sendMessage(from_id, events)
		self.answerCallbackQuery(query_id) #needed because without this, the loading icon will keep displaying.
		self.msg_to_replace[from_id] = self._message_with_inline_keyboard['message_id']+1

	def on_inline_query(self, msg):
		pprint(msg)
		def compute():
			query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
			print('%s: Computing for: %s' % (threading.current_thread().name, query_string))
			inline_response = self.parser.parse_command(query_string)
			# print "inline response is"
			pprint(inline_response)
			articles = [InlineQueryResultArticle(
							id='abcde', 
							title="Event to be added", 
							description=self.dict_to_text_inline_response(inline_response),
							input_message_content=InputTextMessageContent(
								message_text=('Adding the following event to my calendar via my secretary bot: \n' + 
												self.dict_to_text_chat_reponse(inline_response))))]
			if query_string[:3].lower() == "add":
				return articles
			else:
				return []

		self._answerer.answer(msg, compute)

	def on_chosen_inline_result(self, msg):
		result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
		print('Chosen Inline Result:', result_id, from_id, query_string)
		# print msg
		self.add_event(from_id, query_string)
		details = self.parser.parse_command(query_string)

	def dict_to_text_inline_response(self, dict):
		event_details = "Event: " + str(dict["event"])
		if dict["venue"] != "":
			event_details += " @ " + str(dict["venue"])
		if dict["date"] != "" or dict["from"] != "":
			event_details += "\nDate & Time: " + str(dict["date"]) + " "
			event_details += "from: " + str(dict["from"]) 
			if dict["to"] != "":
				event_details += " to " + str(dict["to"])
		# return ("Event: " + str(dict["event"]) + "@ " + str(dict["venue"]) + "\n" +
		# 		"Date & Time: " + str(dict["date"]) + ", " +
		# 		"From: " + str(dict["from"]) + " To: " + str(dict["to"]))
		return event_details

	def dict_to_text_chat_reponse(self, dict):
		return ("Event: " + str(dict["event"]) + "\n" + 
				"Venue: " + str(dict["venue"]) + "\n" +
				"Date : " + str(dict["date"]) + "\n" +
				"Time: " + str(dict["from"]) + " to " + str(dict["to"]))

	def send_help(self):
		help_text = ""
		intro = ("A telegram bot is just like a telegram user (like your friends)." + 
				"You can chat with it, and depending on what the bot is programmed to do, it will reply you differently.\n" +
				"This bot is designed to help you manage your appointments by adding events into your Google calendar " +
				"without you having to exit from telegram (after making plans with your friends).\n\n")
		help_text += intro
		command_intro = ("To interact with this bot, you must type the commands that this bot supports " +
						"(commands are pre-fixed by a slash: e.g. /command). You can use me by entering the following commands: \n\n")
		command_one = "/login - login to your google account\n"
		command_two = "/upcomingevents - view your upcoming events\n"
		command_three = ("@secretary99_bot - This is what we call an inline command. " + 
						"This command can be used in any chat whereas the previous commands can only be use "	+ 
						"when you are in the bot's chat room\n" + 
						"This command allows you to add events to your calendar by typing the following line, and clicking on the pop up that appears: \n" + 
						"@secretary99_bot add <event> at <venue> on <date> from <start time> to <end time>\n" + 
						"e.g.: \"@secretary99_bot add dinner with friends at Orchard Ion on 29/06/ from 7pm to 9pm\"\n")
		command_four = "/nextfreeday - see when is the nearest day from tommorow onwards with no events"
		help_text += command_intro + command_one + command_two + command_three + command_four
		add_event_from_chat = ("\nTo add event from this chat, simply type add <event> at <venue> on <date> from <start time> to <end time>\n")
		help_text += add_event_from_chat
		return help_text

	def bot_intro(self, chat_id):
		intro = "This bot allows you to add event in 2 ways:\n"
		self.sendMessage(chat_id, intro)
		add_event_inchat = "1. Chat with me!\n To add event, type the following to me: add <event> at <venue> on <date e.g. dd/mm> from <start time e.g. 10am, 10.30am, 1359> to <end time>\n"
		self.sendMessage(chat_id, add_event_inchat)
		add_event_inline = (" 2. Summon me from other chat rooms! To summon me, type: @secretary99_bot, followed by:   add <event> at <venue> on <date e.g. dd/mm> from <start time e.g. 10am, 10.30am, 1359> to <end time>" +
						"and click on the pop up that appears: \n" + 
						"e.g.: \"@secretary99_bot add dinner with friends at Orchard Ion on 29/06 from 7pm to 9pm\"\n" + 
						"And CLICK on the pop up that appears!\n")
		self.sendMessage(chat_id, add_event_inline)
		show_upcoming = "This bot also allows you to see your upcoming events! To see them. type: /upcomingevents"
		self.sendMessage(chat_id, show_upcoming)
		show_next_free = "This bot also tells you when is the next day from tommorow onwards with no events! Type: /nextfreeday to try."
		self.sendMessage(chat_id, show_next_free)

	def add_event(self, chat_id, query_string):
		details = self.parser.parse_command(query_string)
		try:
			success = self.gCal.add_event(chat_id, details["event"], details["venue"], details["date"], details["from"], details["to"])
			if success != False:
				self.sendMessage(chat_id, "Event: \"" + details["event"] + "\" successfully added!\nLink: " + success)
			else:
				self.sendMessage(chat_id, "Event failed to add :(")
		except HttpAccessTokenRefreshError, e:
			print "HttpAccessTokenRefreshError", e
			self.sendMessage(chat_id, "Invalid Login! Enter \"/login\" to login to your Google account again")
		except HttpError, err:
			if err.resp.status == 400:
				if err.resp.get('content-type', '').startswith('application/json'):
					error_dict = json.loads(err.content)
					if error_dict["error"]["errors"][0]["reason"] == "timeRangeEmpty":
						error_resp = ("Error occured when adding your event! Ensure that your start time is before your end time")
						self.sendMessage(chat_id, error_resp)
			else:
				error_resp = ("Error occured when adding your event! Ensure that you enter in the following format: \n" + 
								"Add <event> at <venue> on <date> from <start time> to <end time>")
				self.sendMessage(chat_id, error_resp)
			error_msg = 	"HttpError occured when adding event: " + query_string + "\n"
			if err.resp.get('content-type', '').startswith('application/json'):
				error_msg += pformat(json.loads(err.content))
			self.sendMessage(Secret.MY_ID, error_msg)
			

def main():
	testing = True
	token = None
	if testing:
		token = Secret.TEST_TOKEN
	else:
		token = Secret.LIVE_TOKEN
	bot = SecretaryBot(token, testing)
	bot.setWebhook()
	bot.message_loop()
	# print bot.getMe()
	print "Listening"
	while 1:
		time.sleep(10)
		

if __name__ == '__main__':
	main()

