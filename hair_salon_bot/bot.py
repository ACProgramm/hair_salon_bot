import logging, random, os, re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from intent_classifier import classify_intent
from utils import load_intents, load_dialogues, get_best_match
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('BOT_TOKEN', '7711301494:AAGjH01SEwdmU6PfrHgDzEjrewkzwDbR9cA')

intents = load_intents(os.path.join('dataset','intents.json'))
dialogues = load_dialogues('dialogues.txt')
ctx = defaultdict(lambda: {'stage':0})

services = {
    'стрижка': ['мужская', 'женская'],
    'укладка': ['вечерняя', 'повседневная'],
    'окрашивание': ['однотонное', 'сложное', 'омбре', 'балаяж', 'шатуш']
}

masters = [
    {
        'name': 'Начинающий барбер',
        'prices': {
            'стрижка': 1000,
            'мужская': 1000,
            'женская': 1100,
            'укладка': 1200,
            'вечерняя': 1300,
            'повседневная': 1200,
            'окрашивание': 1500,
            'омбре': 1800,
            'балаяж': 1900,
            'шатуш': 1700,
            'однотонное': 1400,
            'сложное': 2000
        }
    },
    {
        'name': 'Барбер',
        'prices': {
            'стрижка': 1500,
            'мужская': 1500,
            'женская': 1600,
            'укладка': 1700,
            'вечерняя': 1800,
            'повседневная': 1700,
            'окрашивание': 2000,
            'омбре': 2300,
            'балаяж': 2400,
            'шатуш': 2200,
            'однотонное': 1900,
            'сложное': 2600
        }
    },
    {
        'name': 'Старший барбер',
        'prices': {
            'стрижка': 2500,
            'мужская': 2500,
            'женская': 2600,
            'укладка': 2700,
            'вечерняя': 2800,
            'повседневная': 2700,
            'окрашивание': 3000,
            'омбре': 3300,
            'балаяж': 3400,
            'шатуш': 3200,
            'однотонное': 2900,
            'сложное': 3500
        }
    }
]


def start(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(intents['greeting']['responses']))
    ctx[update.effective_user.id] = {'stage':0}

def handle(update: Update, context: CallbackContext):
    msg = update.message.text.strip().lower()
    uid = update.effective_user.id
    data = ctx[uid]

    if any(word in msg for word in ['передумал', 'отмени', 'сначала', 'не хочу']):
        ctx[uid] = {'stage': 0}
        update.message.reply_text("Хорошо, если что — я здесь.")
        return

    # Stage 0
    if data['stage'] == 0:
        if any(kw in msg for kw in ['хочу', 'запис']):
            # immediate service+subcategory
            for svc, subs in services.items():
                if svc in msg:
                    for sub in subs:
                        if sub in msg:
                            data.update({'service': svc, 'subcategory': sub, 'stage': 3})
                            text = 'Выберите мастера:\n'
                            for i, m in enumerate(masters, 1):
                                text += f"{i}. {m['name']} — {m['prices'][svc]}₽\n"
                            update.message.reply_text(text)
                            return
            # ask service
            update.message.reply_text(random.choice(intents['ask_booking']['responses']))
            data['stage'] = 1
            return

        # сначала пробуем ответ из диалогов
        faq = get_best_match(msg, dialogues)
        if faq and not faq.startswith("Уточните"):
            update.message.reply_text(faq)
            return

        # если не нашли — классифицируем как намерение
        intent = classify_intent(msg)
        if intent in intents:
            update.message.reply_text(random.choice(intents[intent]['responses']))
        else:
            update.message.reply_text("Извините, я вас не понял.")
        return


        # Stage 1: choose service

    if data['stage'] == 1:
        for svc in services:
            if svc in msg:
                data['service'] = svc
                update.message.reply_text(f"Уточните, какая {svc}: {', '.join(services[svc])}?")
                data['stage'] = 2
                return

        update.message.reply_text("Пожалуйста, выберите: стрижка, укладка или окрашивание.")
        return


        # Stage 2: choose subcategory
    if data['stage'] == 2:
        for sub in services[data['service']]:
            if sub in msg:
                data['subcategory'] = sub
                text = 'Выберите мастера:\n'
                for i, m in enumerate(masters, 1):
                    price = m['prices'].get(sub)
                    if price:
                        text += f"{i}. {m['name']} — {price}₽\n"
                    else:
                        text += f"{i}. {m['name']} — цена не указана\n"
                update.message.reply_text(text)
                data['stage'] = 3
                return

        update.message.reply_text(f"Уточните, какая {data['service']}: {', '.join(services[data['service']])}?")
        return


    # Stage 3: choose master
    if data['stage'] == 3:
        if msg.isdigit() and 1 <= int(msg) <= len(masters):
            m = masters[int(msg) - 1]
            data['master'] = m
            data['price'] = m['prices'][data['subcategory']]
            update.message.reply_text(f"Цена {data['price']}₽. Как вас зовут?")
            data['stage'] = 4
        else:
            update.message.reply_text("Введите номер мастера (1,2 или 3).")
        return


    # Stage 4: name
    if data['stage']==4:
        if re.fullmatch(r"[а-яёА-ЯЁ\s]+", msg):
            data['name']=msg.title()
            update.message.reply_text("Укажите телефон в формате +7XXXXXXXXXX:")
            data['stage']=5
        else:
            update.message.reply_text("Введите корректное имя.")
        return

    # Stage 5: phone
    if data['stage']==5:
        if re.fullmatch(r"\+7\d{10}", msg):
            data['phone']=msg
            update.message.reply_text("Введите дату и время YYYY-MM-DD HH:MM:")
            data['stage']=6
        else:
            update.message.reply_text("Формат: +7XXXXXXXXXX")
        return

    # Stage 6: datetime
    if data['stage']==6:
        try:
            from datetime import datetime
            datetime.strptime(msg, "%Y-%m-%d %H:%M")
            data['datetime']=msg
            update.message.reply_text(
                f"Запись: {data['subcategory']} {data['service']}\n"
                f"Мастер: {data['master']['name']}\n"
                f"Дата/время: {data['datetime']}\n"
                f"Имя: {data['name']}, Телефон: {data['phone']}\n"
                f"Цена: {data['price']}₽"
            )
            ctx[uid]={'stage':0}
        except:
            update.message.reply_text("Неверный формат даты. Используйте YYYY-MM-DD HH:MM")
        return

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
