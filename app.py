from flask import Flask, request, abort, g, render_template
import json
import peewee as pw

from slackclient import SlackClient
# Your app's Slack bot user token
SLACK_BOT_TOKEN = 'xoxb-2181645134-568938734263-nEY50t9VPDc9DycpgOvR1RHZ'
#SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

# Slack client for Web API requests
sc = SlackClient(SLACK_BOT_TOKEN)

app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
from db import db
from models import House, Person, Point

def choose_name(user):
    if user['profile']['display_name'] == "":
        return user['profile']['real_name']
    else:
        return user['profile']['display_name']

# Ensure a separate connection for each thread
@app.before_request
def before_request():
    g.db = db
    g.db.connect()
    try:
        users = [ {'slack_id': i['id'], 'name':choose_name(i), 'house': 5} for i in sc.api_call("users.list").get('members')]
        for i in users:   
            Person.insert(**i).on_conflict(
                    conflict_target=[Person.slack_id],  # Which constraint?
                    update={Person.name:i['name']}).execute()
    except:
        pass


@app.after_request
def after_request(response):
    g.db.close()
    return response


database = {}
houses = [i.name for i in House.select().where(House.name !="unknown")]

message_attachments = [
    {
        "fallback": "Upgrade your Slack client to use messages like these.",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "callback_id": "sorting_hat",
        "actions": [ { "name": i,
            "text": i.title(),
            "type": "button",
            "value": i.lower()
            } for i in houses ]
    }
]

@app.route('/')
def hello_world():
    query = House.select(House.name, pw.fn.COUNT(Point.id).alias('ct')).group_by(House.name).join(Point, pw.JOIN.LEFT_OUTER).where(House.name != "unknown").order_by(House.id)
    return render_template('index.jade', points=query, houses=houses)

@app.route('/points', methods=['POST'])
def points():
    if request.json.get('challenge'):
        return request.json['challenge']
    
    elif request.json.get('event').get('type') == "reaction_added":
        try:
            targetuser = request.json.get('event')['item_user']
        except KeyError:
            abort(500)
        awardinguser = request.json.get('event')['user']
        for i in [targetuser, awardinguser]:
            reactuserinfo = sc.api_call("users.info", user=i).get('user')
            reactuser = {'slack_id': reactuserinfo['id'], 'name':choose_name(reactuserinfo), 'house': 5}
            Person.insert(**reactuser).on_conflict(
                    conflict_target=[Person.slack_id],  # Which constraint?
                    update={Person.name:reactuser['name']}).execute()

        giveuser = Person.get(slack_id=awardinguser)
        receiveuser = Person.get(slack_id=targetuser)
        house = receiveuser.house

        print giveuser, receiveuser, house

        Point.create(house=house, receive=receiveuser, give=giveuser)

        return "Success"
    elif request.json.get('event').get('type') =="message" and request.json.get('event').get('channel_type') == "im":
        #print request.json.get('event')
        if request.json.get('event').get('text') == "!sort":
            sc.api_call(
            "chat.postMessage",
            channel=request.json.get('event').get('channel'),
            text="Where shall I put you?...",
            attachments=message_attachments
            )
        return "Success"
    else:
        print request.json.get('event')
        print request.form
        print request.json
        return "Success"

@app.route('/sortinghat', methods=['POST'])
def sortinghat():
    user = json.loads(request.form.get('payload'))['user']['id']
    house = json.loads(request.form.get('payload'))['actions'][0]['value']
    house = House.get(name=house)
    person = Person.get(slack_id=user)
    person.house = house
    person.save()
    return "Well, if you're sure...better be... {0} !!".format(house.name.title())