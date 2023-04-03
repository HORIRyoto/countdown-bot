from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction, PostbackEvent
)
from flask_sqlalchemy import SQLAlchemy
from time import sleep
from datetime import datetime, time
import schedule
import os

from dotenv import load_dotenv
# .envファイルの内容を読み込む
load_dotenv()


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)


# DBを定義
class DB(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100))
    event_datetime = db.Column(db.DateTime)
    send_time = db.Column(db.Time)
    # , nullable=False

with app.app_context():
    db.create_all()

    # とりあえず仮のデータを入れる
    event_datetime = datetime(2023, 2, 7, 18, 45, 0)
    send_time = time(6, 0, 0)
    db.session.add(DB(event_name="送別会", event_datetime=event_datetime, send_time=send_time))
    db.session.commit()
    # db.sqliteのファイルがない状態で実行したとき、上記のデータが格納されたSQLiteのファイルができてたら成功

# # ちゃんと取り出せるかテストprint
# with app.app_context():
#     results = DB.query.all()
#     print(results)
#     for result in results:
#         print(result.event_name, result.event_datetime, result.send_time)


CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
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

    global user_id
    user_id = event.source.user_id

    event_name = event.message.text #受け取ったテキストメッセージを取得
    print(event_name)
    db.session.add(DB(event_name=event_name)) # DBに格納
    db.session.commit()
    
    # 同じレコードにデータをいれるため、この後使うidを定義する
    results = DB.query.all() # リスト型で取り出されるので
    result = results[-1] # リストの最後尾(最新のデータ)を指定
    global id
    id = result.id
    print(id)

    # 日時選択アクションを定義
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%dT%H:%M")  # フォーマットを指定して現在の日時を取得

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
                    initial=current_time,
                    min='2023-01-01T00:00',
                    max='2030-12-31T23:59'
                )
            ]
        )
    )
    # 予定の日時を聞くメッセージを送信
    line_bot_api.reply_message(
        event.reply_token,
        message
    )


@handler.add(PostbackEvent) #PostbackEventが発生したとき
def handle_postback(event):
    data = event.postback.data

    if data == 'event_datetime': #予定の日時に対する回答だった場合
        selected_datetime = event.postback.params['datetime'] #ユーザーが選択した日時の値を取得
        print('user-select-event-datetime')
        print(selected_datetime)

        # DBのdatetime型に格納するために、LINEのdatetime型からPythonのdatetime型に変更する
        selected_datetime = datetime.strptime(selected_datetime, '%Y-%m-%dT%H:%M')
        print(selected_datetime)

        # idを指定して同じレコードのカラムにデータを保存する
        record = db.session.query(DB).get(id)
        record.event_datetime = selected_datetime
        db.session.commit()

        # 時間選択アクションを定義
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

        # DBのtime型に格納するために、LINEのtime型からPythonのtime型に変更する
        dt_str = selected_send_time + ':00'
        dt_obj = datetime.strptime(dt_str, '%H:%M:%S')
        selected_send_time = dt_obj.time()
        print(selected_send_time)

        # idを指定して同じレコードのカラムにデータを保存する
        record = db.session.query(DB).get(id)
        record.send_time = selected_send_time
        db.session.commit()

        #確認のメッセージを送信
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{selected_send_time}に設定しました"))


        data_list = db.session.query(DB).get(id)
        event_name = data_list.event_name
        event_datetime = data_list.event_datetime.strftime('%Y-%m-%d %H:%M')  # 秒を含めない形式
        send_time = data_list.send_time.strftime('%H:%M')  # 秒を含めない形式
        print(event_datetime, event_name, send_time)  # 2023-02-06 10:00:00 event_name 07:00:00


        # ここにscheduleモジュールを使って、カウントダウンを行う＆メッセージを送る処理を実装していく


if __name__ == "__main__":
    # port = int(os.getenv("PORT"))
    app.run(host="localhost", port=8000)
