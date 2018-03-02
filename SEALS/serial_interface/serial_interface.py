from queue import Queue
from select import select
from serial import Serial
from threading import Thread, Event

from .events import *
#from camera.snapshot import concurrent_snapshot

import requests


# State objects
ALARM_RAISED = False


# Messaging mechanisms
AWAITING_REPLY = False
REPLY_MESSAGE = None

COMMAND_BUFFER = Queue()


# Serial connection
# RPI
#CONNECTION = Serial(port='/dev/ttyACM0', baudrate=9600)
# MAC
CONNECTION = Serial(port='/dev/tty.usbmoem1411', baudrate=9600)


class EventThread(Thread):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(EventThread, self).__init__(*args, **kwargs)
        self.event = Event()

    def run(self):
        """

        :return:
        """
        global AWAITING_REPLY
        global REPLY_MESSAGE
        print("Command waiter started")
        while True:
            self.event.wait()
            self.event.clear()  # If the flag is not cleared, the next wait will return immediately.

            # Prevents a new command from interrupting the current sequence.
            AWAITING_REPLY = True

            handler, command = COMMAND_BUFFER.get()
            print("SERI SERVER: Got command: ", command)
            if command == 'shutdown':
                break

            send_message(str(command))

            # Wait for reply.
            try:
                print("SERI SERVER: Waiting for reply from arduino")
                self.event.wait(timeout=2.0)
            except TimeoutError:
                print("SERI SERVER: Reply timed out")
                REPLY_MESSAGE = EVENT[ERR]
            finally:
                self.event.clear()  # Keep a cleared event flag!
                notify_reply(handler)
                AWAITING_REPLY = False


writer_thread = EventThread()


def start():
    """

    :return:
    """
    writer_thread.start()
    listener_daemon = Thread(target=serial_select, daemon=True)
    listener_daemon.start()


def serial_select():
    """

    :return:
    """
    print("Select waiter started")
    while True:
        # Since no timeout is specified, block until read is available
        # ------------------------------
        # BLOCKS
        select([CONNECTION], [], [])
        # ------------------------------
        
        event = CONNECTION.readline()
        event_notification(decode(event))


def decode(message):
    """

    :param message:
    :return:
    """
    decoded_string = message.decode('utf-8')
    return decoded_string.strip()


def encode(message):
    """

    :param message:
    :return:
    """
    return message.encode('utf-8')


def send_message(message):
    """

    :param message:
    :return:
    """
    message = encode(message)
    CONNECTION.write(message)


def reply(main, sub):
    """

    :param main:
    :param sub:
    :return:
    """
    send_message(str(main) + ' ' + str(sub))


def alarm_raised(sub):
    """

    :param sub:
    :return:
    """
    global ALARM_RAISED
    ALARM_RAISED = sub == EVENT_SUB_CAUSE[ON]
    print("SERI SERVER: Alarm is raised: ", ALARM_RAISED)
    reply(PROXIMITY_ALARM, sub)

    # TODO Add HTTP request to localhost:8000, directly to web server
    alarm_status = 'on' if sub == '1' else 'off'
    if alarm_status == 'on':
        #concurrent_snapshot()
        print('Picture!')

    requests.get('http://localhost:8000/events/alarm/' + alarm_status)


def reply_received(sub):
    """

    :param sub:
    :return:
    """
    global REPLY_MESSAGE
    REPLY_MESSAGE = sub
    writer_thread.event.set()


def get_distance(sub):
    """

    :param sub:
    :return:
    """
    reply_received(sub)


def error(sub):
    """

    :param sub:
    :return:
    """
    print("An error was received!")


def event_notification(event):
    """

    :param event:
    :return:
    """
    print("SERI SERVER: Event notification: ", event)
    event_info = event.split(" ")

    if len(event_info) > 1:
        main, sub = event_info
        events[main](sub)
    else:
        events[event_info[0]]()


events = {
        EVENT[PROXIMITY_ALARM]: alarm_raised,
        EVENT[GET_DISTANCE]: get_distance,
        EVENT[ERR]: error,
    }


def execute_command(handler, command):
    """

    :param command:
    :param handler:
    :return:
    """
    global AWAITING_REPLY
    if AWAITING_REPLY:
        handler.resolve_wait()
        return

    COMMAND_BUFFER.put((handler, command))
    writer_thread.event.set()


def notify_reply(handler):
    """

    :param handler:
    :return:
    """
    print("SERI SERVER: Notifying HTTP SERVER")
    handler.resolve_wait(reply=REPLY_MESSAGE)
