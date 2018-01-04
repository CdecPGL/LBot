'''Message_commandsパッケージ初期化'''

from . import message_command, standard_commands, check_task_commands
from .message_command import execute_message_command, CommandSource, add_message_command_group, remove_message_command_group

message_command.register_command_groups()
