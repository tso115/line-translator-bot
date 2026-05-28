from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from openai import OpenAI
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    prompt = f"""
你是一個專業雙向翻譯員。

規則：
1. 英文翻譯成繁體中文
2. 中文翻譯成英文
3. 其他語言不要翻譯
4. 保留專有名詞、型號、品牌名稱
5. 只輸出翻譯結果
6. 如果不需要翻譯，直接原樣輸出

內容：
{user_text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    translated = response.choices[0].message.content.strip()

    if translated != user_text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=translated)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
