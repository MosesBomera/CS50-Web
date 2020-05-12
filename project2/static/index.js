document.addEventListener('DOMContentLoaded', () => {

  // Assumes one displayname per page
  const displayname = document.querySelector('#curr-displayname').innerHTML;

  // Initialize socket
  var socket = io();
  var channel = '';

  document.querySelector('.channel-list-item').addEventListener('click', e => {
      e.preventDefault();
      element = e.target;
      channel = element.innerHTML.trim();

      // Continue to load messages
      const request = new XMLHttpRequest();
      request.open('GET', `/channel/${channel}`);

      request.onload = () => {
        // messages
        const messages = JSON.parse(request.responseText);
        var x;

        const message_area = document.querySelector('#messages');
        message_area.innerHTML = '';
        for (x of messages) {
          const div = document.createElement('div');
          div.className = 'message-body';
          div.innerHTML = x.timestamp + ' ' + x.sent_by + ' ' + x.message;
          message_area.appendChild(div);
        };
      };

      // send request
      request.send();
      return false;

  });

  document.querySelector('#chat-form').onsubmit = (e) => {
    // prevent page from reloading
    e.preventDefault();
    var d = new Date();
    const timestamp = ("0" + d.getDate()).slice(-2) + "-" + ("0"+(d.getMonth()+1)).slice(-2) + "-" + d.getFullYear() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
    const message = document.querySelector('#message-text').value;
    // Send the message
    socket.emit('chat message', {
      'timestamp': timestamp,
      'displayname': displayname,
      'message': message,
      'channel': channel,
    });

    // Clear the input field
    document.querySelector('#message-text').value = '';
    return false;
  };

  document.querySelector('#channel-form').onsubmit = (e) => {
    // Prevent page from reloading
    e.preventDefault();
    const newchannel = document.querySelector('#channel-name').value;

    // Send channel
    socket.emit('add channel',{
        'newchannel': newchannel,
        'created_by': displayname
    });
    document.querySelector('#channel-name').value = '';
    return false;
  };

  // On receiving the broadcast
  socket.on('chat message', function(data) {
    const div = document.createElement('div');
    div.className = 'message-body';
    div.innerText = data.timestamp + ' ' + data.sent_by + ' ' + data.message;
    document.querySelector('#messages').append(div);
  });

  // On receiving channel broadcast
  socket.on('create channel', function(data) {
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = `channel/${data.channel}`;
    a.className = 'channel-list-item';
    a.innerText = data.channel;
    li.appendChild(a);
    document.querySelector('#channels-list').appendChild(li);
  });

  // Joining rooms
});
