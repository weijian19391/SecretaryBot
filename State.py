
#A state object for every user, for them to add events.

DESC = "Desc"
DATE = "date"
TIME = "time"
VENUE = "venue"

class State(object):
	"""docstring for State"""
	def __init__(self):
		super(State, self).__init__()
		self.event = {DESC : "" , DATE : "", TIME : "", VENUE : ""}
		self.prev_cmd = ""
		self.msg_to_replace = ""
		self.curr_ans = ""

	def questionToAskNext(self):
		if "" == self.event[DESC]:
			self.curr_ans = DESC
			return False, "What event are you adding?"
		elif "" == self.event[DATE]:
			self.curr_ans = DATE
			return False, "What is the date of the event?"
		elif "" == self.event[VENUE]:
			self.curr_ans = VENUE
			return False, "At where?"
		elif "" == self.event[TIME]:
			self.curr_ans = TIME
			return False, "From what time to what time?"
		else:
			return True, ""

	def eventToStringForUser(self):
		event = "Event: " + str(self.event[DESC]) + "\n"
		date = "Date: " + str(self.event[DATE]) + "\n"
		time = "Time: " + str(self.event[TIME]) + "\n"
		venue = "Venue: " + str(self.event[VENUE])
		return event + date + time + venue

	def eventToStringForGCal(self):
		event = str(self.event[DESC])
		date = str(self.event[DATE])
		time = str(self.event[TIME])
		venue = str(self.event[VENUE])
		return "add " + event + " at " + venue + " on " + date + " from " + time

	def populateAns(self, ans):
		self.event[self.curr_ans] = ans

def main():	
	myState = State()
	finishedAsking, question = myState.questionToAskNext()
	if finishedAsking :
		print question
	else:
		print question
		myState.populateAns("meeting friends for kbox")
	print myState.eventToString()
	finishedAsking, question = myState.questionToAskNext()
	if finishedAsking :
		print question
	else:
		print question
		myState.populateAns("12/7")
	print myState.eventToString()
if __name__ == '__main__':
	main()