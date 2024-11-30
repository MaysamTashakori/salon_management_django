from django.core.management.base import BaseCommand
from booking.models import CustomUser, Service, Stylist, Appointment, Review
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates test data for the salon management system'

    def handle(self, *args, **options):
        # Create test users
        clients = []
        for i in range(5):
            client, created = CustomUser.objects.get_or_create(
                username=f'client{i+1}',
                defaults={
                    'first_name': random.choice(['سارا', 'مینا', 'رضا', 'علی', 'زهرا']),
                    'last_name': random.choice(['کریمی', 'محمدی', 'رضایی', 'احمدی', 'حسینی']),
                    'phone_number': f'0912{random.randint(1000000, 9999999)}',
                    'email': f'client{i+1}@example.com',
                }
            )
            if created:
                client.set_password('client123')
                client.save()
            clients.append(client)

        # Create stylists
        stylist_names = [
            ('مریم', 'محمدی'), ('سارا', 'احمدی'), 
            ('زینب', 'حسینی'), ('فاطمه', 'کریمی')
        ]
        stylists_users = []
        for i, (first, last) in enumerate(stylist_names):
            stylist_user, created = CustomUser.objects.get_or_create(
                username=f'stylist{i+1}',
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'phone_number': f'0919{random.randint(1000000, 9999999)}',
                    'email': f'stylist{i+1}@example.com',
                    'is_staff': True
                }
            )
            if created:
                stylist_user.set_password('stylist123')
                stylist_user.save()
            stylists_users.append(stylist_user)

        # Create services
        services_data = [
            {
                'name': 'میکاپ عروس',
                'description': 'آرایش کامل عروس با متدهای روز دنیا',
                'price': 2500000,
                'duration': 180
            },
            {
                'name': 'اصلاح ابرو',
                'description': 'اصلاح ابرو با متد تخصصی و میکروبلیدینگ',
                'price': 200000,
                'duration': 30
            },
            {
                'name': 'کراتینه مو',
                'description': 'کراتینه مو با بهترین متریال برزیلی',
                'price': 1500000,
                'duration': 150
            },
            {
                'name': 'رنگ مو',
                'description': 'رنگ مو با برندهای معتبر جهانی',
                'price': 800000,
                'duration': 120
            },
            {
                'name': 'کوتاهی مو',
                'description': 'کوتاهی مو با جدیدترین متدهای روز',
                'price': 300000,
                'duration': 60
            },
            {
                'name': 'شینیون',
                'description': 'شینیون مو با مدل‌های متنوع و خاص',
                'price': 1000000,
                'duration': 90
            }
        ]

        services = []
        for service_data in services_data:
            service, _ = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            services.append(service)

        # Create stylist profiles
        stylists = []
        for i, stylist_user in enumerate(stylists_users):
            stylist, _ = Stylist.objects.get_or_create(
                user=stylist_user,
                defaults={
                    'bio': f'متخصص با {random.randint(3, 15)} سال سابقه کار',
                    'experience_years': random.randint(3, 15)
                }
            )
            # Assign random services to each stylist
            stylist.services.set(random.sample(services, random.randint(2, 4)))
            stylists.append(stylist)

        # Create appointments
        Appointment.objects.all().delete()
        
        start_date = datetime.now()
        status_choices = ['pending', 'confirmed', 'completed', 'cancelled']
        
        for i in range(20):  # Creating 20 appointments
            appointment_date = start_date + timedelta(days=random.randint(0, 30))
            status = random.choice(status_choices)
            
            appointment = Appointment.objects.create(
                client=random.choice(clients),
                service=random.choice(services),
                stylist=random.choice(stylists),
                date=appointment_date.date(),
                time=f'{random.randint(9,17):02d}:00',
                status=status,
                notes=random.choice(['', 'درخواست مدل خاص', 'نیاز به مشاوره'])
            )
            
            # Add reviews for completed appointments
            if status == 'completed':
                Review.objects.create(
                    appointment=appointment,
                    rating=random.randint(3, 5),
                    comment=random.choice([
                        'عالی بود، خیلی راضی بودم',
                        'کار تمیز و حرفه‌ای',
                        'برخورد پرسنل عالی بود',
                        'از نتیجه کار راضی هستم'
                    ])
                )

        self.stdout.write(self.style.SUCCESS('داده‌های تستی با موفقیت ایجاد شدند'))
