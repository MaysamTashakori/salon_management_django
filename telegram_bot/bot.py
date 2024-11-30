from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from urllib.parse import quote
import django
import os
import sys
import logging
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime
from persiantools.jdatetime import JalaliDateTime, JalaliDate
from datetime import datetime

# Django Setup
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salon_management.settings')
django.setup()

from booking.models import CustomUser, Stylist, Service, Appointment

# States
PHONE, USERNAME, EMAIL, PASSWORD, NAME = range(5)

# Status Dictionary
APPOINTMENT_STATUS = {
    'pending': '⏳ در انتظار تایید',
    'confirmed': '✅ تایید شده',
    'cancelled': '❌ لغو شده',
    'completed': '🎯 انجام شده'
}
@sync_to_async
def create_user(username, email, password, phone_number, first_name, last_name):
    try:
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return False, "این شماره تلفن قبلاً ثبت شده است"
        
        if CustomUser.objects.filter(username=username).exists():
            return False, "این نام کاربری قبلاً ثبت شده است"
        
        if CustomUser.objects.filter(email=email).exists():
            return False, "این ایمیل قبلاً ثبت شده است"
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        return True, user.id
    except Exception as e:
        return False, str(e)
@sync_to_async
def get_stylist_name(stylist):
    return stylist.user.get_full_name()

@sync_to_async
def get_stylists_with_names(service_id):
    stylists = list(Stylist.objects.filter(services__id=service_id))
    result = []
    for stylist in stylists:
        result.append({
            'id': stylist.id,
            'name': stylist.user.get_full_name()
        })
    return result

async def show_stylists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    service_id = int(query.data.split('_')[1])
    context.user_data['service_id'] = service_id
    
    stylists = await get_stylists_with_names(service_id)
    keyboard = []
    for stylist in stylists:
        keyboard.append([InlineKeyboardButton(
            f"👩‍💼 {stylist['name']}",
            callback_data=f'stylist_{stylist["id"]}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='book')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👩‍💼 لطفاً آرایشگر مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

@sync_to_async
def get_user_by_phone(phone):
    try:
        return CustomUser.objects.get(phone_number=phone)
    except CustomUser.DoesNotExist:
        return None

@sync_to_async
def get_services():
    return list(Service.objects.all())

@sync_to_async
def get_stylists_for_service(service_id):
    return list(Stylist.objects.filter(services__id=service_id))

@sync_to_async
def get_appointment_by_id(appointment_id):
    return Appointment.objects.select_related(
        'service', 
        'stylist', 
        'stylist__user'
    ).get(id=appointment_id)

@sync_to_async
def get_formatted_appointments(user_id):
    return list(Appointment.objects.filter(client_id=user_id)
                .select_related('service', 'stylist', 'stylist__user')
                .order_by('date', 'time'))


@sync_to_async
def create_appointment(user_id, service_id, stylist_id, date, time):
    try:
        # تبدیل تاریخ از رشته به شیء datetime
        appointment_date = datetime.strptime(date, "%Y/%m/%d").date()
        
        # بررسی تداخل زمانی
        existing_appointment = Appointment.objects.filter(
            stylist_id=stylist_id,
            date=appointment_date,
            time=time
        ).exists()
        
        if existing_appointment:
            return None
            
        # ایجاد نوبت جدید
        appointment = Appointment.objects.create(
            client_id=user_id,
            service_id=service_id,
            stylist_id=stylist_id,
            date=appointment_date,
            time=time,
            status='pending'
        )
        return appointment
        
    except Exception as e:
        print(f"Error creating appointment: {e}")
        return None

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stylist_id = int(query.data.split('_')[1])
    context.user_data['stylist_id'] = stylist_id
    
    keyboard = []
    today = datetime.now()  # Changed from JalaliDateTime to datetime
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y/%m/%d")
        display_date = convert_to_persian_date(date_str)
        keyboard.append([InlineKeyboardButton(
            display_date,
            callback_data=f'date_{date_str}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'service_{context.user_data["service_id"]}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 لطفاً تاریخ مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
def convert_to_persian_date(date_str):
    gregorian_date = datetime.strptime(date_str, "%Y/%m/%d")
    jalali_date = JalaliDateTime.to_jalali(gregorian_date)
    
    persian_months = {
        1: "فروردین", 2: "اردیبهشت", 3: "خرداد",
        4: "تیر", 5: "مرداد", 6: "شهریور",
        7: "مهر", 8: "آبان", 9: "آذر",
        10: "دی", 11: "بهمن", 12: "اسفند"
    }
    
    return f"{jalali_date.day} {persian_months[jalali_date.month]} {jalali_date.year}"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton('📱 ارسال شماره تماس', request_contact=True)],
        [KeyboardButton('❓ راهنما'), KeyboardButton('📞 تماس با ما')],
        [KeyboardButton('📍 آدرس سالن'), KeyboardButton('🎀 درباره ما')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🌸 به سالن زیبایی خوش آمدید!\n"
        "برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number
    phone = ''.join(filter(str.isdigit, phone))[-10:]
    
    user = await get_user_by_phone(phone)
    if user:
        context.user_data['user_id'] = user.id
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    context.user_data['phone'] = phone
    await update.message.reply_text(
        "✨ نام کاربری خود را وارد کنید:",
        reply_markup=ReplyKeyboardRemove()
    )
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text("📧 ایمیل خود را وارد کنید:")
    return EMAIL

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    context.user_data['email'] = email
    await update.message.reply_text("🔑 رمز عبور خود را وارد کنید:")
    return PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    context.user_data['password'] = password
    await update.message.reply_text("👤 نام و نام خانوادگی خود را وارد کنید:")
    return NAME
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    first_name = full_name.split()[0]
    last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
    
    success, result = await create_user(
        context.user_data['username'],
        context.user_data['email'],
        context.user_data['password'],
        context.user_data['phone'],
        first_name,
        last_name
    )
    
    if success:
        context.user_data['user_id'] = result
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(f"❌ خطا در ثبت‌نام: {result}")
        return ConversationHandler.END
    
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✨ رزرو نوبت", callback_data='book')],
        [InlineKeyboardButton("📋 نوبت‌های من", callback_data='my_appointments')],
        [InlineKeyboardButton("❓ راهنما", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🌸 منوی اصلی\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🌸 منوی اصلی\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await get_services()
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(
            f"💇‍♀️ {service.name} - {service.price:,} تومان",
            callback_data=f'service_{service.id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "✨ لطفاً خدمت مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_stylists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    service_id = int(query.data.split('_')[1])
    context.user_data['service_id'] = service_id
    
    stylists = await get_stylists_for_service(service_id)
    keyboard = []
    for stylist in stylists:
        keyboard.append([InlineKeyboardButton(
            f"👩‍💼 {stylist.user.get_full_name()}",
            callback_data=f'stylist_{stylist.id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='book')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👩‍💼 لطفاً آرایشگر مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stylist_id = int(query.data.split('_')[1])
    context.user_data['stylist_id'] = stylist_id
    
    keyboard = []
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y/%m/%d")
        display_date = convert_to_persian_date(date_str)
        keyboard.append([InlineKeyboardButton(
            display_date,
            callback_data=f'date_{date_str}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'service_{context.user_data["service_id"]}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 لطفاً تاریخ مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    selected_date = query.data.split('_')[1]
    context.user_data['date'] = selected_date
    
    time_slots = []
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("21:00", "%H:%M")
    interval = timedelta(minutes=30)
    
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime("%H:%M")
        time_slots.append([InlineKeyboardButton(
            f"⏰ {time_str}",
            callback_data=f'time_{time_str}'
        )])
        current_time += interval
    
    time_slots.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'stylist_{context.user_data["stylist_id"]}')])
    reply_markup = InlineKeyboardMarkup(time_slots)
    
    await query.edit_message_text(
        "⏰ لطفاً ساعت مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def confirm_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    selected_time = query.data.split('_')[1]
    context.user_data['time'] = selected_time
    
    appointment = await create_appointment(
        user_id=context.user_data['user_id'],
        service_id=context.user_data['service_id'],
        stylist_id=context.user_data['stylist_id'],
        date=context.user_data['date'],
        time=selected_time
    )
    
    if appointment:
        text = "✅ نوبت شما با موفقیت ثبت شد!\n\n"
        text += f"📅 تاریخ: {convert_to_persian_date(context.user_data['date'])}\n"
        text += f"⏰ ساعت: {selected_time}\n"
        keyboard = [
            [InlineKeyboardButton("📋 مشاهده نوبت‌های من", callback_data='my_appointments')],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
        ]
    else:
        text = "❌ متأسفانه این زمان قبلاً رزرو شده است.\n"
        keyboard = [
            [InlineKeyboardButton("🔄 انتخاب زمان دیگر", callback_data=f'stylist_{context.user_data["stylist_id"]}')],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📌 راهنمای استفاده از ربات:\n\n"
        "1️⃣ ابتدا شماره تماس خود را ثبت کنید\n"
        "2️⃣ از منوی اصلی، خدمت مورد نظر را انتخاب کنید\n"
        "3️⃣ زمان و تاریخ مناسب را انتخاب کنید\n"
        "4️⃣ نوبت شما ثبت خواهد شد\n\n"
        "برای شروع مجدد از دستور /start استفاده کنید"
    )
    await update.message.reply_text(text)

async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📞 راه‌های ارتباطی با ما:\n\n"
        "☎️ تلفن ثابت: 021-12345678\n"
        "📱 موبایل: 0912-3456789\n"
        "📧 ایمیل: info@salon.com\n"
        "🌐 وبسایت: www.salon.com\n"
        "📱 اینستاگرام: @salon_beauty"
    )
    await update.message.reply_text(text)

async def salon_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📍 آدرس سالن زیبایی:\n\n"
        "تهران، خیابان ولیعصر، نرسیده به میدان ونک\n"
        "پلاک 123، طبقه دوم\n\n"
        "🕐 ساعات کاری:\n"
        "شنبه تا چهارشنبه: 9 صبح تا 9 شب\n"
        "پنجشنبه: 9 صبح تا 10 شب\n"
        "جمعه‌ها: 10 صبح تا 8 شب"
    )
    await update.message.reply_text(text)

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎀 درباره سالن زیبایی ما:\n\n"
        "✨ با بیش از 10 سال سابقه درخشان\n"
        "👩‍💼 بهترین آرایشگران با مدارک بین‌المللی\n"
        "🏆 دارای گواهینامه‌های معتبر از انجمن صنفی\n"
        "💝 ارائه خدمات VIP\n"
        "✅ تضمین کیفیت خدمات\n"
        "🛡️ استفاده از برندهای معتبر و اورجینال\n"
        "♨️ محیطی کاملاً بهداشتی و لوکس"
    )
    await update.message.reply_text(text)
async def show_my_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    appointments = await get_formatted_appointments(context.user_data['user_id'])
    
    if not appointments:
        keyboard = [[InlineKeyboardButton("✨ رزرو نوبت جدید", callback_data='book')],
                   [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📋 شما هیچ نوبت فعالی ندارید.\n"
            "می‌توانید از دکمه زیر نوبت جدید رزرو کنید.",
            reply_markup=reply_markup
        )
        return

    text = "📅 نوبت‌های فعال شما:\n\n"
    keyboard = []
    for apt in appointments:
        persian_date = convert_to_persian_date(apt.date.strftime("%Y/%m/%d"))
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'completed': '🎯'
        }.get(apt.status, '📌')
        
        button_text = f"{status_emoji} {persian_date} │ {apt.time} │ {apt.service.name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'view_apt_{apt.id}')])
    
    keyboard.extend([
        [InlineKeyboardButton("✨ رزرو نوبت جدید", callback_data='book')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def view_appointment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    apt_id = int(query.data.split('_')[2])
    appointment = await get_appointment_by_id(apt_id)
    
    persian_date = convert_to_persian_date(appointment.date.strftime("%Y/%m/%d"))
    text = (
        f"📅 تاریخ: {persian_date}\n"
        f"⏰ ساعت: {appointment.time}\n"
        f"💇‍♀️ خدمت: {appointment.service.name}\n"
        f"👩‍💼 آرایشگر: {appointment.stylist.user.get_full_name()}\n"
        f"💰 هزینه: {appointment.service.price:,} تومان\n"
        f"📊 وضعیت: {APPOINTMENT_STATUS.get(appointment.status, appointment.status)}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 برگشت به لیست", callback_data='my_appointments')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = (
        "🌟 راهنمای استفاده از ربات:\n\n"
        "1️⃣ از منوی اصلی 'رزرو نوبت' را انتخاب کنید\n"
        "2️⃣ خدمت مورد نظر خود را انتخاب کنید\n"
        "3️⃣ آرایشگر مورد نظر را انتخاب کنید\n"
        "4️⃣ تاریخ و ساعت مناسب را انتخاب کنید\n"
        "5️⃣ نوبت شما ثبت خواهد شد"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
@sync_to_async
def get_stylist_with_user(stylist_id):
    return Stylist.objects.select_related('user').get(id=stylist_id)

@sync_to_async
def get_all_stylists_for_service(service_id):
    return list(Stylist.objects.select_related('user').filter(services__id=service_id))

async def show_stylists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    service_id = int(query.data.split('_')[1])
    context.user_data['service_id'] = service_id
    
    stylists = await get_all_stylists_for_service(service_id)
    keyboard = []
    
    for stylist in stylists:
        full_name = f"{stylist.user.first_name} {stylist.user.last_name}"
        keyboard.append([InlineKeyboardButton(
            f"👩‍💼 {full_name}",
            callback_data=f'stylist_{stylist.id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='book')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👩‍💼 لطفاً آرایشگر مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

def main():
    TOKEN = "YOUR_BOT_TOKEN" # توکن ربات خود را اینجا قرار دهید
    application = ApplicationBuilder().token(TOKEN).build()
    
    # تعریف مسیر مکالمه
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )
    
    # اضافه کردن هندلرها
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(show_services, pattern='^book$'))
    application.add_handler(CallbackQueryHandler(show_stylists, pattern='^service_'))
    application.add_handler(CallbackQueryHandler(handle_date_selection, pattern='^stylist_'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern='^date_'))
    application.add_handler(CallbackQueryHandler(confirm_appointment, pattern='^time_'))
    application.add_handler(CallbackQueryHandler(show_my_appointments, pattern='^my_appointments$'))
    application.add_handler(CallbackQueryHandler(view_appointment_details, pattern='^view_apt_'))
    application.add_handler(CallbackQueryHandler(help_command, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern='^main_menu$'))
    
    # هندلرهای دکمه‌های اصلی
    application.add_handler(MessageHandler(filters.Regex('^❓ راهنما$'), help_message))
    application.add_handler(MessageHandler(filters.Regex('^📞 تماس با ما$'), contact_us))
    application.add_handler(MessageHandler(filters.Regex('^📍 آدرس سالن$'), salon_address))
    application.add_handler(MessageHandler(filters.Regex('^🎀 درباره ما$'), about_us))
    
    print("🟢 Bot successfully launched!")
    print("🤖 To start, go to the bot and enter the /start command")

    application.run_polling()

if __name__ == '__main__':
    main()
