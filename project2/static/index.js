document.addEventListener('DOMContentLoaded', () => {
  // connect to the socket
  var socket = io();

  //
  socket.on('connect',() => {
      // On Joining
      socket.emit('join');
  });


  // chat functionality
  // Send message
  document.querySelector('#chat-form').onsubmit = (e) => {
    // Prevent submission action
    e.preventDefault();
    const d = new Date();
    const timestamp = ("0" + d.getDate()).slice(-2) + "-" + ("0"+(d.getMonth()+1)).slice(-2) + "-" + d.getFullYear() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
    const message = document.querySelector('#message-text').value;

    // Send message
    socket.emit('send message',
                {"timestamp": timestamp,
                 "message": message});

    // Clear the input field
    document.querySelector('#message-text').value = '';
    return false;
  };

  // Receive message
  socket.on('receive message', message => {
        // Add message to DOM
        const div = addElement('div', 'message-box');
        const span1 = addElement('span', 'displayname', message.sent_by);
        const span2 = addElement('span', 'timestamp',' // ' + message.timestamp);
        const p = addElement('p', 'message-body', message.message);
        div.appendChild(span1);
        // Add // using CSS
        div.appendChild(span2);
        div.appendChild(document.createElement('br'));
        div.appendChild(p);
        document.querySelector('#messages').append(div);
  });

  // Announce joining or leaving
  socket.on('channel update', message => {
      const div = addElement('div', 'channel-notification', message.message);
      document.querySelector('#messages').append(div);

      // Remember channel
      localStorage.setItem('curr_channel', message.channel)
  });

  // Helper function
  function addElement(tag, classname, value) {
    const element = document.createElement(tag);
    element.className = classname;
    if (value !== undefined ) {element.innerHTML = value};
    return element;
  };

});
