from datetime import datetime
"""
	This class is responsible for parsing the text from user into the event dictionary
	--Supports the following general format:
		1.add event at place on xx/xx from xxxx to xxxx
			e.g.add meeting lala at westmall on 12/07 from 1000 to 1200
		2.add event at place on dd/mm/yy or dd/mm/yyyy from hhmm to hhmm
			e.g.add meeting lala at westmall on 12/07/2016 (or 12/07/16) from 1000 to 1200
	--Time format:
		1. Hpm (1pm)
		2. HMMpm (130pm)
		3. H.MMpm (1.30pm)
		4. HHMM (1230)
	--Date format:
		1. D/M (7/7)
		2. DD/MM (07/07)
		3. DD/MM/YY (07/07/26)
"""
class CommandParsing(object):
	def __init__(self):
		super(CommandParsing, self).__init__()
		self.keywords = ["add", "at", "on", "from", "to"]

	def parse_command(self, event_string):
		parsed_text = {"event" : "" , "venue" : "", "date": "",
								"from" : "", "to" : ""}
		keywords_index = [-1, -1, -1, -1, -1, -1] #store the index of the keyword in the follow order: Add <event>, at <venue>, on <date> from, to
																#includes the index+1 for the last element in the string array (+1 due to the nature of xrange)
		event_string_arr = event_string.split(" ")
		event_details_arr = []
		event_details_arr.append("")
		x = 1
		for y in xrange(0,len(event_string_arr)):
			if x >= len(self.keywords):
				event_details_arr[len(event_details_arr)-1] += event_string_arr[y] + " "
			else:
				if event_string_arr[y] != self.keywords[x]:
					event_details_arr[len(event_details_arr)-1] += event_string_arr[y] + " "
				else:
					event_details_arr[len(event_details_arr)-1] = event_details_arr[len(event_details_arr)-1][:-1]
					event_details_arr.append(self.keywords[x] + " ")
					x += 1
		event_details_arr[len(event_details_arr)-1] = event_details_arr[len(event_details_arr)-1][:-1]
		print event_details_arr

		for details in event_details_arr:
			# print details,
			# print details[:3].lower()
			if details[:3].lower() == "add":
				parsed_text["event"] = details[4:]
			if details[:2].lower() == "at":
				parsed_text["venue"] = details[3:]
			if details[:2].lower() == "on":
				parsed_text["date"] = self.convert_date(details[3:])
			if details[:4].lower() == "from":
				if details[-2:].lower() == "am" or details[-2:].lower() == "pm":
					parsed_text["from"] = self.convert_time(details[5:-2], details[-2:].lower())
				else:
					parsed_text["from"] = details[5:]
			if details[:2].lower() == "to":
				if details[-2:].lower() == "am" or details[-2:].lower() == "pm":
					parsed_text["to"] = self.convert_time(details[3:-2], details[-2:].lower())
				else:
					parsed_text["to"] = details[3:]
		return parsed_text

	"""
	returns a 24hrs time in the following format: HHMM
	"""
	def convert_time(self, time, period):
		time_24_hours = None
		converted_time = -1
		if "." in time or ":" in time:
			index_of_symbol = time.index(".") if "." in time else time.index(":")
			hour = ("0" + time[0:index_of_symbol])[-2:]
			minute = time[index_of_symbol+1:]
			time_24_hours = int(hour+minute)
		elif len(time) == 4:
			time_24_hours = int(time)
		else:
			time_24_hours = int(str(int(time) * 100)[:4])
		# print time_24_hours
		if period == "am":
			if time_24_hours >= 1200 and time_24_hours <= 1259:
				converted_time = (time_24_hours + 1200) % 2400
			else:
				converted_time = time_24_hours
		if period == "pm":
			if time_24_hours >= 100 and time_24_hours <= 1159:
				converted_time = (time_24_hours + 1200) % 2400
			else:
				converted_time = time_24_hours
		return  "%04d"%converted_time

	"""
	returns a date in the following format: DD/MM/YYYY
	"""
	def convert_date(self, date):
		event_year = None
		event_month = None
		event_day = None
		date_details = None
		if "/" in date or "-" in date:
			date_details = date.split("/") if "/" in date else date.split("-")
			if len(date_details) > 2:
				event_year = str(2000 + int(date_details[2][-2:]))
			else:
				event_year = str(datetime.now().year)
		# print event_year
		event_month = "%02d"%int(date_details[1])
		# print event_month
		event_day = "%02d"%int(date_details[0])
		# print event_day
		parsed_date = event_day + "/" + event_month + "/" + event_year
		return parsed_date

testing_convert_time = False
if testing_convert_time:
	test_case_am = ["1", "1.30", "0130", "01", "0545", "0933", "12", "1200", "1159", "11.59", "12.59", "1259", "1:30"]
	test_case_am_ans = ["0100", "0130", "0130", "0100", "0545", "0933", "0000", "0000", "1159", "1159", "0059", "0059", "0130"]
	test_case_pm = ["1", "1.30", "0130", "01", "0545", "0933", "12", "1200", "1159", "11.59", "12.59", "1259", "1:30"]
	test_case_pm_ans = ["1300", "1330", "1330", "1300", "1745", "2133", "1200", "1200", "2359", "2359", "1259", "1259", "1330"]
	parsing = CommandParsing()
	test_all = True
	if test_all:
		for x in xrange(0,len(test_case_am)):
			if parsing.convert_time(test_case_am[x], "am") != test_case_am_ans[x]:
				print test_case_am[x],
				print "am input gives ",
				print parsing.convert_time(test_case_am[x], "am")
		for x in xrange(0,len(test_case_pm)):
			if parsing.convert_time(test_case_pm[x], "pm") != test_case_pm_ans[x]:
				print test_case_pm[x],
				print "pm input gives ",
				print parsing.convert_time(test_case_pm[x], "pm")
	else:
		print "output:" ,parsing.convert_time(test_case_am[3], "am")

testing_convert_date = False
if testing_convert_date:
	test_case = ["07/07", "7/7", "07/06/16", "07/05/2016", "7/6/16", "07-07", "7-7", "07-06-16", "07-05-2016"]
	test_case_ans = ["07/07/2016", "07/07/2016", "07/06/2016", "07/05/2016", "07/06/2016", "07/07/2016", "07/07/2016", "07/06/2016", "07/05/2016"]
	parsing = CommandParsing()
	test_all = True
	if test_all:
		for x in xrange(0,len(test_case)):
			if parsing.convert_date(test_case[x]) != test_case_ans[x]:
				print "output is",
				print parsing.convert_date(test_case[x])
				print "actual is " + test_case_ans[x]
	else:
		print parsing.convert_date(test_case[2])