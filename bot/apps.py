from django.apps import AppConfig


from apscheduler.schedulers.background import BackgroundScheduler

def test_job():
    print("testsetsetsets")

class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        '''アプリ起動時の処理'''
        print("初期化。")
        scheduler = BackgroundScheduler()
        scheduler.add_job(test_job, "interval", minutes=1)
        scheduler.start()

