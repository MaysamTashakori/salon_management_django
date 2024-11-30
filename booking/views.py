from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from persiantools.jdatetime import JalaliDateTime
from datetime import datetime, date, timedelta
from .models import Service, Stylist, Appointment, Review
from .forms import (
    AppointmentBookingForm, 
    ReviewForm, 
    CustomUserCreationForm
)
from persiantools.jdatetime import JalaliDateTime
from datetime import datetime, time, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Holiday
from persiantools.jdatetime import JalaliDateTime
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Appointment, Service, Stylist
from django.urls import reverse
from django.http import JsonResponse
def home(request):
    services = Service.objects.all()
    stylists = Stylist.objects.all()
    return render(request, 'home.html', {
        'services': services,
        'stylists': stylists
    })

def services(request):
    services = Service.objects.all()
    return render(request, 'services.html', {'services': services})

def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return render(request, 'services_detail.html', {'service': service})

@login_required
def profile(request):
    appointments = Appointment.objects.filter(client=request.user).order_by('-date')
    return render(request, 'profile.html', {
        'user': request.user,
        'appointments': appointments
    })

@login_required
def dashboard(request):
    if hasattr(request.user, 'stylist'):
        appointments = Appointment.objects.filter(
            stylist=request.user.stylist,
            date=date.today()
        )
        context = {'appointments': appointments}
    else:
        upcoming = Appointment.objects.filter(
            client=request.user,
            date__gte=date.today()
        ).order_by('date', 'time')
        completed = Appointment.objects.filter(
            client=request.user,
            status='completed'
        )
        reviews = Review.objects.filter(appointment__client=request.user)
        context = {
            'upcoming_appointments': upcoming,
            'completed_appointments': completed,
            'reviews': reviews
        }
    return render(request, 'dashboard.html', context)

@login_required
def appointments(request):
    user_appointments = Appointment.objects.filter(
        client=request.user
    ).order_by('-date', '-time')
    return render(request, 'appointments.html', {'appointments': user_appointments})

@login_required
def book_appointment(request):
    if request.method == 'POST':
        # Get form data
        service_id = request.POST.get('service')
        stylist_id = request.POST.get('stylist')
        date_str = request.POST.get('date')
        time_str = request.POST.get('selected_time')

        # Convert Persian date to Gregorian
        persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
        english_numbers = '0123456789'
        translation_table = str.maketrans(persian_numbers, english_numbers)
        date_str = date_str.translate(translation_table)

        jalali_date = JalaliDateTime.strptime(date_str, '%Y/%m/%d')
        gregorian_date = jalali_date.togregorian()

        # Create appointment
        appointment = Appointment.objects.create(
            client=request.user,
            service_id=service_id,
            stylist_id=stylist_id,
            date=gregorian_date,
            time=datetime.strptime(time_str, '%H:%M').time(),
            status='pending'
        )

        messages.success(request, 'نوبت شما با موفقیت ثبت شد!')
        return JsonResponse({
            'status': 'success',
            'message': 'نوبت با موفقیت ثبت شد',
            'redirect_url': reverse('booking:appointment_detail', args=[appointment.pk])
        })
    
    context = {
        'services': Service.objects.all().order_by('name'),
        'stylists': Stylist.objects.all().order_by('user__first_name'),
    }
    return render(request, 'booking/book_appointment.html', context)



@login_required
def add_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.save()
            messages.success(request, 'نظر شما با موفقیت ثبت شد.')
            return redirect('booking:dashboard')
    else:
        form = ReviewForm()
    return render(request, 'booking/add_review.html', {
        'form': form, 
        'appointment': appointment
    })

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
            return redirect('booking:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('booking:dashboard')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است')
    
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت از سیستم خارج شدید')
    return redirect('booking:home')

@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, client=request.user)
    
    if appointment.can_cancel():
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'نوبت شما با موفقیت لغو شد')
    else:
        messages.error(request, 'امکان لغو این نوبت وجود ندارد')
    
    return redirect('booking:appointments')

@login_required
def stylist_dashboard(request):
    if not hasattr(request.user, 'stylist'):
        messages.error(request, 'شما دسترسی به این بخش را ندارید')
        return redirect('booking:home')
    
    today = timezone.now().date()
    stylist = request.user.stylist
    
    context = {
        'today_appointments': Appointment.objects.filter(
            stylist=stylist,
            date=today
        ).order_by('time'),
        'upcoming_appointments': Appointment.objects.filter(
            stylist=stylist,
            date__gt=today
        ).order_by('date', 'time'),
        'pending_appointments': Appointment.objects.filter(
            stylist=stylist,
            status='pending'
        ).order_by('date', 'time'),
        'all_appointments': Appointment.objects.filter(
            stylist=stylist
        ).order_by('-date', '-time')
    }
    
    return render(request, 'booking/stylist_dashboard.html', context)

@login_required
def update_appointment_status(request, pk):
    if not hasattr(request.user, 'stylist'):
        messages.error(request, 'شما دسترسی به این بخش را ندارید')
        return redirect('booking:home')
        
    appointment = get_object_or_404(Appointment, pk=pk, stylist=request.user.stylist)
    new_status = request.POST.get('status')
    
    if new_status in dict(Appointment.STATUS_CHOICES):
        appointment.status = new_status
        appointment.save()
        messages.success(request, 'وضعیت نوبت با موفقیت بروزرسانی شد')
    
    return redirect('booking:stylist_dashboard')

def get_available_times(request):
    date_str = request.GET.get('date')
    stylist_id = request.GET.get('stylist')
    service_id = request.GET.get('service')

    # تبدیل اعداد فارسی به انگلیسی
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    date_str = date_str.translate(translation_table)

    try:
        # تبدیل تاریخ شمسی به میلادی
        jalali_date = JalaliDateTime.strptime(date_str, '%Y/%m/%d')
        gregorian_date = jalali_date.to_gregorian()
        
        # ساخت لیست ساعت‌های خالی
        time_slots = []
        start_time = time(9, 0)  # شروع از ساعت 9 صبح
        end_time = time(21, 0)   # پایان در ساعت 9 شب
        interval = timedelta(minutes=30)  # فاصله 30 دقیقه‌ای

        current_time = start_time
        while current_time <= end_time:
            slot_datetime = datetime.combine(gregorian_date, current_time)
            
            # بررسی در دسترس بودن
            is_available = True  # اینجا منطق بررسی رزرو را اضافه کنید
            
            time_slots.append({
                'time': current_time.strftime('%H:%M'),
                'display': current_time.strftime('%H:%M'),
                'available': is_available
            })
            
            current_time = (datetime.combine(gregorian_date, current_time) + interval).time()

        return JsonResponse(time_slots, safe=False)
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
def get_stylists(request, service_id):
    stylists = Stylist.objects.filter(services__id=service_id)
    data = [{
        'id': stylist.id,
        'name': f"{stylist.user.first_name} {stylist.user.last_name}"
    } for stylist in stylists]
    return JsonResponse(data, safe=False)



def get_holidays(request):
    holidays = Holiday.objects.filter(is_active=True).values('date')
    holiday_list = []
    for holiday in holidays:
        jalali_date = JalaliDateTime.to_jalali(holiday['date'])
        unix_timestamp = int(datetime.combine(holiday['date'], datetime.min.time()).timestamp() * 1000)
        holiday_list.append({
            'date': unix_timestamp,
            'jalali_date': jalali_date.strftime('%Y/%m/%d')
        })
    return JsonResponse(holiday_list, safe=False)

def check_holiday(request):
    date_str = request.GET.get('date')
    try:
        # تبدیل timestamp به تاریخ
        date_obj = datetime.fromtimestamp(int(date_str) / 1000).date()
        is_holiday = Holiday.objects.filter(date=date_obj, is_active=True).exists()
        return JsonResponse({'is_holiday': is_holiday})
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)



def convert_to_gregorian(jalali_date):
    from persiantools.jdatetime import JalaliDateTime
    year, month, day = map(int, jalali_date.split('/'))
    return JalaliDateTime(year, month, day).to_gregorian()
@login_required
def book_appointment(request):
    if request.method == 'POST':
        try:
            # Get form data
            service_id = request.POST.get('service')
            stylist_id = request.POST.get('stylist')
            date_str = request.POST.get('date')
            time_str = request.POST.get('selected_time')

            # Create appointment
            appointment = Appointment.objects.create(
                client=request.user,
                service_id=service_id,
                stylist_id=stylist_id,
                date=convert_to_gregorian(date_str),  # Add this helper function
                time=time_str,
                status='pending'
            )

            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('booking:appointment_success', args=[appointment.pk])
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    context = {
        'services': Service.objects.all(),
    }
    return render(request, 'booking/book_appointment.html', context)

# Add this helper function

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, client=request.user)
    context = {
        'appointment': appointment,
        'title': 'جزئیات نوبت'
    }
    return render(request, 'booking/appointment_detail.html', context)

@login_required
def appointment_success(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, client=request.user)
    return render(request, 'booking/appointment_success.html', {
        'appointment': appointment
    })
