from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from threading import Thread
import time
import pika
import argparse
import json
import queue

async_mode = "threading"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
users = {}
namespace_to_user = {}


class Rabbit:
    def __init__(self):
        self.credentials = pika.PlainCredentials('rabbit', 'rabbit')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/',
                                                                            self.credentials))

    def formatqueueName(self, user):
        return "chanel_{}".format(user.id)

    def createSender(self, user):
        queueName = self.formatqueueName(user)
        channel = self.connection.channel()
        channel.queue_declare(queue=queueName)

        return RabbitSender(channel, queueName, user)

    def createReceiver(self, user):
        queueName = self.formatqueueName(user)

        channel = self.connection.channel()
        channel.queue_declare(queue=queueName)

        return RabbitReceiver(channel, queueName, user)


class RabbitSender():
    def __init__(self, channel, queueName, user):
        self.channel = channel
        self.queueName = queueName
        self.user = user

    def send(self, fromUserId, msg):
        msg["from"] = fromUserId
        text = json.dumps(msg)

        self.channel.basic_publish(exchange='',
                                   routing_key=self.queueName,
                                   body=text)


class RabbitReceiver(Thread):
    def __init__(self, channel, queueName, user):
        Thread.__init__(self)

        channel.basic_consume(self.recvMessageCallback,
                              queue=queueName,
                              no_ack=True)
        self.user = user
        self.channel = channel
        self.queueName = queueName

    def run(self):
        self.working = True

        while self.working:
            self.channel.start_consuming()

    def recvMessageCallback(self, ch, method, properties, body):
        global queueOfPendingMessageToSend

        text = body.decode('utf8')
        msg = json.loads(text)

        print("Msg received : {}, sending to {}".format(msg, self.user.namespace))

        socketio.emit('msg', msg, namespace=self.user.namespace, json=True)


rabbit = Rabbit()


class User():
    def __init__(self, userId):
        self.id = userId
        self.connected = False
        self.sender = rabbit.createSender(self)

    def connect(self, sid):
        global namespace_to_user

        self.namespace = "/{}".format(sid)

        namespace_to_user[self.namespace] = self

        if not self.connected:
            self.connected = True
            self.receiver = rabbit.createReceiver(self)
            self.receiver.start()

    def disconnect(self):
        global namespace_to_user

        self.connected = False
        self.receiver.working = False
        self.receiver.stop()
        del namespace_to_user[self.namespace]


@app.route("/")
def hello():
    return app.send_static_file("client.html")
    '''
    with open("clientr.html", 'rb') as f:
        content = f.read()
        return content.decode('UTF-8')
'''


@app.route('/static/<path>')
def static_file(path):
    return app.send_static_file(path)


@socketio.on('msg')
def handle_auth(json):
    global rabbit
    global users

    print('IN : {}'.format(json))
    print ("Request sid {}".format(request.sid))

    if json["op"] == 'auth':
        userId = json["user"]

        if userId not in users:
            users[userId] = User(userId)

        namespace = request.sid

        users[userId].connect(namespace)

        result = {"op": "auth", "ack": 1, "namespace": namespace}

        emit('auth', result, json=True)

    elif json["op"] == 'ping':
        json["ack"] = 1
        emit('ping', json, json=True)

    elif json["op"] == 'msg':
        users[json["to"]].sender.send(namespace_to_user["/{}".format(request.sid)].id, json)


@socketio.on('connect')
def connect():
    global thread
    print ("Request connection sid {}".format(request.sid))


@socketio.on('disconnect')
def disconnect():
    print("Disconnect sid {}".format(request.sid))
    # namespace_to_user["/{}".format(request.sid)].disconnect()


if __name__ == '__main__':
    socketio.run(app)
