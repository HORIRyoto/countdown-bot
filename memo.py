
#ーーーーーメッセージ（予定）を受け取ったとき（カウントダウン設定の流れ）ーーーーー＃
# ・DBに予定名を格納
# ・予定の日時を聞く日時選択アクションを起こす
# ・受け取った日時をDBに格納
# ・何時に通知を送るか聞く時間選択アクションを起こす
# ・受け取った時刻をDBに格納


#ーーーーーカウントダウン通知を行う処理の案ーーーーー#

# 予定名・予定日時・通知時刻をDBから取り出して定義する
event_name = event_name
event_datetime = event_datetime
send_time = send_time

while True:
    now = datetime.datetime.now() #現在の日時を取得

    # 目標日時を達成しているか確認
    if now >= event_datetime:
        break

    # メッセージを送信する時間かどうかを確認
    if now.time() == send_time:
        A = event_datetime - now #現在の時刻と目標時刻の差分を出す
        days = A.day
        message = f"{event_name}まであと{days}日"

        #メッセージを送信する処理を追加、イベント当日用のメッセージも追加したい

        time.sleep(24 * 60 * 60) #次に時間を確認するまで24時間待つ（微調整必要）
    else:
        time.sleep(1) #次に時間を確認するまで1秒待つ