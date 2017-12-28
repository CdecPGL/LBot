'''LINE関連のAPI'''

import linebot

ACCESS_TOKEN = 'CPkNadsUhm1VSLYWCq0dZEe9tXvmFlF55rTupLg/RScH2q5g3ya7datka0XpFKku+dUiYr28p0WHXJQUUNoZN/gYYvb+0dvWxJzUFO4rWJgo1+b9N7q6v9j7r2PFTcOWIVGteTkg/WFVP/tS1Xb6RQdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = "85a6ab89a82e466e7d1f34dad95dd007"

api = linebot.LineBotApi(ACCESS_TOKEN)
handler = linebot.WebhookHandler(CHANNEL_SECRET)
