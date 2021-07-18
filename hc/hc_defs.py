"""
Definitions for the Device Controller.
"""


#
# CLI args
#
CLI_HUME_UUID = "hume_uuid"
CLI_HINT_IP_ADDRESS = "hint_ip_address"
CLI_HINT_PORT = "hint_port"
CLI_BROKER_IP_ADDRESS = "broker_ip_address"
CLI_BROKER_PORT = "broker_port"


#
# Message types
#
class MessageType:
    DISCOVER_DEVICES = 0
    CONFIRM_ATTACH = 1
    DETACH = 2
