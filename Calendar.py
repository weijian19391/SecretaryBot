from oauth2client import client
from oauth2client.client import HttpAccessTokenRefreshError
from apiclient import discovery
import httplib2
import base64
import oauth2client
from oauth2client import tools
from datetime import datetime, timedelta
from pprint import pprint
import dateutil.parser
from dateutil import tz
from oauth2client.file import Storage
import json
from telepot.namedtuple import KeyboardButton
from CloudantDB import CloudantDataBase
import os

class GoogleCalendar(object):
	"""docstring for Calendar"""
	def __init__(self, test):
		super(GoogleCalendar, self).__init__()
		redirect = ""
		if test:
			redirect = "http://secretarybot.mybluemix.net/oauthtest"
		else:
			redirect = "http://secretarybot.mybluemix.net/oauth"
		self.flow = client.flow_from_clientsecrets(
				'client_secret.json',
				scope='https://www.googleapis.com/auth/calendar',
				redirect_uri=redirect)
		self.flow.params["access_type"] = "offline"
		self.flow.params["approval_prompt"] = "force"
		self.storage = None
		self.DAYS = ["Monday   ", "Tuesday  ", "Wednesday", "Thursday ", "Friday   ", "Saturday ", 'Sunday   ']
		self.resultMax = 100
		USERNAME = os.environ["CLOUDANT_USERNAME"]
		PASSWORD = os.environ["CLOUDANT_PASSWORD"]
		URL = os.environ["CLOUDANT_URL"]
		self.my_database = CloudantDataBase(USERNAME, PASSWORD, URL)

	def get_auth_uri(self):
		return self.flow.step1_get_authorize_url()

	def create_service(self,chat_id):
		try:
			credential_JSON = self.my_database.getUserCredential(chat_id)
			credential = client.Credentials.new_from_json(credential_JSON)
			if credential == None:
				raise HttpAccessTokenRefreshError(); #not really refresh error, just jiang jiu yi dian
			http_auth = credential.authorize(httplib2.Http())
			service = discovery.build('calendar', 'v3', http=http_auth)
			return service
		except HttpAccessTokenRefreshError, error_msg:
			raise error_msg
		except KeyError ,e:
			raise e

	def add_credentials(self,chat_id, code):
		auth_code = base64.b64decode(code)
		print "after decode is " + auth_code
		credentials = self.flow.step2_exchange(auth_code)
		self.my_database.createDbDocumentWithCredentials(credentials, chat_id)

	def get_upcoming_events(self, chat_id, nearest=False, tomorrow=False, week=False):
		events_string = ""
		datetime_obj = None
		date_str = ""
		day_str = ""
		time_str = ""
		service = self.create_service(chat_id)
		if nearest:
			time_now = datetime.utcnow().isoformat() + 'Z'
			try:
				eventsResult = service.events().list(
								calendarId='primary', timeMin=time_now, maxResults=1, singleEvents=True,
								orderBy='startTime').execute()
			except HttpAccessTokenRefreshError, e:
				raise e
			events = eventsResult.get('items', [])
		elif tomorrow:
			time_now = datetime.utcnow().isoformat() + 'Z'
			calendar_list_entry = self.create_service(chat_id).calendarList().get(calendarId='primary').execute()
		
			to_zone = tz.gettz(calendar_list_entry['timeZone'])
			from_zone = tz.gettz('UTC')
			utc = datetime.utcnow().replace(tzinfo=from_zone)
			local_time_zone = utc.astimezone(to_zone)
			local = local_time_zone
			date_tmr = (local + timedelta(days=1))
			date_midnight_tmr = date_tmr.replace(hour=0, minute=0, second=0)
			datedate_midnight_after_tmr = date_midnight_tmr + timedelta(days=1)

			utc_tmr = date_midnight_tmr.astimezone(from_zone).isoformat()[:-6] + 'Z'
			utc_after_tmr = datedate_midnight_after_tmr.astimezone(from_zone).isoformat()[:-6] + 'Z'
			try:
				eventsResult = service.events().list(
								calendarId='primary', timeMin=utc_tmr, timeMax=utc_after_tmr, maxResults=self.resultMax, singleEvents=True,
								orderBy='startTime').execute()
			except HttpAccessTokenRefreshError, e:
				raise e
			events = eventsResult.get('items', [])
		elif week:
			time_now = datetime.utcnow().isoformat() + 'Z'
			calendar_list_entry = self.create_service(chat_id).calendarList().get(calendarId='primary').execute()
			
			to_zone = tz.gettz(calendar_list_entry['timeZone'])
			from_zone = tz.gettz('UTC')
			utc = datetime.utcnow().replace(tzinfo=from_zone)
			local_time_zone = utc.astimezone(to_zone)
			date_midnight_after_week = local_time_zone + timedelta(days=7)
			print date_midnight_after_week
			utc_after_week = date_midnight_after_week.astimezone(from_zone).isoformat()[:-6] + 'Z'
			try:
				eventsResult = service.events().list(
								calendarId='primary', timeMin=time_now, timeMax=utc_after_week, maxResults=self.resultMax, singleEvents=True,
								orderBy='startTime').execute()
			except HttpAccessTokenRefreshError, e:
				raise e
			events = eventsResult.get('items', [])
		if not events:
			return "No upcoming events found."
		for event in events:
			datetime_str = event['start'].get("dateTime")
			if datetime_str != None:
				datetime_obj = dateutil.parser.parse(datetime_str)
				time_str = str(datetime_obj.strftime("%I:%M %p"))
				day_str = self.DAYS[datetime_obj.weekday()][0:3]
				date_str = str(datetime_obj.strftime("%d-%m-%Y"))
				events_string += date_str + " " + day_str + " " + time_str + "  "
			else :
				datetime_obj = dateutil.parser.parse(event["start"].get("date"))
				day_str = self.DAYS[datetime_obj.weekday()][0:3]
				date_str = str((datetime_obj).strftime("%d-%m-%Y"))
				events_string += date_str + " " + day_str + " " + "All Day   "
			events_string += event["summary"] + "\n"
		return events_string

	def add_event(self, chat_id, description, venue, date, start, end):
		event_year = int(date[6:])
		from_datetime_obj = datetime(year=event_year, month=int(date[3:5]), day=int(date[:2]), hour=int(start[:2]), minute=int(start[-2:]))
		# print from_datetime_obj
		to_datetime_obj = datetime(year=event_year, month=int(date[3:5]), day=int(date[:2]), hour=int(end[:2]), minute=int(end[-2:]))
		# print to_datetime_obj
		calendar_list_entry = self.create_service(chat_id).calendarList().get(calendarId='primary').execute()
		event = {
		  'summary': description,
		  'location': venue,
		  'start': {
		    'dateTime': from_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S"),
		    'timeZone': calendar_list_entry['timeZone'],
		  },
		  'end': {
		    'dateTime': to_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S"),
		    'timeZone': calendar_list_entry['timeZone'],
		  },	
		  'reminders': {
		    'useDefault': True,
		  },
		}
		service = self.create_service(chat_id)
		event = service.events().insert(calendarId='primary', body=event).execute()
		if event.get('htmlLink') != None:
			# print 'Event created: %s' % (event.get('htmlLink'))
			return event.get('htmlLink')
		else:
			return False

	def get_free_day(self, chat_id):
		events_string = ""
		datetime_obj = None
		time_now = datetime.utcnow().isoformat() + 'Z'
		user_time_now = None
		user_time_zone = None
		service = self.create_service(chat_id)
		free_date = None
		results_num = 7
		try:
			user_time_zone = service.events().list(
							calendarId='primary', timeMin=time_now, maxResults=results_num, singleEvents=True,
							orderBy='startTime', fields='timeZone').execute()
		except HttpAccessTokenRefreshError, e:
			raise e 
		user_time_now = datetime.now(tz.gettz(user_time_zone["timeZone"]))
		while not free_date:
			curr_date = user_time_now
			try:
				eventsResult = service.events().list(
								calendarId='primary', timeMin=time_now, maxResults=results_num, singleEvents=True,
								orderBy='startTime', fields='items').execute()
			except HttpAccessTokenRefreshError, e:
				raise e 
			events = eventsResult.get('items', [])
			for event in events:
				event_date = None
				datetime_str = event['start'].get("dateTime")
				if datetime_str != None:
					datetime_obj = dateutil.parser.parse(datetime_str)
					event_date = datetime_obj.strftime("%Y-%m-%d")
				else :
					event_date = (dateutil.parser.parse(event["start"].get("date"))).strftime("%Y-%m-%d")
				if str(curr_date.date()) != event_date:
					curr_date = curr_date + timedelta(hours=24)
					if str(curr_date.date()) != event_date:
						free_date = str(curr_date.strftime("%d-%m-%Y"))
						day_of_week = self.DAYS[curr_date.weekday()]
						return "Next free day is " + free_date + ", " + day_of_week
					
			results_num *= 2

	def get_cal_keyboard(self):
		print "hahhaa"
		first_row = [self.DAYS]
		first_row.append(['Plain text', KeyboardButton(text=u'\U0001F64C')])
		first_row.append([KeyboardButton(text="sdfsdf")])
		first_row.append([dict(text='Phone', request_contact=True), KeyboardButton(text='Location', request_location=True)])
		return first_row


# def main():

# if __name__ == '__main__':
# 	main()