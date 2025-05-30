import json
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User

class Command(BaseCommand):
    help = 'Import model from a JSON file'

    def handle(self, *args, **kwargs):
        self.import_admin()
        self.import_users()

    def import_users(self):
        with open('data/users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            users = [
                User(
                    email=item['email'],
                    username=item['username'],
                    first_name=item['first_name'],
                    last_name=item['last_name'],
                    password=make_password(item['password'])
                )
                for item in data
            ]
            User.objects.bulk_create(users)
            self.stdout.write(self.style.SUCCESS('Successfully imported users'))

    def import_admin(self):
        with open('data/admin.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            users = [
                User(
                    email=item['email'],
                    username=item['username'],
                    first_name=item['first_name'],
                    last_name=item['last_name'],
                    password=make_password(item['password'])
                )
                for item in data
            ]
            for user in users:
                user.is_superuser = True
                user.is_staff = True
            User.objects.bulk_create(users)
            self.stdout.write(self.style.SUCCESS('Successfully imported admin'))
