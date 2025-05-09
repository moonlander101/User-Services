from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create sample users for all roles in the system'

    def handle(self, *args, **kwargs):
        from accounts.models import Role, Supplier, Vendor, WarehouseManager, Driver
        
        # Create roles if they don't exist
        roles = [
            {"id": 1, "name": "Admin", "description": "System administrator with full access"},
            {"id": 2, "name": "Regular User", "description": "Standard system user"},
            {"id": 3, "name": "Supplier", "description": "Product and service supplier"},
            {"id": 4, "name": "Vendor", "description": "Retail vendor or shop owner"},
            {"id": 5, "name": "Warehouse Manager", "description": "Manages warehouse inventory"},
            {"id": 6, "name": "Driver", "description": "Delivery personnel"}
        ]
        
        self.stdout.write(self.style.SUCCESS('Creating roles...'))
        created_roles = []
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                id=role_data["id"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"]
                }
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(f"{status}: Role {role.name}")
            created_roles.append(role)
        
        User = get_user_model()
        
        # Create admin user
        admin_role = Role.objects.get(id=1)
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': admin_role,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
                'phone': '+1234567890'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
        else:
            self.stdout.write(f'Admin user already exists: {admin_user.username}')
        
        # Create regular user
        regular_role = Role.objects.get(id=2)
        regular_user, created = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@example.com',
                'first_name': 'Regular',
                'last_name': 'User',
                'role': regular_role,
                'is_verified': True,
                'phone': '+1987654321'
            }
        )
        if created:
            regular_user.set_password('user123')
            regular_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created regular user: {regular_user.username}'))
        else:
            self.stdout.write(f'Regular user already exists: {regular_user.username}')
        
        # Create supplier user
        supplier_role = Role.objects.get(id=3)
        supplier_user, created = User.objects.get_or_create(
            username='supplier',
            defaults={
                'email': 'supplier@example.com',
                'first_name': 'Supply',
                'last_name': 'Manager',
                'role': supplier_role,
                'is_verified': True
            }
        )
        if created:
            supplier_user.set_password('supplier123')
            supplier_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created supplier user: {supplier_user.username}'))
        else:
            self.stdout.write(f'Supplier user already exists: {supplier_user.username}')
            
        # Create or update supplier profile
        supplier_profile, created = Supplier.objects.get_or_create(
            user=supplier_user,
            defaults={
                'company_name': 'ABC Supplies Inc.',
                'code': f'SUP-{random.randint(100, 999)}',
                'business_type': 'Manufacturing',
                'tax_id': f'TAX{random.randint(10000, 99999)}',
                'compliance_score': round(random.uniform(3.5, 5.0), 1),
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created supplier profile for {supplier_user.username}'))
        else:
            self.stdout.write(f'Supplier profile already exists for {supplier_user.username}')
            
        # Create vendor user
        vendor_role = Role.objects.get(id=4)
        vendor_user, created = User.objects.get_or_create(
            username='vendor',
            defaults={
                'email': 'vendor@example.com',
                'first_name': 'Vendor',
                'last_name': 'Shop',
                'role': vendor_role,
                'is_verified': True
            }
        )
        if created:
            vendor_user.set_password('vendor123')
            vendor_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created vendor user: {vendor_user.username}'))
        else:
            self.stdout.write(f'Vendor user already exists: {vendor_user.username}')
            
        # Create or update vendor profile
        vendor_profile, created = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                'shop_name': 'Corner Shop',
                'location': '123 Main St, City',
                'business_license': f'BL-{random.randint(10000, 99999)}'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created vendor profile for {vendor_user.username}'))
        else:
            self.stdout.write(f'Vendor profile already exists for {vendor_user.username}')
            
        # Create warehouse manager user
        warehouse_role = Role.objects.get(id=5)
        warehouse_user, created = User.objects.get_or_create(
            username='warehouse',
            defaults={
                'email': 'warehouse@example.com',
                'first_name': 'Warehouse',
                'last_name': 'Manager',
                'role': warehouse_role,
                'is_verified': True
            }
        )
        if created:
            warehouse_user.set_password('warehouse123')
            warehouse_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created warehouse manager user: {warehouse_user.username}'))
        else:
            self.stdout.write(f'Warehouse manager user already exists: {warehouse_user.username}')
            
        # Create or update warehouse manager profile
        warehouse_profile, created = WarehouseManager.objects.get_or_create(
            user=warehouse_user,
            defaults={
                'warehouse_id': f'WH-{random.randint(100, 999)}',
                'department': 'Logistics'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created warehouse manager profile for {warehouse_user.username}'))
        else:
            self.stdout.write(f'Warehouse manager profile already exists for {warehouse_user.username}')
            
        # Create driver user
        driver_role = Role.objects.get(id=6)
        driver_user, created = User.objects.get_or_create(
            username='driver',
            defaults={
                'email': 'driver@example.com',
                'first_name': 'Delivery',
                'last_name': 'Driver',
                'role': driver_role,
                'is_verified': True
            }
        )
        if created:
            driver_user.set_password('driver123')
            driver_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created driver user: {driver_user.username}'))
        else:
            self.stdout.write(f'Driver user already exists: {driver_user.username}')
            
        # Create or update driver profile
        driver_profile, created = Driver.objects.get_or_create(
            user=driver_user,
            defaults={
                'license_number': f'DL-{random.randint(10000, 99999)}',
                'vehicle_type': 'Delivery Van'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created driver profile for {driver_user.username}'))
        else:
            self.stdout.write(f'Driver profile already exists for {driver_user.username}')
            
        self.stdout.write(self.style.SUCCESS('\nUser creation completed!'))
        self.stdout.write(self.style.SUCCESS('======================='))
        self.stdout.write(self.style.SUCCESS('Default passwords:'))
        self.stdout.write(self.style.SUCCESS('admin: admin123'))
        self.stdout.write(self.style.SUCCESS('user: user123'))
        self.stdout.write(self.style.SUCCESS('supplier: supplier123'))
        self.stdout.write(self.style.SUCCESS('vendor: vendor123'))
        self.stdout.write(self.style.SUCCESS('warehouse: warehouse123'))
        self.stdout.write(self.style.SUCCESS('driver: driver123'))
        self.stdout.write(self.style.SUCCESS('======================='))