import os,time,json


# 引入flask模組
from flask import Flask, request, abort

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate(os.path.join(os.getcwd(),'secret','firebase.json'))
firebase_admin.initialize_app(cred)

db = firestore.client()




# 引入linebot相關模組
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

# 處理器請參閱以下網址的 Message objects 章節
# https://github.com/line/line-bot-sdk-python
from linebot.models import (
    MessageEvent, PostbackEvent, TextMessage, StickerMessage, TextSendMessage, StickerSendMessage, FlexSendMessage, LocationSendMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageAction, URIAction, CarouselTemplate, CarouselColumn
)



from brainFuckInterpreter import BrainF,text2bf2,text2bf3,text2bf
from brainFuckInterpreter.translation import TEXT






app = Flask(__name__)

if app.env=='development':
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.getcwd(),'.env'),override=True)

# LINE的Webhook為了辨識開發者身份所需的資料
# 相關訊息進入網址(https://developers.line.me/console/)
line_secret=json.load(open(os.path.join(os.getcwd(),'secret','line.json')))
CHANNEL_ACCESS_TOKEN = line_secret['channel_access_token']
CHANNEL_SECRET = line_secret['channel_secret']

# *********** 以下為 X-LINE-SIGNATURE 驗證程序 ***********
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/", methods=['POST'])
def callback():
    # 當LINE發送訊息給機器人時，從header取得 X-Line-Signature
    # X-Line-Signature 用於驗證頻道是否合法
    signature = request.headers['X-Line-Signature']

    # 將取得到的body內容轉換為文字處理
    body = request.get_data(as_text=True)

    # 一但驗證合法後，將body內容傳至handler
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('[X-Line-Signature 驗證失敗]')
        abort(400)

    return 'OK'
@app.route('/',methods=('GET',))
def index():
    return 'OK',200
# *********** 以上為 X-LINE-SIGNATURE 驗證程序 ***********


# 文字訊息傳入時的處理器
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 當有文字訊息傳入時
    # event.message.text : 使用者輸入的訊息內容
    print('*'*40)
    print('[使用者傳入文字訊息]')
    print(str(event))
    # 使用者說的文字
    user_msg = event.message.text
    # 準備要回傳的文字訊息
    reply=None

    user_doc=db.document(f'users_session/{event.source.user_id}').get()
    user={
        'status':None
    }
    if user_doc.exists:
        user.update(user_doc.to_dict())
    if user['status']:
        if user['status']=='encrypt':
            reply=TextSendMessage(
                text=text2bf3(user_msg)
            )
            user['status']=None
        elif user['status']=='decrypt':
            reply = TextSendMessage(
                text=BrainF(code=user_msg, print_memory=False).run()
            )
            user['status'] = None
    else:
        if user_msg.split()[0].lower()=='encrypt':
            reply=TextSendMessage(
                text=text2bf3(" ".join(user_msg.split()[1::]))
            )
        elif user_msg.split()[0].lower()=='decrypt':
            reply = TextSendMessage(
                text=BrainF(code=" ".join(user_msg.split()[1::]),print_memory=False).run()
            )
        elif user_msg.split()[0].lower().find('學測')!=-1:
            reply=TextSendMessage(
                text=TEXT
            )
        elif user_msg.find('余') != -1:
            reply = TextSendMessage(text=f'余才不知道大人在說什麼呢')
        else:
            flex_dict=json.load(open(os.path.join(os.getcwd(),'templates','card.json')))
            reply = FlexSendMessage(
                alt_text="flex message",
                contents=flex_dict
            )
            # pass

    db.collection('users_session').document(event.source.user_id).set(user)


    # 回傳訊息
    if reply:
        line_bot_api.reply_message(
            event.reply_token,
            reply
        )


@handler.add(PostbackEvent)
def postback(event):
    print(event)
    reply=None
    user={
        'status':None
    }
    if event.postback.data=="encrypt":
        reply='plz enter text'
        user['status']='encrypt'
    elif event.postback.data=="decrypt":
        reply="plz enter bf code"
        user['status'] = 'decrypt'

    db.collection('users_session').document(event.source.user_id).set(user)


    if reply:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply
            )
        )

# # 貼圖訊息傳入時的處理器
# @handler.add(MessageEvent, message=StickerMessage)
# def handle_sticker_message(event):
#     # 當有貼圖訊息傳入時
#     print('*'*40)
#     print('[使用者傳入貼圖訊息]')
#     print(str(event))
#
#     # 準備要回傳的貼圖訊息
#     # TODO: 機器人可用的貼圖 https://devdocs.line.me/files/sticker_list.pdf
#     reply = StickerSendMessage(package_id='2', sticker_id='149')
#
#     # 回傳訊息
#     line_bot_api.reply_message(
#         event.reply_token,
#         reply)




if __name__ == "__main__":
    print('[伺服器開始運行]')
    port = int(os.environ.get('PORT', 5500))
    # 使app開始在此連接端口上運行
    print('[Flask運行於連接端口:{}]'.format(port))
    # 本機測試使用127.0.0.1, debug=True
    # Heroku部署使用 0.0.0.0
    app.run(port=port)
