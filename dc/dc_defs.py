"""
Definitions for the Device Controller.
"""


#
# CLI args
#
CLI_HUME_UUID = "hume_uuid"


#
# Message types
#
class MessageType:
    DISCOVER_DEVICES = 0
    CONFIRM_ATTACH = 1
    DETACH = 2
