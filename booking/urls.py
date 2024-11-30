from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('services/<int:pk>/', views.service_detail, name='service_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
	path('appointments/', views.appointments, name='appointments'),
    path('appointment/<int:pk>/update-status/', views.update_appointment_status, name='update_appointment_status'),
	path('stylist/dashboard/', views.stylist_dashboard, name='stylist_dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
	path('api/available-times/', views.get_available_times, name='get_available_times'),
	path('api/stylists/<int:service_id>/', views.get_stylists, name='get_stylists'),
	path('api/holidays/', views.get_holidays, name='get_holidays'),
    path('api/check-holiday/', views.check_holiday, name='check_holiday'),
    path('appointment/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('review/<int:appointment_id>/', views.add_review, name='add_review'),
	path('success/<int:pk>/', views.appointment_success, name='appointment_success'),
]
