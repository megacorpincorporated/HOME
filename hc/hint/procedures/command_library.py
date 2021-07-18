import json
import logging

from rabbitmq_client import RMQProducer, QueueParams

from util import get_arg
from hc_defs import CLI_HUME_UUID


LOGGER = logging.getLogger(__name__)

HINT_MASTER_COMMAND_QUEUE = "hint_master"
producer: RMQProducer
_hint_queue_params = QueueParams(HINT_MASTER_COMMAND_QUEUE, durable=True)


def init(producer_instance):
    """
    :type producer_instance: rabbitmq_client.RMQProducer
    """
    global producer
    producer = producer_instance


def encode_hint_command(command):
    """Formats a HINT command."""
    command["uuid"] = get_arg(CLI_HUME_UUID)
    return json.dumps(command)


def discover_devices_done(command):
    """
    This is just a forward of what was returned by DC since the messages look
    exactly the same.

    :type command: dict
    """
    LOGGER.info("sending discover devices result to HINT")
    producer.publish(encode_hint_command(command),  # noqa
                     queue_params=_hint_queue_params)


def confirm_attach_result(command):
    """
    This is just a forward of what was returned by DC since the messages look
    exactly the same.

    :type command: dict
    """
    LOGGER.info("sending confirm attach result to HINT")
    producer.publish(encode_hint_command(command),  # noqa
                     queue_params=_hint_queue_params)
