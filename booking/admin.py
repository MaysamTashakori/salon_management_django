from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Service, Stylist, Appointment, Review

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration')
    search_fields = ('name',)
    list_filter = ('duration',)

@admin.register(Stylist)
class StylistAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'experience_years', 'is_available')
    search_fields = ('user__first_name', 'user__last_name')
    list_filter = ('is_available', 'experience_years')
    filter_horizontal = ('services',)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'نام کامل'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'stylist', 'date', 'time', 'status')
    list_filter = ('status', 'date', 'service')
    search_fields = ('client__first_name', 'client__last_name', 'stylist__user__first_name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('appointment__client__first_name', 'comment')
    readonly_fields = ('created_at',)
from django.contrib import admin
from .models import Holiday

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'date']
    search_fields = ['description']
