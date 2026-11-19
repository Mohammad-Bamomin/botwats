import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ====== حط مفاتيحك هنا ======
ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID")
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ====== قراءة بيانات المحل ======
def load_shop_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "محل في تريم، حضرموت"

SHOP_DATA = load_shop_data()

# ====== دالة إرسال رسالة واتساب ======
def send_whatsapp(to, message):
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    requests.post(url, data=payload)
    print(f"تم الإرسال إلى {to}: {message}")

# ====== دالة الذكاء الاصطناعي ======
def get_ai_reply(user_message, sender_name="زبون"):
    prompt = f"""
أنت موظف خدمة عملاء في محل في تريم، حضرموت. اسمك "مساعد تريم".
تتكلم باللهجة الحضرمية، بأسلوب محترم ومختصر وودود.

بيانات المحل:
{SHOP_DATA}

قواعد مهمة:
1. رد فقط من بيانات المحل. إذا سألك عن شي مو موجود، قل "ما عندي معلومة أكيدة، بخلي صاحب المحل يتواصل معك".
2. إذا الزبون يبغى يطلب، اسأله: الاسم، الموقع في تريم، الطلب بالضبط، وكمية.
3. لا تخترع أسعار ولا مواعيد.
4. إذا الزبون قال "سلام" أو "هلا"، رد عليه بترحيب.

رسالة الزبون: {user_message}
ردك:
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # رخيص وسريع وممتاز للبوت
        messages=[
            {"role": "system", "content": "أنت مساعد واتساب لمحل في تريم."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content

# ====== استقبال رسائل واتساب ======
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("وصلت رسالة:", data)

    try:
        # UltraMsg يرسل البيانات بهذا الشكل
        msg_data = data.get('data', {})
        user_message = msg_data.get('body', '')
        sender = msg_data.get('from', '')
        is_from_me = msg_data.get('fromMe', False)

        # تجاهل رسائلي أنا عشان ما يرد على نفسه
        if is_from_me or not user_message:
            return jsonify({"status": "ignored"}), 200

        print(f"رسالة من {sender}: {user_message}")

        # جيب الرد من الذكاء الاصطناعي
        reply = get_ai_reply(user_message)
        
        # أرسل الرد
        send_whatsapp(sender, reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("خطأ:", e)
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/')
def home():
    return "بوت تريم شغال! 🔥"

if __name__ == '__main__':
    app.run(port=5000, debug=True)