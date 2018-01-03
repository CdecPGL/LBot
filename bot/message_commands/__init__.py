'''Message_commandsパッケージ初期化'''

from . import message_command, standard_commands, check_task_commands
from .message_command import execute_message_command, CommandSource

message_command.register_command_groups()
