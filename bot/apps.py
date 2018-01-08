from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

# タスクの確認間隔
TASK_CHECK_INTERVAL = (0, 1)


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        '''アプリ起動時の処理'''
        super(BotConfig, self).ready()
        # modelsのインポートはdjangoの初期化前に行えないので個々で行う
        from .task_check import TaskChecker, TaskCheckType

        def task_check_job():
            '''明日のタスクのリマインドや確認を行うジョブ'''
            TaskChecker.execute(TaskCheckType.All)

        scheduler = BackgroundScheduler()

        # タスクの事前確認(10分おきに確認)
        scheduler.add_job(task_check_job, "interval",
                          hours=TASK_CHECK_INTERVAL[0], minutes=TASK_CHECK_INTERVAL[1])

        scheduler.start()
