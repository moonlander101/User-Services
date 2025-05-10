from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = "Create default roles"

    def handle(self, *args, **kwargs):
        roles = [
            (1, 'Admin', 'Administrator with full access'),
            (2, 'Regular User', 'Standard user account'),
            (3, 'Supplier', 'Product supplier'),
            (4, 'Vendor', 'Product vendor'),
            (5, 'Warehouse Manager', 'Manages warehouses'),
            (6, 'Driver', 'Delivery personnel'),
        ]

        for role_id, name, desc in roles:
            obj, created = Role.objects.get_or_create(id=role_id, defaults={'name': name, 'description': desc})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {name}'))
