from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from persiantools.jdatetime import JalaliDateTime
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=11, unique=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_full_name() or self.username

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام خدمت")
    description = models.TextField(verbose_name="توضیحات")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت")
    duration = models.IntegerField(help_text="مدت زمان به دقیقه", verbose_name="مدت زمان")
    
    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"
    
    def __str__(self):
        return self.name

class Stylist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    services = models.ManyToManyField(Service, verbose_name="خدمات")
    bio = models.TextField(verbose_name="بیوگرافی")
    experience_years = models.IntegerField(verbose_name="سال‌های تجربه")
    is_available = models.BooleanField(default=True, verbose_name="در دسترس")
    
    class Meta:
        verbose_name = "آرایشگر"
        verbose_name_plural = "آرایشگران"
    
    def __str__(self):
        return self.user.get_full_name()

class Appointment(models.Model):
    # ثابت‌های ماه‌های فارسی را در سطح کلاس تعریف می‌کنیم
    PERSIAN_MONTHS = {
        1: 'فروردین',
        2: 'اردیبهشت',
        3: 'خرداد',
        4: 'تیر',
        5: 'مرداد',
        6: 'شهریور',
        7: 'مهر',
        8: 'آبان',
        9: 'آذر',
        10: 'دی',
        11: 'بهمن',
        12: 'اسفند'
    }

    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('confirmed', 'تایید شده'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
    ]

    # فیلدهای اصلی همان فیلدهای قبلی
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='appointments', verbose_name="مشتری")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="خدمت")
    stylist = models.ForeignKey(Stylist, on_delete=models.CASCADE, verbose_name="آرایشگر")
    date = models.DateField(verbose_name="تاریخ")
    time = models.TimeField(verbose_name="ساعت")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='pending', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.client.get_full_name()} - {self.service.name}"

    def can_cancel(self):
        return self.status == 'pending'

    @property
    def jalali_date(self):
        try:
            if self.date:
                return JalaliDateTime.to_jalali(self.date).strftime('%Y/%m/%d')
            return "تاریخ نامشخص"
        except:
            return "تاریخ نامشخص"

    @property 
    def formatted_time(self):
        try:
            if self.time:
                return self.time.strftime('%H:%M')
            return "ساعت نامشخص"
        except:
            return "ساعت نامشخص"

    @property
    def get_persian_date(self):
        try:
            jalali_date = JalaliDateTime.to_jalali(self.date)
            month_name = self.PERSIAN_MONTHS[jalali_date.month]
            return f"{jalali_date.day} {month_name} {jalali_date.year}"
        except:
            return "تاریخ نامعتبر"

    # متدهای جدید و مفید
    def get_end_time(self):
        """محاسبه زمان پایان نوبت"""
        start_datetime = datetime.combine(self.date, self.time)
        end_datetime = start_datetime + timedelta(minutes=self.service.duration)
        return end_datetime.time()

    @property
    def is_upcoming(self):
        """آیا نوبت در آینده است"""
        appointment_datetime = datetime.combine(self.date, self.time)
        return appointment_datetime > timezone.now()



class Review(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name="نوبت")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="امتیاز")
    comment = models.TextField(verbose_name="نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    
    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
    
    def __str__(self):
        return f"نظر {self.appointment.client} برای {self.appointment.service}"
from django.db import models
from django.conf import settings

class Holiday(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'روز تعطیل'
        verbose_name_plural = 'روزهای تعطیل'

    def __str__(self):
        return f"{self.date} - {self.description}"



