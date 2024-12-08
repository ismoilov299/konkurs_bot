import re
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from loader import dp, db, bot
from urllib.parse import urlparse


def create_main_keyboard():
    """Asosiy klaviaturani yaratish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton(text="🎁 Mukofot"), KeyboardButton(text="🏆 Reyting"))
    keyboard.row(KeyboardButton(text="🤝 Shartlar"))
    return keyboard


def get_channel_username(url: str) -> str:
    """Kanal usernameni olish"""
    path = urlparse(url).path.strip('/')
    if path.startswith('@'):
        return path
    return '@' + path


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    if message.chat.type != types.ChatType.PRIVATE:
        await message.reply(
            "Menga shaxsiydan yozing va men sizga javob beraman",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    user_id = message.from_user.id
    user_fullname = message.from_user.full_name
    username = message.from_user.username
    referral_args = message.get_args()

    # Foydalanuvchini tekshirish va qo'shish
    user = db.get_user_by_chat_id(user_id)
    if not user:
        user = db.add_user(
            fullname=user_fullname,
            user_id=user_id,
            username=username,
            referral_code=str(user_id)
        )
        # Referral aloqani yaratish
        if referral_args and referral_args.isdigit():
            referrer_id = int(referral_args)
            db.check_and_create_referral(referrer_id, user_id)

    # Faol kanallarni olish va tekshirish
    links = db.get_all_active_links()
    not_subscribed = []

    for title, url in links:
        channel_username = get_channel_username(url)
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append((title, url))
        except Exception as e:
            print(f"Xatolik: {channel_username} tekshirishda: {e}")
            not_subscribed.append((title, url))

    if not not_subscribed:  # Barcha kanallarga obuna bo'lgan
        # Referral bonus berish
        if referral_args and referral_args.isdigit():
            referrer_id = int(referral_args)
            db.give_referral_bonus(referrer_id, user_id)

        # Asosiy menyuni ko'rsatish
        main_keyboard = create_main_keyboard()
        await message.answer(
            f"Assalomu aleykum, {user_fullname}!\n\n"
            f"🔗 Do'stlaringizni taklif qilish uchun havola:\n"
            f"https://t.me/{(await bot.me).username}?start={user_id}\n\n"
            f"Do'stingiz kanallarga obuna bo'lgandan so'ng sizga 10 ball beriladi!\n\n"
            f"Quyidagi tugmalar orqali kerakli bo'limni tanlang:",
            reply_markup=main_keyboard
        )
    else:
        # Inline klaviatura yaratish
        keyboard = InlineKeyboardMarkup(row_width=1)
        # Faqat obuna bo'linmagan kanallarni ko'rsatish
        for title, url in not_subscribed:
            button = InlineKeyboardButton(text=title, url=url)
            keyboard.add(button)

        keyboard.add(InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data='check_subscription'))

        await message.answer(
            f"Assalomu aleykum, {user_fullname}!\n"
            f"Botimizdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=keyboard
        )


@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def process_callback_check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    print(f"Checking subscription for user {user_id}")  # Debug

    # Faol kanallarni olish
    links = db.get_all_active_links()

    not_subscribed = []
    for title, url in links:
        channel_username = get_channel_username(url)
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
            if not is_member:
                not_subscribed.append((title, url))
        except Exception as e:
            print(f"Xatolik: {channel_username} tekshirishda: {e}")
            not_subscribed.append((title, url))

    if not_subscribed:
        # Obuna bo'linmagan kanallar uchun klaviatura
        keyboard = InlineKeyboardMarkup(row_width=1)
        for title, url in not_subscribed:
            button = InlineKeyboardButton(text=title, url=url)
            keyboard.add(button)
        keyboard.add(InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data='check_subscription'))

        await bot.answer_callback_query(
            callback_query.id,
            text="Ba'zi kanallarga obuna bo'lmagansiz."
        )
        await bot.send_message(
            user_id,
            "Quyidagi kanallarga obuna bo'ling:",
            reply_markup=keyboard
        )
    else:
        # Statistikani yangilash
        db.update_statistics()

        # Referral tekshirish va ball berish
        user = db.get_user_by_chat_id(user_id)
        print(f"User data: {user}")  # Debug

        if user and not user[6]:  # is_referral_counted tekshirish
            # Bazadan referrer_id ni olish
            sql = "SELECT referred_by_id FROM konkurs_user WHERE telegram_id = ?"
            referrer_data = db.execute(sql, (user_id,), fetchone=True)
            print(f"Referrer data: {referrer_data}")  # Debug

            if referrer_data and referrer_data[0]:
                referrer_id = referrer_data[0]
                try:
                    # Referrer telegram_id ni olish
                    sql = "SELECT telegram_id FROM konkurs_user WHERE id = ?"
                    referrer_telegram_id = db.execute(sql, (referrer_id,), fetchone=True)

                    if referrer_telegram_id:
                        print(f"Updating score for referrer {referrer_telegram_id[0]}")  # Debug
                        db.update_user_score(referrer_telegram_id[0], 10)
                        db.mark_referral_counted(user_id)
                        print("Referral bonus given successfully")  # Debug
                except Exception as e:
                    print(f"Error while giving referral bonus: {e}")  # Debug

        # Asosiy menyuni ko'rsatish
        main_keyboard = create_main_keyboard()
        await bot.send_message(
            user_id,
            f"✅ Siz botdan foydalanishingiz mumkin!\n\n"
            f"🔗 Do'stlaringizni taklif qilish uchun havola:\n"
            f"https://t.me/{(await bot.me).username}?start={user_id}\n\n"
            f"Do'stingiz kanallarga obuna bo'lgandan so'ng sizga 10 ball beriladi!\n\n"
            f"Quyidagi tugmalar orqali kerakli bo'limni tanlang:",
            reply_markup=main_keyboard
        )

        await bot.answer_callback_query(
            callback_query.id,
            text="Barcha kanallarga obuna bo'ldingiz!"
        )


@dp.callback_query_handler(lambda c: c.data.startswith('subscribe_'))
async def process_subscribe_callback(callback_query: types.CallbackQuery):
    url = callback_query.data[len('subscribe_'):]
    channel_username = get_channel_username(url)
    user_id = callback_query.from_user.id

    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        is_member = member.status in ['member', 'administrator', 'creator']

        if is_member:
            await bot.answer_callback_query(
                callback_query.id,
                text="Siz allaqachon bu kanalga obuna bo'lgansiz."
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="Siz hali obuna bo'lmagansiz. Obuna bo'lishingiz zarur."
            )
    except Exception as e:
        print(f"Xatolik: {channel_username} tekshirishda: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )