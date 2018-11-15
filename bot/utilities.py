from enum import Enum


class TaskImportance(Enum):
    '''タスクの重要度'''
    High = "高"
    Middle = "中"
    Low = "低"


class ServiceGroupKind(Enum):
    '''サービスグループの種類'''
    LINEGroup = "LINEGroup"
    DiscordServer = "DiscordServer"
    DiscordChannel = "DiscordChannel"
    AsanaTeam = "AsanaTeam"

class ServiceUserKind(Enum):
    '''サービスユーザーの種類'''
    LINEUser = "LINEUser"
    DiscordUser = "DiscordUser"
    AsanaUser = "AsanaUser"


def get_choices_from_enum(source_enum):
    '''列挙体から選択肢を取得'''
    return [(item.name, item.name) for item in source_enum]
