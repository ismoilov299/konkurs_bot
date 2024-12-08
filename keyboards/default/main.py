import os
from email.policy import default

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, db


@dp.message_handler(lambda message: message.text == "🎁 Mukofot")
async def send_latest_award(message: types.Message):
    latest_award = db.get_latest_award()

    if latest_award:
        if len(latest_award) == 3:
            title, description, image_path = latest_award
        elif len(latest_award) == 2:
            title = "Mukofot"
            description, image_path = latest_award
        else:
            await message.answer("🎁 Mukofot ma'lumotlarini olishda xatolik yuz berdi.")
            return

        if image_path:
            correct_image_path = os.path.join('admin', image_path)
            if os.path.exists(correct_image_path):
                with open(correct_image_path, 'rb') as photo:
                    await message.answer_photo(
                        photo=photo,
                        caption=f"🎁 {title}\n\n{description}"
                    )
            else:
                await message.answer(f"🎁 {title}\n\n{description}")
        else:
            await message.answer(f"🎁 {title}\n\n{description}")
    else:
        await message.answer("🎁 Hozircha mukofotlar yo'q.")


@dp.message_handler(lambda message: message.text == "🏆 Reyting")
async def send_top_users_and_score(message: types.Message):
    user_id = message.from_user.id
    top_users = db.get_top_users_by_score()
    user_score = db.get_score_by_id(user_id)

    if top_users:
        top_users_text = []
        for i, user_data in enumerate(top_users):
            if len(user_data) == 3:
                fullname, score, telegram_id = user_data
            else:
                fullname, score = user_data
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
            top_users_text.append(
                f"{i + 1}) {medal} {fullname}\n"
                f"Ball: {score} 🎯"
            )

        response = "🏆 TOP ISHTIROKCHILAR:\n\n"
        response += "\n\n".join(top_users_text)

        if user_score is not None:
            response += f"\n\n📊 Sizning ballingiz: {user_score} 🎯"

        await message.answer(response)
    else:
        await message.answer("📊 Hozircha reyting mavjud emas.")


@dp.message_handler(lambda message: message.text == "🤝 Shartlar")
async def send_terms(message: types.Message):
    terms_text = (f"Qatnashish uchun: ⬇️\n\n"
                  f"🔗 Bot sizga taqdim etgan referral linkni iloji boricha ko'proq\n"
                  f"do'stlaringizga ulashing. Sizni linkingizdan qo'shilgan har bir ishtirokchiga\n"
                  f"2 balldan beriladi. Sovg'alar eng ko'p ball to'plagan 2 ta ishtirokchiga\n"
                  f"beriladi.\n\n"
                  f"Quyidagi 📎Taklif qilish havolasini olish tugmasini bosib, do'stlaringizni\n"
                  f"taklif qilishni boshlang👇\n\n"

        f"https://t.me/{(await message.bot.me).username}?start={message.from_user.id}"
    )

    await message.answer(terms_text)




