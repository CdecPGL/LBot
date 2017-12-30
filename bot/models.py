from django.db import models

from bot.authorities import UserAuthority

# Create your models here.


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
    AUTHORITY_CHOICES = (
        (UserAuthority.Master.name, UserAuthority.Master.name),
        (UserAuthority.Editor.name, UserAuthority.Editor.name),
        (UserAuthority.Watcher.name, UserAuthority.Watcher.name),
    )
    # ユーザー名。そのユーザー自身のみ設定可能
    name = models.CharField(max_length=64, unique=True)
    # LINEのユーザー情報。そのユーザーのみ設定可能
    line_user = models.OneToOneField(
        LineUser, on_delete=models.SET_NULL, null=True)
    # Asanaのユーザー情報。そのユーザーのみ設定可能
    asana_user = models.OneToOneField(
        AsanaUser, on_delete=models.SET_NULL, null=True)
    # 権限。Masterユーザーのみ変更可能
    authority = models.CharField(max_length=16, choices=AUTHORITY_CHOICES)


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
    # タスクの管理者。タスク管理者のみ変更可能
    managers = models.ManyToManyField(User, related_name="managing_tasks")
    # タスクの参加者。タスク管理者のみ変更可能
    participants = models.ManyToManyField(User, related_name="belonging_tasks")
    # タスクの参加グループ。タスク管理者のみ変更可能
    groups = models.ManyToManyField(Group)
    # Asanaタスク。タスク管理者のみ変更可能
    asana_task = models.OneToOneField(
        AsanaTask, on_delete=models.SET_NULL, null=True)
    # グループメンバー全員参加かどうか
    is_participate_all_in_groups = models.BooleanField(default=False)
