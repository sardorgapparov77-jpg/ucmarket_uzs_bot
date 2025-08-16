# UCmarket_UZS – minimal ishchi bot (aiogram 2.25.1)
# /start -> menyu, "💳 To‘lov ma’lumotlari" -> kartalar,
# "💰 UC buyurtma" -> paket tanlash -> PUBG ID -> (ixtiyoriy nick) -> chek rasm yuborish

import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
# Istasangiz: BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN = "8482805730:AAHFhONSobJ2XclC7VC54jHkRvZasZA1MpA"
# UC paketlari (UC, narx UZS)
PRICES = [
    (60, 12000), (120, 24000), (180, 38000),
    (325, 59000), (385, 71000), (445, 83000),
    (660, 115000), (720, 127000), (780, 140000)
]

# To‘lov ma’lumotlari
PAYMENT_TEXT = (
    "💳 To‘lov usuli: Uzcard / Humo / Mastercard / Visa\n\n"
    "📌 To‘lov ma’lumotlari:\n"
    "• Payme: +998933750907 (SARDOR ASATILLAEV)\n"
    "• HUMO: 9860 6004 3200 1680\n"
    "• UZCARD: 8600 0604 6580 2461\n"
    "• MASTERCARD: 5321 5400 5080 9249\n\n"
    "‼️ To‘lovda ism sifatida <b>SARDOR ASATILLAEV</b> ko‘rinishi shart."
)

# --- BOT OBYEKTLARI ---
bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# --- HOLATLAR (FSM) ---
class OrderFlow(StatesGroup):
    waiting_pubg = State()
    waiting_nick = State()
    waiting_receipt = State()

# --- KLAVIATURALAR ---
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("💰 UC buyurtma", "🎁 Aksiya / Referal",
           "💳 To‘lov ma’lumotlari", "👤 Profil / Yordam")
    return kb

def packages_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    for uc, price in PRICES:
        kb.insert(InlineKeyboardButton(f"{uc} UC • {price:,} so'm", callback_data=f"pkg:{uc}"))
    return kb

# --- YORDAMCHI ---
def price_of(uc: int) -> int:
    for u, p in PRICES:
        if u == uc:
            return p
    return 0

# --- HANDLERLAR ---
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    await m.answer("👋 Assalomu alaykum!\nUCmarket_UZS ga xush kelibsiz.\n\n🌐 Menyudan tanlang:", reply_markup=main_menu())

@dp.message_handler(lambda msg: msg.text == "💳 To‘lov ma’lumotlari")
async def pay_info(m: types.Message):
    await m.answer(PAYMENT_TEXT, reply_markup=main_menu())

@dp.message_handler(lambda msg: msg.text == "🎁 Aksiya / Referal")
async def referral(m: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{m.from_user.id}"
    await m.answer(
        "🎁 Referal aksiyasi!\nDo‘stlaringizni taklif qiling va bonuslar oling.\n\n"
        f"🔗 Sizning referal havolangiz:\n<code>{link}</code>\n\n"
        "ℹ️ Hozircha oddiy havola ko‘rsatildi (hisoblash keyinroq qo‘shiladi).",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda msg: msg.text == "👤 Profil / Yordam")
async def profile_help(m: types.Message):
    await m.answer(
        f"👤 Profil / Yordam\n• Username: @{m.from_user.username or '—'}\n• Savollar: @Sardor0073",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda msg: msg.text == "💰 UC buyurtma")
async def buy_entry(m: types.Message):
    await m.answer("🌟 Paketni tanlang:", reply_markup=packages_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("pkg:"))
async def pkg_chosen(c: types.CallbackQuery, state: FSMContext):
    uc = int(c.data.split(":")[1])
    price = price_of(uc)
    await state.update_data(uc=uc, price=price)
    await bot.send_message(
        c.from_user.id,
        f"🧾 Tanlangan: <b>{uc} UC</b> — <b>{price:,} so‘m</b>\n\n🆔 Iltimos, PUBG ID kiriting (faqat raqam)."
    )
    await OrderFlow.waiting_pubg.set()
    await c.answer()

@dp.message_handler(state=OrderFlow.waiting_pubg, content_types=types.ContentTypes.TEXT)
async def get_pubg(m: types.Message, state: FSMContext):
    pubg_id = m.text.strip()
    await state.update_data(pubg_id=pubg_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("⏭️ O‘tkazib yuborish")
    await m.answer("📝 (ixtiyoriy) Nickname kiriting yoki «⏭️ O‘tkazib yuborish»ni bosing.", reply_markup=kb)
    await OrderFlow.waiting_nick.set()

@dp.message_handler(state=OrderFlow.waiting_nick, content_types=types.ContentTypes.TEXT)
async def get_nick_or_skip(m: types.Message, state: FSMContext):
    nick = None if m.text == "⏭️ O‘tkazib yuborish" else m.text.strip()
    await state.update_data(nickname=nick)
    data = await state.get_data()
    uc, price = data["uc"], data["price"]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ To‘lov qildim", "🔙 Orqaga")
    await m.answer(
        f"{PAYMENT_TEXT}\n🧾 Buyurtma: <b>{uc} UC</b> — <b>{price:,} so‘m</b>\n\n"
        "To‘lovni bajaring va «✅ To‘lov qildim»ni bosib, <b>chek rasm</b> yuboring.",
        reply_markup=kb
    )
    await OrderFlow.waiting_receipt.set()

@dp.message_handler(lambda msg: msg.text == "🔙 Orqaga")
async def back_to_menu(m: types.Message, state: FSMContext):
    await state.finish()
    await m.answer("🏠 Bosh menyu:", reply_markup=main_menu())

@dp.message_handler(state=OrderFlow.waiting_receipt,
                    content_types=[types.ContentTypes.PHOTO, types.ContentTypes.DOCUMENT, types.ContentTypes.TEXT])
async def get_receipt(m: types.Message, state: FSMContext):
    file_id = None
    if m.photo:
        file_id = m.photo[-1].file_id
    elif m.document and (m.document.mime_type or "").startswith("image/"):
        file_id = m.document.file_id

    if m.text == "✅ To‘lov qildim" and not file_id:
        await m.answer("📎 Iltimos, chek rasm yuboring (foto).")
        return
    if not file_id:
        await m.answer("📎 Faqat rasm yuboring (chek).")
        return

    # Bu yerda odatda admin'ga yuborish/forward qilinadi (soddalashtirilgan)
    await m.answer("📤 To‘lovingiz tekshirilmoqda...\n⏳ Tez orada UC akkauntingizda paydo bo‘ladi.", reply_markup=main_menu())
    await state.finish()

# --- POLLINGNI BARQAROR BOSHLASH (webhookni o'chirish) ---
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    print("🔌 Webhook o'chirildi, polling boshlanadi")

if __name__ == "__main__":
    print("🚀 Bot ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
