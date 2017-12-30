'''データベース関連のユーティリティ'''

from bot.models import User, Group, Task
from bot.exceptions import UserNotFoundError, GroupNotFoundError, TaskNotFoundError


def get_user_by_name_from_database(name: str)->User:
    '''ユーザ名でデータベースからユーザーを取得する'''
    try:
        return User.objects.get(name__exact=name)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(名前: {})が見つかりませんでした。".format(name))


def get_group_by_name_from_database(name: str)->Group:
    '''グループ名でデータベースからユーザーを取得する'''
    try:
        return Group.objects.get(name__exact=name)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            "グループ(名前: {})が見つかりませんでした。".format(name))


def get_task_by_name_or_shot_name_from_database(name: str)->Group:
    '''タスクを名前か短縮名で取得する。検索には名前が優先される'''
    try:
        return Task.objects.get(name__exact=name)
    except Task.DoesNotExist:
        try:
            return Task.objects.get(short_name__exact=name)
        except Task.DoesNotExist:
            raise TaskNotFoundError("タスク(名前又は短縮名：{})が見つかりませんでした。".format(name))
