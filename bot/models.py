from enum import Enum

from django.db import models

from bot.authorities import UserAuthority

# Create your models here.


class TaskImportance(Enum):
    '''タスクの重要度'''
    High = "高"
    Middle = "中"
    Low = "低"


def get_choices_from_enum(source_enum):
    '''列挙体から選択肢を取得'''
    return [(item.name, item.name) for item in source_enum]


class Vocabulary(models.Model):
    '''ボキャブラリデータベース'''
    # 単語
    word = models.CharField(max_length=64, unique=True)


class LineUser(models.Model):
    '''LINEのユーザーデータベース'''
    # UserID。LINEから取得
    user_id = models.CharField(max_length=64, null=True, unique=True)
    # UserName。LINEから取得
    name = models.CharField(max_length=64, null=True)


class AsanaUser(models.Model):
    '''Asanaのユーザーデータベース'''
    pass


class User(models.Model):
    '''ユーザーデータベース'''
    # ユーザー名。そのユーザー自身のみ設定可能
    name = models.CharField(max_length=64, unique=True)
    # LINEのユーザー情報。そのユーザーのみ設定可能
    line_user = models.OneToOneField(
        LineUser, on_delete=models.SET_NULL, null=True)
    # Asanaのユーザー情報。そのユーザーのみ設定可能
    asana_user = models.OneToOneField(
        AsanaUser, on_delete=models.SET_NULL, null=True)
    # 権限。Masterユーザーのみ変更可能
    authority = models.CharField(
        max_length=16, choices=get_choices_from_enum(UserAuthority))
    # 有効なメッセージコマンドグループ。カンマ区切りで複数指定
    valid_message_command_groups = models.CharField(max_length=256, default="")


class LineGroup(models.Model):
    '''LINEのグループデータベース'''
    # グループID。LINEから取得
    group_id = models.CharField(max_length=64, null=True, unique=True)


class AsanaTeam(models.Model):
    '''Asanaのチームデータベース'''
    pass


class Group(models.Model):
    '''グループデータベース'''
    # グループ名。グループ管理者のみ変更可能
    name = models.CharField(max_length=64, unique=True)
    # 管理者。グループ管理者のみ変更可能
    managers = models.ManyToManyField(User, related_name="managing_groups")
    # メンバー。グループ管理者のみ変更可能
    members = models.ManyToManyField(User, related_name="belonging_groups")
    # LINEグループ。グループ管理者のみ変更可能
    line_group = models.OneToOneField(
        LineGroup, on_delete=models.SET_NULL, null=True)
    # AsanaTeam。グループ管理者のみ変更可能
    asana_team = models.OneToOneField(
        AsanaTeam, on_delete=models.SET_NULL, null=True)
    # 有効なメッセージコマンドグループ。カンマ区切りで複数指定
    valid_message_command_groups = models.CharField(max_length=256, default="")


class AsanaTask(models.Model):
    '''Asanaのタスクデータベース'''
    pass


class Task(models.Model):
    '''タスクデーターベース'''
    # タスク名。タスク作成時に設定。タスク管理者のみ変更可能
    name = models.CharField(max_length=64, unique=True)
    # タスクの短縮名。タスクマスターのみ変更可能
    short_name = models.CharField(max_length=64, unique=True, null=True)
    # 締め切り。タスク作成時に設定。タスクマスターのみ変更可能
    deadline = models.DateTimeField()
    # 重要度
    importance = models.CharField(max_length=16, choices=get_choices_from_enum(
        TaskImportance), default=TaskImportance.Middle.name)
    # タスクの管理者。タスク管理者のみ変更可能
    managers = models.ManyToManyField(User, related_name="managing_tasks")
    # タスクの参加者。タスク管理者のみ変更可能
    participants = models.ManyToManyField(User, related_name="belonging_tasks")
    # タスクの参加グループ。タスク管理者のみ変更可能
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, related_name="tasks", null=True)
    # Asanaタスク。タスク管理者のみ変更可能
    asana_task = models.OneToOneField(
        AsanaTask, on_delete=models.SET_NULL, null=True)
    # 参加可能者
    joinable_members = models.ManyToManyField(
        User, related_name="joinable_tasks")
    # 欠席者
    absent_members = models.ManyToManyField(User, related_name="absent_tasks")
    # 明日のタスク確認が終わったかどうか(リマインド含む)
    is_tomorrow_check_finished = models.BooleanField(default=False)
    # もうすぐのタスク確認が終わったかどうか(リマインド含む)
    is_soon_check_finished = models.BooleanField(default=False)


class TaskJoinCheckJob(models.Model):
    '''タスクの参加チェックジョブデータベース'''
    # 対象のグループ
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="task_checks")
    # 対象のタスク
    task = models.OneToOneField(Task, on_delete=models.CASCADE, unique=True)
    # 確認が取れたユーザー
    checked_users = models.ManyToManyField(
        User, related_name="checked_task_join_check_job")
    # グループ内でのタスクチェック番号
    check_number = models.PositiveIntegerField()
    # チェックの期限
    deadline = models.DateTimeField()
