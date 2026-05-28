from flask import Flask, request

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import requests
import os

app = Flask(__name__)

configuration = Configuration(
    access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("LINE_CHANNEL_SECRET")
)

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook Error:", e)
        return "Error", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    if not user_text:
        return

    # 中文 → 英文
    if any('\u4e00' <= c <= '\u9fff' for c in user_text):
        target_lang = "EN"

    # 英文 → 中文
    elif user_text.isascii():
        target_lang = "ZH"

    else:
        return

    try:
        response = requests.post(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": DEEPL_API_KEY,
                "text": user_text,
                "target_lang": target_lang
            },
            timeout=10
        )

        data = response.json()

        print(data)

        translated = data["translations"][0]["text"]

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=translated)
                    ]
                )
            )

    except Exception as e:
        print("Translation Error:", e)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
