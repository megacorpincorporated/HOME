import signal
import sys
import logging
import threading
import argparse

import hume_storage

from util import set_args, set_up_logger_for, HANDLER_STREAM
from dc_communication import application as dispatch
from hint import application as hint


LOGGER = logging.getLogger(__name__)

UTIL = [
    hume_storage
]

APPLICATIONS = [
    dispatch, hint
]


def parse_args():
    """
    Parse arguments provided at running the python program.
    """
    parser = argparse.ArgumentParser(
        description="HUME HINT controller"
    )

    # HUME identification
    parser.add_argument('hume_uuid',
                        metavar="HUME_UUID",
                        help="HUME UUID")

    # Connection args
    parser.add_argument('-hip',
                        '--hint-ip-address',
                        default='127.0.0.1',
                        help="HINT IP address")
    parser.add_argument('-hp',
                        '--hint-port',
                        type=int,
                        default=8000,
                        help="HINT port")
    parser.add_argument('-bip',
                        '--broker-ip-address',
                        default='127.0.0.1',
                        help="Central HINT broker IP address")
    parser.add_argument('-bp',
                        '--broker-port',
                        type=int,
                        default=5672,
                        help="Central HINT broker port")

    # print("Starting HC with the following arguments:")
    # print(parser.parse_args())

    return parser.parse_args()


def set_up_interrupt():
    """
    Ensures that the program can exist gracefully.
    :return:
    """

    def interrupt(_signum, _frame):
        """
        :param _signum:
        :param _frame:
        """
        stop()
        sys.exit(0)

    def terminate(_signum, _frame):
        """
        :param _signum:
        :param _frame:
        """
        stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, terminate)


def set_up_logging():
    """Sets up logging for HC."""
    set_up_logger_for("HC",
                      None,  # Root logger
                      logging.INFO,
                      HANDLER_STREAM)
    set_up_logger_for("HC",
                      "hume_storage",
                      logging.INFO,
                      HANDLER_STREAM)
    set_up_logger_for("HC",
                      "rabbitmq_client",
                      logging.INFO,
                      HANDLER_STREAM)
    pika_logger = logging.getLogger("pika")
    pika_logger.propagate = False


def start():
    """
    Starts the RootApp and all its sub-applications.
    """
    LOGGER.info("root start")

    # storage start
    hume_storage.start()

    # model init
    for app in APPLICATIONS:
        app.model_init()

    # pre start
    for app in APPLICATIONS:
        app.pre_start()

    # app start
    for app in APPLICATIONS:
        app.start()


def stop():
    """
    Stops all RootApp sub-applications in order to clean up used resources.
    """

    def print_exit_status():
        """
        Health check sort of, to see that resources are released properly when
        exiting.
        """
        print("----------------------------------------------")
        print("- STOP RESULTS -")
        print("----------------------------------------------")
        print("# THREADING")
        print(f"# Active threads: {threading.active_count()}")
        print("# List of threads:")
        for thread in threading.enumerate():
            print(f"# {thread}")

    LOGGER.info("root stop")

    # application stop
    for app in APPLICATIONS:
        app.stop()

    # core stop
    for app in UTIL:
        app.stop()

    print_exit_status()


if __name__ == "__main__":
    cli_args = parse_args()
    set_args(**vars(cli_args))

    set_up_logging()

    set_up_interrupt()
    start()

    threading.Event().wait()  # Blocks indefinitely
