import os
from myBot import SecretaryBot
import Secret
from flask import Flask, request, redirect
import cf_deployment_tracker
import telepot
import base64

try:
	from Queue import Queue
except ImportError:
	from queue import Queue

# Emit Bluemix deployment event
cf_deployment_tracker.track()
app = Flask(__name__)
port = int(os.getenv('VCAP_APP_PORT', 8080))
testing = False
token = None
if testing:
	token = os.environ["TEST_TOKEN"]
else:
	token = os.environ["LIVE_TOKEN"]

SECRET = '/bot' + token
URL = 'secretarybot.mybluemix.net' 
UPDATE_QUEUE = Queue()
myBot = SecretaryBot(token, testing)

def on_chat_message(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	print "CHAT ID IS " + str(chat_id)
	print msg
	myBot.sendMessage(chat_id, msg['text'])

@app.route('/')
def hello_world():
	return 'Hello World'

@app.route(SECRET, methods=['GET', 'POST'])
def pass_update():
	UPDATE_QUEUE.put(request.data)  # pass update to bot
	return 'OK'

@app.route('/oauthtest', methods=['GET'])
def sendTokenTest():
	oauth_token = request.args.get('code')
	encoded = base64.b64encode(oauth_token)
	url = "https://telegram.me/Learn1Bot?start=" + encoded
	return redirect(url, code=301)

@app.route('/oauth', methods=['GET'])
def sendToken():
	oauth_token = request.args.get('code')
	encoded = base64.b64encode(oauth_token)
	url = "https://telegram.me/secretary99_bot?start=" + encoded
	return redirect(url, code=301)

myBot.message_loop({'chat': myBot.on_chat_message,
                  'callback_query': myBot.on_callback_query,
                  'inline_query': myBot.on_inline_query,
                  'chosen_inline_result': myBot.on_chosen_inline_result}, source=UPDATE_QUEUE)  # take updates from queue
if __name__ == '__main__':
	myBot.setWebhook() # unset if was set previously
	myBot.setWebhook(URL + SECRET)
	# print(URL+SECRET)
	app.run(host='0.0.0.0', port=port)


