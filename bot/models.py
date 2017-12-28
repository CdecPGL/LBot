from django.db import models

# Create your models here.


class Vocabulary(models.Model):
    '''ボキャブラリデータベース'''
    # 単語
    word = models.CharField(max_length=64, unique=True)


class User(models.Model):
    '''ユーザーデータベース'''
    AUTHORITY_CHOICES = (
        ("Master", "Master"),
        ("Editor", "Editor"),
        ("Watcher", "Watcher"),
    )
    # ユーザーID。LINEから取得
    user_id = models.CharField(max_length=64, unique=True)
    # ユーザー名。LINEから取得
    name = models.CharField(max_length=64)
    # ニックネーム。そのユーザー自身のみ設定可能
    nickname = models.CharField(max_length=64, null=True)
    # 権限。Masterユーザーのみ変更可能
    authority = models.CharField(max_length=64, choices=AUTHORITY_CHOICES)


class Group(models.Model):
    '''グループデータベース'''
    # グループID。LINEから取得
    group_id = models.CharField(max_length=64, unique=True)
    # グループ名。LINEから取得
    name = models.CharField(max_length=64)


class Task(models.Model):
    '''タスクデーターベース'''
    # タスク名。タスク作成時に設定。タスクマスターのみ変更可能
    name = models.CharField(max_length=64, unique=True)
    # タスクの短縮名。タスクマスターのみ変更可能
    short_name = models.CharField(max_length=64, unique=True, null=True)
    # 締め切り。タスク作成時に設定。タスクマスターのみ変更可能
    deadline = models.DateTimeField()
    # タスクの管理者。管理者のみ変更可能
    managers = models.ManyToManyField(User, related_name="managers")
    # タスクの参加者。管理者のみ変更可能
    user_participants = models.ManyToManyField(User, related_name="user_participants")
    # タスクの参加グループ。管理者のみ変更可能
    group_participants = models.ManyToManyField(Group)
