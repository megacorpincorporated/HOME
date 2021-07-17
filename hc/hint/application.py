import logging
import pika

import hume_storage as storage

from rabbitmq_client import (
    RMQConsumer,
    RMQProducer,
    ConsumeParams,
    QueueParams
)

from hint.models import (
    HumeUser,
    BrokerCredentials,
    HintAuthentication
)
from hint import (
    request_library,
    command_handler,
    command_library
)
from util import get_arg
from hc_defs import (
    CLI_HUME_UUID,
    CLI_BROKER_IP_ADDRESS,
    CLI_BROKER_PORT
)

LOGGER = logging.getLogger(__name__)

_consumer = RMQConsumer()
_hume_queue_params: QueueParams

_producer = RMQProducer()


def model_init():
    """
    Initialize models.
    """
    LOGGER.info("model-init")
    storage.register(HumeUser)
    storage.register(BrokerCredentials)
    storage.register(HintAuthentication)


def pre_start():
    """
    Pre-start, before starting applications.
    """
    LOGGER.info("pre-start")

    def first_time_startup():
        """
        Called when HUME has no user account, usually on first startup.

        1. Pair the HUME with HINT, this should yield user information for
           the HUME.
        2. Use the credentials to authenticate.
        3. Get broker credentials (authenticated view)
        """
        LOGGER.debug("first time HUME setup running")
        user_info = request_library.pair()

        if user_info:
            LOGGER.debug("pairing successful, got credentials")
            username = user_info['username']
            password = user_info['password']
            hume_user = HumeUser(username=username, password=password)
            storage.save(hume_user)

            session_id = request_library.login(hume_user)
            if session_id:
                LOGGER.debug("login success")
                hint_auth = HintAuthentication(session_id)
                storage.save(hint_auth)

                broker_credentials = request_library.broker_credentials(
                    session_id
                )
                if broker_credentials:
                    LOGGER.debug("got broker credentials successfully")
                    username = broker_credentials['username']
                    password = broker_credentials['password']
                    new_broker_credentials = BrokerCredentials(
                        username=username,
                        password=password
                    )
                    storage.save(new_broker_credentials)
                else:
                    LOGGER.critical("broker credentials could not be "
                                    "gotten for some reason")
            else:  # session_id
                LOGGER.critical("newly gotten HUME user credentials "
                                "faulty, could not be used to "
                                "authenticate the HUME")
        else:  # user_info
            LOGGER.critical("HUME deadlocked, no user exists and pairing "
                            "failed")

    def verify_start_state(hume_user):
        """
        Verify the HUME reaches its starting state.

        1. Login (session id is not stored persistently)
        2. Check broker credentials present
           - If not, get credentials

        :param hume_user: HUME user info
        :type hume_user: HumeUser
        """
        LOGGER.info("getting the HUME in the correct starting state")
        session_id = request_library.login(hume_user)
        if session_id:
            LOGGER.debug("login success")
            hint_auth = HintAuthentication(session_id)
            storage.save(hint_auth)

            broker_credentials = storage.get(BrokerCredentials, None)
            if broker_credentials:
                LOGGER.debug("already have broker credentials")
                pass
            else:
                LOGGER.debug("fetching broker credentials")
                broker_credentials = request_library.broker_credentials(
                    session_id
                )
                if broker_credentials:
                    LOGGER.debug("got broker credentials successfully")
                    username = broker_credentials['username']
                    password = broker_credentials['password']
                    new_broker_credentials = BrokerCredentials(
                        username=username,
                        password=password
                    )
                    storage.save(new_broker_credentials)
                else:
                    LOGGER.critical("broker credentials could not be "
                                    "gotten for some reason")
        else:  # session_id
            LOGGER.critical("unable to authenticate using stored HUME "
                            "user credentials")

    hume_user = storage.get(HumeUser, None)

    if hume_user is None:
        # first time startup
        first_time_startup()
    else:
        verify_start_state(hume_user)


def start():
    """
    Starts up the HTTP listener.
    """
    LOGGER.info("hint start")

    # Fetch broker credentials
    broker_credentials = storage.get(BrokerCredentials, None)

    if broker_credentials is not None:
        credentials = pika.PlainCredentials(broker_credentials.username,
                                            broker_credentials.password)
    else:
        # Default fallback to avoid exceptions at this stage
        credentials = pika.PlainCredentials('guest', 'guest')
    conn_params = pika.ConnectionParameters(host=get_arg(
                                                CLI_BROKER_IP_ADDRESS
                                            ),
                                            port=get_arg(CLI_BROKER_PORT),
                                            virtual_host='/',
                                            credentials=credentials)

    global _consumer, _producer, _hume_queue_params
    _consumer = RMQConsumer(connection_parameters=conn_params)
    _producer = RMQProducer(connection_parameters=conn_params)

    _consumer.start()
    _producer.start()

    # Initialize command lib with producer instance
    command_library.init(_producer)

    # Consumer from the HUME's input command queue.
    _hume_queue_params = QueueParams(f"{get_arg(CLI_HUME_UUID)}", durable=True)
    _consumer.consume(ConsumeParams(command_handler.incoming_command),
                      queue_params=_hume_queue_params)


def stop():
    """
    Stop the central broker client.
    """
    LOGGER.info("hint stop")
    _consumer.stop()
    _producer.stop()
