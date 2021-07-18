import signal
import sys
import threading
import argparse
import logging

import hume_storage

from util import set_args, set_up_logger_for, HANDLER_STREAM
from device import application as device
from hc_communication import application as dispatch


LOGGER = logging.getLogger(__name__)

UTIL = [
    hume_storage
]

APPLICATIONS = [
    device, dispatch
]


def parse_args():
    """
    Parse arguments provided at running the python program.
    """
    parser = argparse.ArgumentParser(
        description="HUME device controller"
    )

    #
    # Positional arguments
    #

    # HUME identification
    parser.add_argument('hume_uuid',
                        metavar="HUME_UUID",
                        help="HUME UUID")

    #
    # Optional arguments
    #

    # Testing arguments are prepended with "--test", or "-t" for short.

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
    """Sets up DC logging."""
    set_up_logger_for("DC",
                      None,
                      logging.INFO,
                      HANDLER_STREAM)
    set_up_logger_for("DC",
                      "hume_storage",
                      logging.INFO,
                      HANDLER_STREAM)
    set_up_logger_for("DC",
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

    # Only set up logging if DC is run standalone and not from HTT. Rely on HTT
    # to set up logging otherwise.

    # print(f"DC sys.path: {sys.path}")

    set_up_interrupt()
    start()

    threading.Event().wait()  # Blocks indefinitely
