'''タスクの確認に関するクラスなど'''

import datetime
import sys
from enum import Enum
from threading import Thread, Lock

from linebot.models import TextSendMessage

from . import line
from .message_commands import add_message_command_group
from .models import Task, TaskImportance, TaskJoinCheckJob
from .utilities import TIMEZONE_DEFAULT

# 明日のタスクリマインダーの時刻
TOMORROW_REMIND_TIME = (23, 0)
# 明日のタスク確認の時刻
TOMORROW_CHECK_TIME = (12, 0)
# もうすぐのタスクリマインダーと確認をどれくらい前に行うか
SOON_REMIND_AND_CHECK_BEFORE = (1, 0)


def convert_deadline_to_string(deadline):
    '''期限を時間分の文字列に変換'''
    deadline = deadline.astimezone(TIMEZONE_DEFAULT)
    return "{:02d}:{:02d}".format(deadline.hour, deadline.minute)


def get_tommorow_range():
    '''明日の日時範囲を取得する'''
    tommorow = datetime.date.today() + datetime.timedelta(days=1)
    start_datetime = datetime.datetime(
        tommorow.year, tommorow.month, tommorow.day, 0, 0, 0, tzinfo=TIMEZONE_DEFAULT)
    end_datetime = datetime.datetime(
        tommorow.year, tommorow.month, tommorow.day, 23, 59, 59, 999999, tzinfo=TIMEZONE_DEFAULT)
    return start_datetime, end_datetime


class TaskCheckType(Enum):
    '''タスクチェックのタイプ'''
    # 全リマインド及び確認
    All = "All"
    # 明日のタスクのリマインド
    TommorowTasksRemind = "TommorowTasksRemind"
    # 明日の重要タスクの確認
    TommorowImportantTasksCheck = "TommorowImportantTasksCheck"
    # タスクの事前確認とリマインド
    SoonTasksRemindAndCheck = "SoonTasksRemindAndCheck"


class TaskChecker(object):
    '''タスクの確認クラス'''
    __lock = Lock()

    def __init__(self):
        self.__handler_map = {
            TaskCheckType.All: TaskChecker.__execute_all,
            TaskCheckType.TommorowTasksRemind: TaskChecker.__execute_tommorow_tasks_remind,
            TaskCheckType.TommorowImportantTasksCheck: TaskChecker.__execute_tommorow_important_tasks_check,
            TaskCheckType.SoonTasksRemindAndCheck: TaskChecker.__execute_soon_tasks_remind_and_check,
        }

    def __execute(self, task_check_type, force):
        '''確認を実行'''
        self.__handler_map[task_check_type](force)

    @staticmethod
    def execute(task_check_type, force=False):
        '''確認を実行'''
        # Djangoの複数プロセスから同時に呼ばれた場合に同じ処理が複数回行われることを防ぐため、スレッドロックを行う
        with TaskChecker.__lock:
            TaskChecker().__execute(task_check_type, force)

    @classmethod
    def __execute_all(cls, force):
        '''全てのタスクを行う'''
        cls.__execute_tommorow_tasks_remind(force)
        cls.__execute_tommorow_important_tasks_check(force)
        cls.__execute_soon_tasks_remind_and_check(force)

    @staticmethod
    def __execute_tommorow_tasks_remind(force):
        '''明日が期限のタスクを通知'''
        print("明日のタスク通知を実行({})".format(datetime.datetime.now(TIMEZONE_DEFAULT)))
        group_task_map = {}
        for task in Task.objects.filter(deadline__range=get_tommorow_range()):
            group = task.group
            if group.line_group.group_id in group_task_map:
                group_task_map[group.line_group.group_id].append(task)
            else:
                group_task_map[group.line_group.group_id] = [task]

        for line_group_id, task_list in group_task_map.items():
            mess = "こんばんは。明日が期限のタスクは以下のとおりだよ。"
            line.api.push_message(
                line_group_id, TextSendMessage(text=mess))
            mess = "\n".join(
                ["■{}(期限: {})".format(task.name, convert_deadline_to_string(task.deadline)) for task in task_list])
            line.api.push_message(
                line_group_id, TextSendMessage(text=mess))
            mess = "おやすみなさい:D"
            line.api.push_message(
                line_group_id, TextSendMessage(text=mess))

    @staticmethod
    def __execute_tommorow_important_tasks_check(force):
        '''明日が期限の重要タスクを通知(グループのみ)'''
        print("明日の重要タスク参加確認を実行({})".format(
            datetime.datetime.now(TIMEZONE_DEFAULT)))
        # 明日が期限の重要タスクを取得しグループごとにまとめる
        group_task_map = {}
        for task in Task.objects.filter(deadline__range=get_tommorow_range(), importance=TaskImportance.High.name, group__isnull=False):
            group = task.group
            if group.line_group.group_id in group_task_map:
                group_task_map[group.line_group.group_id].append(task)
            else:
                group_task_map[group.line_group.group_id] = [task]

        # グループごとに通知
        for line_group_id, task_list in group_task_map.items():
            group = line.utilities.get_group_by_line_group_id_from_database(
                line_group_id)
            # 確認タスクを追加
            check_number_count = 1
            for task in task_list:
                # すでに登録されていたら飛ばす
                if not TaskJoinCheckJob.objects.filter(task=task).exists():
                    # 空いている確認番号を探す
                    while TaskJoinCheckJob.objects.filter(check_number=check_number_count).exists():
                        check_number_count += 1
                    # タスク確認の登録(テストで期限を12時間後にする)
                    TaskJoinCheckJob.objects.create(
                        group=task.group, task=task, check_number=check_number_count, deadline=datetime.datetime.now() + datetime.timedelta(hours=12))

            # 確認タスク一覧を作成
            important_task_check_job_list = TaskJoinCheckJob.objects.filter(
                group=group, task__importance=TaskImportance.High.name)
            # 確認タスクがなかったらエラー
            if not important_task_check_job_list.exists():
                sys.stderr.write(
                    "グループ「{}」で存在するべきタスク確認ジョブが存在しません。".format(group.name))
                continue
            # 確認番号で並び替え
            ordered_task_check_job_list = [task_check_job for task_check_job in sorted(
                important_task_check_job_list.all(), key=lambda task_check_job: task_check_job.check_number)]

            # 通知
            if len(ordered_task_check_job_list) == 1:
                task_check_job = ordered_task_check_job_list[0]
                task = task_check_job.task
                mess = "こんにちは。\n重要なタスク「{}」が明日の{}からあるよ。".format(
                    task.name, convert_deadline_to_string(task.deadline))
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "メンバーの{}はこのタスクに参加できる？".format(
                    "".join(["「{}」".format(member.name) for member in task.participants.all()]))
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "参加できるなら「#できる」、できないなら「#できない」と答えてね。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
            else:
                mess = "こんにちは。明日が期限の重要なタスクは以下のとおりだよ。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                # タスク一覧を作成
                mess = ""
                for task_check_job in ordered_task_check_job_list:
                    mess += "{}. {}(期限: {})\n".format(task_check_job.check_number, task_check_job.task.name,
                                                      convert_deadline_to_string(task_check_job.task.deadline))
                    mess += "メンバー：{}\n".format(
                        "、".join([member.name for member in task_check_job.task.participants.all()]))
                mess = mess.rstrip("\n")
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "これらのタスクに参加できるかできないか答えてね。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "例えば、1番のタスクに参加できて2番はできない場合は\n======\n#できる\n1\n======\n#できない\n2\n======\nのように答えてね。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))

            # タスク参加確認を開始
            add_message_command_group(group, "タスク参加確認")

    @staticmethod
    def __execute_soon_tasks_remind_and_check(force):
        '''もうすぐのタスクのリマインドとチェック'''
        print("もうすぐのタスク確認を実行({})".format(
            datetime.datetime.now(TIMEZONE_DEFAULT)))
