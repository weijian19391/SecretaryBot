from cloudant.client import Cloudant
from oauth2client.file import Storage
import json

class CloudantDataBase(object):
	"""docstring for CloudantDataBase"""
	def __init__(self, *args, **kwargs):
		super(CloudantDataBase, self).__init__()
		self.db_username = args[0]
		self.db_password = args[1]
		self.db_url = args[2]
		self.database = None
		client = Cloudant(self.db_username, self.db_password, url = self.db_url)
		client.connect()

		session = client.session()
		self.database = client['things']

	def getUserCredential(self, user_fromId):
		credential = self.database[str(user_fromId)]
		return json.dumps(credential["data"])

	def createDbDocumentWithCredentials(self, credentials, chat_id):
		documentId = "{ \"_id\": \"" + str(chat_id) + "\", "
		storedCredentials = documentId + "\"data\": " + credentials.to_json() + "}"
		jsonCredentials = json.loads(storedCredentials)

		new_credentials = self.database.create_document(jsonCredentials)
		if new_credentials.exists():
			print 'SUCCESS!!'
def main():
	my_database = CloudantDataBase(USERNAME, PASSWORD, URL)
if __name__ == '__main__':
	main()