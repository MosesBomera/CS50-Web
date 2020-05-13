from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from util import logged_in

app = Flask(__name__)
app.config["SECRET_KEY"] = 'u893j2wmsldrircsmc5encx'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
io = SocketIO(app)
Session(app)

# channels
"""
____________CHANNEL_VARIABLE_STRUCTURE________________
CHANNELS = {
    "channel_name": {
        "created_by": "displayname",
        "messages": [
            {"timestamp":, "sent_by":, "message":}
        ]
    }
}
"""
CHANNELS = {
        "ChannelOne" : {
        "created_by": "moses",
        "messages": [
            {"timestamp": "12-05-2020 17:01", "sent_by":"Moses", "message":"Hi, Allen"},
            {"timestamp": "12-05-2020 17:05", "sent_by":"Allen", "message":"Hi, Moses! How are you doing?"},
            {"timestamp": "12-05-2020 17:15", "sent_by":"Moses", "message":"I'm great, How about you?"},
        ]},
        "ChannelTwo" : {
        "created_by": "moses",
        "messages": [
            {"timestamp": "12-05-2020 17:01", "sent_by":"Moses", "message":"Hey Team!"},
        ]},
        "ChannelThree" : {
        "created_by": "house44",
        "messages": [
            {"timestamp": "12-05-2020 17:01", "sent_by":"Moses", "message":"Hi, Allen"},
            {"timestamp": "12-05-2020 17:05", "sent_by":"Allen", "message":"Hi, Moses! How are you doing?"},
            {"timestamp": "12-05-2020 17:15", "sent_by":"Moses", "message":"I'm great, How about you?"},
        ]}

}

# # messages; keep only a hundred messages at a time
# MESSAGE_LIMIT = 100
# MESSAGES = [None] * MESSAGE_LIMIT

# users
USERS = []

@app.route('/', methods=['POST', 'GET'])
def index():
    """Renders the root page depending on if a user is returning or new."""

    # Channels currently created
    channels = list(CHANNELS.keys())

    # If old user
    if 'displayname' in session:
        displayname = session['displayname']

        prompt = f"{displayname}, create a new channel or join an existing one below!"
        # send user to the channels page
        return render_template(
            "channels.html",
            prompt=prompt,
            channels=channels)

    # If a new user, create a profile
    if request.method == "POST":

        error = ''
        #check if the displayname name already exists
        displayname = request.form.get('displayname')

        if displayname in USERS:
            error = "Display name already exists"
            return render_template("index.html", error=error)
        else:
            session['displayname'] = displayname
            USERS.append(displayname)

        prompt = f"Welcome {displayname}, create a new channel or join an existing one below!"

        return render_template(
            "channels.html",
            prompt=prompt,
            channels=channels)

    # New user, return create profile
    return render_template("index.html")

@app.route("/logout")
def logout():
    # end session
    session.pop('displayname', None)
    # redirect to log in page
    return render_template("index.html")

@app.route("/channel/<string:channel_name>")
@logged_in
def channel(channel_name):
    """Returns the messages from a given channel."""

    # save the current channel
    session['curr_channel'] = channel_name
    # Get channel details
    channel = CHANNELS.get(channel_name)
    messages = channel.get("messages")

    # Remove current channel from the list
    channels = list(CHANNELS.keys())
    channels.remove(channel_name)

    # send a JSON asynchronously
    # return jsonify(messages)
    return render_template(
        "channel.html",
        channels = channels,
        messages=messages)

@app.route("/create_channel", methods=["POST"])
@logged_in
def create_channel():

    newchannel = request.form.get('newchannel')
    created_by = session['displayname']

    # update session
    session['curr_channel'] = newchannel
    CHANNELS[newchannel] = {
        "created_by": created_by,
        "messages": []
    }

    # Get channel details
    channel = CHANNELS.get(newchannel)
    messages = channel.get("messages")

    # Remove current channel from the list
    channels = list(CHANNELS.keys())
    channels.remove(newchannel)

    # Take user to channel
    return render_template('channel.html',
                        channels=channels)

@io.on('send message')
def chat(data):
    """ Receives the message and sends it to the defined room (channel)."""
    message = {}
    message["timestamp"] = data["timestamp"]
    message["sent_by"] = session['displayname']
    message["message"] = data["message"]

    curr_channel = session['curr_channel']
    channel = CHANNELS.get(curr_channel)

    if len(channel.get('messages')) >= 100:
        # Remove the first(oldest) element
        channel.get('messages').pop(0)
    channel.get('messages').append(message)

    io.emit('receive message', message, room=curr_channel)

# @io.on('add channel')
# def add_channel(data):
#     # channel created and available to everyone immediately.
#     newchannel = data["newchannel"]
#     created_by = session['displayname']
#     CHANNELS[newchannel] = {
#         "created_by": created_by,
#         "messages": MESSAGES
#     }
#     emit('create channel', {"channel": newchannel}, broadcast=True)

@io.on('join', namespace='/')
def join_channel():
    """When a user joins a new channel."""

    # Get the user and their current channel
    displayname = session['displayname']
    channel = session['curr_channel']

    # join them to the channel
    join_room(channel)

    emit('channel update',
        {'message': displayname + ' joined channel.',
         'channel': channel },
        room = channel)

@io.on('leave', namespace='/')
def leave_channel():
    """When a user leaves the given channel."""

    channel = session['curr_channel']

    # leave the channel
    leave_room(channel)

    emit('channel update',
        {'message': session['displayname'] + ' left.',
         'channel': channel },
        room = channel)
