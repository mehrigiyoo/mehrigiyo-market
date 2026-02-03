from django.core.management.base import BaseCommand
from partner_auth.models import Partner


class Command(BaseCommand):
    help = 'Yangi partner yaratish va uning credentials ni chiqarish'

    def add_arguments(self, parser):
        parser.add_argument('partner_name', type=str, help='Partner nomi')
        parser.add_argument(
            '--rate-limit',
            type=int,
            default=60,
            help='Minutiga ruxsat berilgan so\'rovlar soni (default: 60)'
        )

    def handle(self, *args, **options):
        partner_name = options['partner_name']
        rate_limit = options['rate_limit']

        # Bunday partner mavjudligini tekshirish
        if Partner.objects.filter(name=partner_name).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ "{partner_name}" nomli partner allaqachon mavjud!')
            )
            return

        # Credentials yaratish
        api_key, api_secret = Partner.generate_credentials()

        # Partner yaratish
        partner = Partner.objects.create(
            name=partner_name,
            api_key=api_key,
            api_secret=Partner.hash_secret(api_secret),
            rate_limit_per_minute=rate_limit,
            is_active=True
        )

        # Natijani chiqarish
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Partner muvaffaqiyatli yaratildi!'))
        self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))

        self.stdout.write(self.style.WARNING('⚠️  BU MA\'LUMOTLARNI XAVFSIZ JOYDA SAQLANG!'))
        self.stdout.write(self.style.WARNING('⚠️  API Secret qayta tiklanmaydi!\n'))

        self.stdout.write(f"Partner nomi:    {self.style.HTTP_INFO(partner_name)}")
        self.stdout.write(f"API Key:         {self.style.HTTP_INFO(api_key)}")
        self.stdout.write(f"API Secret:      {self.style.HTTP_INFO(api_secret)}")
        self.stdout.write(f"Rate Limit:      {self.style.HTTP_INFO(f'{rate_limit}/min')}")
        self.stdout.write(f"Status:          {self.style.SUCCESS('Active')}\n")

        self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))

        # Test qilish uchun curl misol
        self.stdout.write(self.style.HTTP_INFO('📝 Test qilish uchun:'))
        self.stdout.write(self.style.HTTP_INFO('\ncurl -X POST http://your-domain.com/api/partner/token/ \\'))
        self.stdout.write(self.style.HTTP_INFO(f'  -H "X-API-Key: {api_key}" \\'))
        self.stdout.write(self.style.HTTP_INFO(f'  -H "X-API-Secret: {api_secret}" \\'))
        self.stdout.write(self.style.HTTP_INFO('  -H "Content-Type: application/json" \\'))
        self.stdout.write(
            self.style.HTTP_INFO('  -d \'{"user_phone": "+998901234567", "create_if_not_exists": false}\''))
        self.stdout.write('\n')