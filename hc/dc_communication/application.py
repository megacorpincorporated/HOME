import logging
import json

from rabbitmq_client import (
    RMQConsumer,
    RMQProducer,
    ConsumeParams,
    QueueParams,
    ConsumeOK
)

from util import get_arg
from hc_defs import CLI_HUME_UUID, MessageType
from hint.procedures import command_library

LOGGER = logging.getLogger(__name__)

_consumer = RMQConsumer()
_dc_command_queue_params: QueueParams

_producer = RMQProducer()
_hc_command_queue_params: QueueParams


"""
This module is the starting point of the dc_communication application,
responsible for registering callbacks for various HUME internal comm. types.
"""


def model_init():
    """
    Initialize models.
    """
    LOGGER.info("model-init")


def pre_start():
    """
    Pre-start, before starting applications.
    """
    LOGGER.info("pre-start")


def start():
    """
    Starts the hc_communication application
    """
    LOGGER.info("hc hc_communication start")
    global _dc_command_queue_params, _hc_command_queue_params
    _dc_command_queue_params = QueueParams(
        f"{get_arg(CLI_HUME_UUID)}-dc-commands", durable=True
    )
    _hc_command_queue_params = QueueParams(
        f"{get_arg(CLI_HUME_UUID)}-hc-commands", durable=True
    )

    _consumer.start()
    _consumer.consume(
        ConsumeParams(_incoming_command),
        queue_params=_hc_command_queue_params
    )
    _producer.start()


def stop():
    """
    Stops the hc_communication application
    """
    LOGGER.info("hc hc_communication stop")
    _consumer.stop()
    _producer.stop()


def forward_command_to_dc(command):
    """
    :type command: bytes
    """
    LOGGER.info("forwarding command to DC")

    _producer.publish(command, queue_params=_dc_command_queue_params)  # noqa


def dc_command(command_content):
    """
    Input must be possible to convert to valid JSON.

    :type command_content: dict
    """
    LOGGER.info("sending a command to DC")

    _producer.publish(
        json.dumps(command_content).encode('utf-8'),
        queue_params=_dc_command_queue_params  # noqa
    )


def _incoming_command(command):
    """
    :param command: DC command
    :type command: bytes
    """
    if isinstance(command, ConsumeOK):
        LOGGER.info("dc command handler got ConsumeOK")
        return

    LOGGER.info("got command from DC")

    decoded_command = json.loads(command.decode('utf-8'))
    command_type = decoded_command["type"]

    if command_type == MessageType.DISCOVER_DEVICES:
        LOGGER.info("received a discover devices complete from DC")
        # Just forward the whole thing, no need for a special procedure
        command_library.discover_devices_done(decoded_command)

    elif command_type == MessageType.CONFIRM_ATTACH:
        LOGGER.info("received a confirm attach result from DC")
        # Just forward the whole thing, no need for a special procedure
        command_library.confirm_attach_result(decoded_command)
