from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

# タスクの確認間隔
TASK_CHECK_INTERVAL = (0, 10)


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        '''アプリ起動時の処理'''
        super(BotConfig, self).ready()
        # modelsのインポートはdjangoの初期化前に行えないので個々で行う
        from .task_check import TaskChecker, TaskCheckType
        from .utilities import TIMEZONE_DEFAULT

        def task_check_job():
            '''明日のタスクのリマインドや確認を行うジョブ'''
            TaskChecker.execute(TaskCheckType.All)

        scheduler = BackgroundScheduler()
        # # 明日のタスク確認(毎日23:00に確認)
        # tommorow_remind_datetime = datetime(
        #     2000, 1, 1, 23, tzinfo=TIMEZONE_DEFAULT).astimezone(timezone.utc)
        # scheduler.add_job(tommorow_tasks_remind_job, "cron", hour=tommorow_remind_datetime.hour,
        #            minute=tommorow_remind_datetime.minute)
        # # 明日の重要タスク確認(毎日12:00に確認)
        # tommorow_important_check_datetime = datetime(
        #     2000, 1, 1, 12, tzinfo=TIMEZONE_DEFAULT).astimezone(timezone.utc)
        # scheduler.add_job(tommorow_important_tasks_check_job, "cron", hour=tommorow_important_check_datetime.hour,
        #            minute=tommorow_important_check_datetime.minute)
        # タスクの事前確認(10分おきに確認)
        scheduler.add_job(task_check_job, "interval",
                          hour=TASK_CHECK_INTERVAL[0], minutes=TASK_CHECK_INTERVAL[1])

        scheduler.start()
