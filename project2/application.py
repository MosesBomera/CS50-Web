from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from flask_session import Session

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
        "helloworld" : {
        "created_by": "moses",
        "messages": [
            {"timestamp": "17:03", "sent_by":"moses", "message":"hi"},
            {"timestamp": "17:03", "sent_by":"allen", "message":"homies"},
            {"timestamp": "12:23", "sent_by":"moses", "message":"hi, allen"},
        ]},
        "helloworld2" : {
        "created_by": "moses",
        "messages": [
            {"timestamp": "17:03", "sent_by":"moses", "message":"hello, musa"}
        ]},
        "helloworld34" : {
        "created_by": "house44",
        "messages": [
            {"timestamp": "17:03", "sent_by":"allen", "message":"homies"},
            {"timestamp": "12:23", "sent_by":"moses", "message":"hi, allen"},
        ]}

}

# messages; keep only a hundred messages at a time
MESSAGE_LIMIT = 100
MESSAGES = [None] * MESSAGE_LIMIT

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

        # send user to the chat room, for now.
        return render_template(
            "chatroom.html",
            displayname=displayname,
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

        return render_template(
            "chatroom.html",
            displayname=displayname,
            channels=channels)

    # New user, return create profile
    return render_template("index.html")

@app.route("/logout")
def logout():
    # end session
    session.pop('displayname', None)
    # redirect to log in page
    return render_template("index.html")

@app.route("/channel/<string:channel_name>", methods=["GET"])
def channel(channel_name):
    """Returns the messages from a given channel asynchronously."""

    # Get channel details
    channel = CHANNELS.get(channel_name)
    messages = channel.get("messages")

    # send a JSON asynchronously
    return jsonify(messages)

@io.on('chat message')
def connection(data):
    temp = {}
    temp["timestamp"] = data["timestamp"]
    temp["sent_by"] = data["displayname"]
    temp["message"] = data["message"]

    channel = CHANNELS.get(data['channel'])

    if len(channel.get('messages')) >= 100:
        # Remove the last element
        channel.get('messages').pop(0)
    channel.get('messages').append(temp)

    io.emit('chat message', temp, broadcast=True)

@io.on('add channel')
def add_channel(data):
    newchannel = data["newchannel"]
    created_by = data["created_by"]
    CHANNELS[newchannel] = {
        "created_by": created_by,
        "messages": MESSAGES
    }
    emit('create channel', {"channel": newchannel}, broadcast=True)

@io.on('join')
def join_room(data):
    """When a user joins a new channel."""
    displayname = session['displayname']
    room = data['room']
    join_room(room)
    send(displayname + 'joined channel', room=room)

@io.on('leave')
def leave_room(data):
    """When a user leaves the given channel."""
    displayname = session['displayname']
    room = data['room']
    leave_room(room)
    send(displayname + ' left channel', room=room)
