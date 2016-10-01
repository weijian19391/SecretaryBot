from pprint import pprint
import csv
"""
This class stores a chat_id and code dictionary for all users that log in before.
The code stored is prior to decoding
"""
class UserDb(object):
	def __init__(self):
		super(UserDb, self).__init__()
		self.all_users = []
		file = open("userdata.csv", "rt")
		try:
			reader = csv.reader(file)
			for row in reader:
				self.all_users.append(row[0])
		finally:
			file.close()
			self.all_users.remove("chat_id")
			print self.all_users
		
	def add_new_user(self, chat_id, first_name, last_name):
		if str(chat_id) not in self.all_users:
			try:
				file = open("userdata.csv", "ab")
				writer = csv.writer(file)
				writer.writerow((chat_id, first_name,last_name))
				self.all_users.append(str(chat_id))
				print "new user added", chat_id, first_name, last_name
			finally:
				file.close()