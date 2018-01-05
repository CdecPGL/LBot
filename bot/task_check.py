'''タスクの確認に関するクラスなど'''

import sys
from datetime import date, datetime, time, timedelta
from enum import Enum
from threading import Lock

from linebot.models import TextSendMessage

from . import line
from .message_commands import add_message_command_group
from .models import Task, TaskImportance, TaskJoinCheckJob
from .utilities import TIMEZONE_DEFAULT

# 明日のタスクリマインダーの時刻
TOMORROW_REMIND_TIME = time(hour=23, tzinfo=TIMEZONE_DEFAULT)
# 明日のタスク確認の時刻
TOMORROW_CHECK_TIME = time(hour=12, tzinfo=TIMEZONE_DEFAULT)
# もうすぐのタスクリマインダーと確認をどれくらい前に行うか
SOON_REMIND_AND_CHECK_BEFORE = timedelta(hours=1)


def convert_deadline_to_string(deadline):
    '''期限を時間分の文字列に変換'''
    deadline = deadline.astimezone(TIMEZONE_DEFAULT)
    return "{:02d}:{:02d}".format(deadline.hour, deadline.minute)


def get_tommorow_range():
    '''明日の日時範囲を取得する'''
    tommorow = date.today() + timedelta(days=1)
    start_datetime = datetime(
        tommorow.year, tommorow.month, tommorow.day, 0, 0, 0, tzinfo=TIMEZONE_DEFAULT)
    end_datetime = datetime(
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
        '''明日が期限の全てのタスクを通知(グループのみ)'''
        # リマインド時間前なら何もしない
        if not force and TOMORROW_REMIND_TIME < datetime.now(TIMEZONE_DEFAULT).timetz():
            return
        # 明日が期限でリマインドが終わってないタスクを探す
        target_task_set = Task.objects.filter(
            deadline__range=get_tommorow_range(), group__isnull=False, is_tomorrow_remind_finished=False)
        # タスクのリマインドを実行
        TaskChecker.__remind_tasks(
            target_task_set, "こんばんは。明日が期限のタスクは以下のとおりだよ。", "おやすみなさい:D")
        # リマインドしたタスクがあったらログに残す
        if target_task_set.exists():
            print("明日のタスク{}件のリマインドを実行。({})".format(
                target_task_set.count(), datetime.now(TIMEZONE_DEFAULT)))

    @staticmethod
    def __execute_tommorow_important_tasks_check(force):
        '''明日が期限の重要度高タスクを通知(グループのみ)'''
        # 確認時間前なら何もしない
        if not force and TOMORROW_CHECK_TIME < datetime.now(TIMEZONE_DEFAULT).timetz():
            return
        # 明日が期限の確認していない重要タスクを取得する
        taret_task_set = Task.objects.filter(deadline__range=get_tommorow_range(
        ), importance=TaskImportance.High.name, group__isnull=False, is_tomorrow_check_finished=False)
        # タスクの参加確認を実行
        TaskChecker.__check_tasks(
            taret_task_set, "こんにちは。\n重要なタスク「{}」が明日の{}からあるよ。", "こんにちは。明日が期限の重要なタスクは以下のとおりだよ。")
        # 確認したタスクがあったらログに残す
        if taret_task_set.exists():
            print("明日の重要タスク{}件の新たな参加確認を実行({})。".format(
                taret_task_set.count(), datetime.now(TIMEZONE_DEFAULT)))

    @staticmethod
    def __execute_soon_tasks_remind_and_check(force):
        '''もうすぐのタスクのリマインド(重要度中)とチェック(重要度高)(グループのみ)'''
        # 期限もうすぐの重要度中でリマインド終わってないタスクを取得する
        target_remind_task_set = Task.objects.filter(
            deadline__lte=datetime.now(TIMEZONE_DEFAULT) + SOON_REMIND_AND_CHECK_BEFORE, group__isnull=False, importance=TaskImportance.Middle.name, is_soon_check_finished=False)
        TaskChecker.__remind_tasks(
            target_remind_task_set, "やあ。期限が近づいてるタスクがあるよ。", "忘れないようにね:-)")
        # 期限もうすぐの重要度高でリマインド終わってないタスクを取得する
        target_check_task_set = Task.objects.filter(
            deadline__lte=datetime.now(TIMEZONE_DEFAULT) + SOON_REMIND_AND_CHECK_BEFORE, group__isnull=False, importance=TaskImportance.High.name, is_soon_check_finished=False)
        TaskChecker.__check_tasks(
            target_check_task_set, "おい。\n重要なタスク「{}」が{}からあるよ。", "はい。期限の近い重要なタスクがあるよ。")
        # リマインドや確認したものがあったらログに残す
        if target_remind_task_set.exists() and target_check_task_set.exists():
            print("もうすぐのタスク{}件のリマインドと重要タスク{}件の確認を実行。({})".format(target_remind_task_set.count(), target_check_task_set.count(),
                                                                 datetime.now(TIMEZONE_DEFAULT)))

    @staticmethod
    def __remind_tasks(target_task_set, start_messege, end_message):
        '''タスクのリマインドを行う'''
        # 対象タスクをグループごとにまとめる
        group_task_map = {}
        for task in target_task_set:
            group = task.group
            if group.line_group.group_id in group_task_map:
                group_task_map[group.line_group.group_id].append(task)
            else:
                group_task_map[group.line_group.group_id] = [task]

        for line_group_id, task_list in group_task_map.items():
            # 開始メッセージを送信
            line.api.push_message(
                line_group_id, TextSendMessage(text=start_messege))
            # タスク確認を送信
            mess = ""
            for task in task_list:
                mess += "■{}(期限: {})\n".format(task.name,
                                               convert_deadline_to_string(task.deadline))
                mess += "メンバー：{}\n".format(
                    "、".join([member.name for member in task.participants.all()]))
            mess = mess.rstrip("\n")
            line.api.push_message(
                line_group_id, TextSendMessage(text=mess))
            # 終了メッセージを送信
            line.api.push_message(
                line_group_id, TextSendMessage(text=end_message))

            # タスクをリマインド済みにする
            for task in task_list:
                task.is_tomorrow_remind_finished = True
                task.save()

    @staticmethod
    def __check_tasks(taret_task_set, start_messege_single, start_messege_alone_multi):
        '''タスクの参加確認を行う'''
        # 対象タスクをグループごとにまとめる
        group_task_map = {}
        for task in taret_task_set:
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
            important_task_check_job_list = []
            for task in task_list:
                try:
                    task_check_job = TaskJoinCheckJob.objects.get(task=task)
                except TaskJoinCheckJob.DoesNotExist:
                    # 空いている確認番号を探す
                    while TaskJoinCheckJob.objects.filter(check_number=check_number_count).exists():
                        check_number_count += 1
                    # タスク確認の登録(テストで期限を12時間後にする)
                    task_check_job = TaskJoinCheckJob.objects.create(
                        group=task.group, task=task, check_number=check_number_count, deadline=datetime.now() + timedelta(hours=12))
                important_task_check_job_list.append(task_check_job)
            # 確認番号で並び替え
            ordered_task_check_job_list = [task_check_job for task_check_job in sorted(
                important_task_check_job_list, key=lambda task_check_job: task_check_job.check_number)]

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

            # タスクを確認済みにする
            for task in task_list:
                task.is_tomorrow_check_finished = True
                task.save()

            # タスク参加確認を開始
            add_message_command_group(group, "タスク参加確認")
