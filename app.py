from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction, PostbackEvent
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)

class DB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    event_datetime = db.Column(db.DateTime, nullable=False)
    send_time = db.Column(db.Time, nullable=False)
    #ユーザーを識別するためのLINEのユーザー情報も必要だと思われ

with app.app_context():
    db.create_all()

    # とりあえず仮のデータを入れる
    event_datetime = datetime(2023, 2, 7, 18, 45, 0)
    send_time = time(6, 0, 0)
    db.session.add(DB(event_name="送別会", event_datetime=event_datetime, send_time=send_time))
    db.session.commit()
    # db.sqliteのファイルがない状態で実行したとき、上記のデータが格納されたSQLiteのファイルができてたら成功

# ちゃんと取り出せるかテストprint
with app.app_context():
    results = DB.query.all()
    print(results)
    for result in results:
        print(result.event_name, result.event_datetime, result.send_time)


CHANNEL_ACCESS_TOKEN = "MWItH/5GyF/l9wg8M5fVY8HCOXTK6ojEhmQQWa6m3JX5lWntShvFS5Eu1ihMKECdyOedX6AhzLMjUSVuAqLOVr/XnndAxyNs2C/ldWdEqQEW3yylHTOQmeKwwHMqnGGJmd9hPtZnYVBD7P0vAPNwqgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "40fe315ab82434c0e2187ab9a5bb8cba"
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/", methods=['GET'])
def hello_world():
   return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    # get x-line-signature header value
    signature = request.headers['x-line-signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage) #ユーザーからテキストメッセージを受け取ったとき
def handle_message(event):

    event_name = event.message.text #受け取ったテキストメッセージを取得
    print(event_name)

    #日時選択アクションを定義
    message = TemplateSendMessage(
        alt_text="予定日時",
        template=ButtonsTemplate(
            text="イベントの予定日時を教えてください",
            title="イベントの予定日時",
            image_size="cover",
            thumbnail_image_url="https://3.bp.blogspot.com/-dqoq-nN83NM/W1vg19r9wlI/AAAAAAABNrw/IP2DyyofvHgh8Z1weiHaVYZlPkplfZ3hACLcBGAs/s800/animal_chara_computer_inu.png",
            actions=[
                DatetimePickerTemplateAction(
                    label='Select date and time',
                    data='event_datetime',
                    mode='datetime',
                    initial='2023-02-06T10:00',
                    min='2022-01-01T00:00',
                    max='2026-12-31T23:59'
                )
            ]
        )
    )
    #予定の日時を聞くメッセージを送信
    line_bot_api.reply_message(
        event.reply_token,
        message
    )
    # return event_name


@handler.add(PostbackEvent) #PostbackEventが発生したとき
def handle_postback(event):
    data = event.postback.data 

    if data == 'event_datetime': #予定の日時に対する回答だった場合
        selected_datetime = event.postback.params['datetime'] #ユーザーが選択した日時の値を取得
        print(selected_datetime)

        #時間選択アクションを定義
        message = TemplateSendMessage(
		alt_text="アラーム",
		template=ButtonsTemplate(
			text="カウントダウンの通知を受け取る時間を設定してください",
			title="通知時間を設定",
			actions=[
				DatetimePickerTemplateAction(
					label='time_select',
					data='send_time',
					mode='time',
					initial='06:00',
					min='00:00',
					max='23:59'
				    )
	    		]
		    )
	    )
        #確認のメッセージと通知時刻を聞くメッセージを送信
        messages = [TextSendMessage(text=f"{selected_datetime}に設定しました。"), message]
        line_bot_api.reply_message(
            event.reply_token,
            messages
        ) 

    elif data == 'send_time': #通知時間に対する回答だった場合
        selected_send_time = event.postback.params['time'] #ユーザーが選択した通知時間の値を取得
        print(selected_send_time)

        #確認のメッセージを送信
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{selected_send_time}に設定しました"))


if __name__ == "__main__":
    app.run(host="localhost", port=8000)