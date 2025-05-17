from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from datetime import date, timedelta
from accounts.models import Role, Supplier

class Command(BaseCommand):
    help = 'Create dummy supplier data for testing'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Ensure the supplier role exists
        supplier_role, created = Role.objects.get_or_create(
            id=3,
            defaults={
                "name": "Supplier",
                "description": "Product and service supplier"
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created Supplier role"))
        
        # List of supplier company names
        company_names = [
            "Alpha Supplies Ltd", "Beta Components Inc", "Gamma Electronics Co",
            "Delta Materials", "Epsilon Industrial", "Zeta Manufacturing",
            "Eta Distribution", "Theta Products", "Iota Technologies",
            "Kappa Systems", "Lambda Solutions", "Mu Logistics"
        ]
        
        cities = ["Colombo", "Galle", "Kandy", "Jaffna", "Negombo", "Batticaloa"]
        business_types = ["Manufacturing", "Distribution", "Retail", "Wholesale"]
        
        # Generate 115 suppliers
        dummy_suppliers_created = 0
        for i in range(1, 116):
            # Use deterministic random based on supplier ID
            random.seed(i)
            
            # Create a random but consistent compliance score for this supplier
            compliance_score = round(5.0 + random.random() * 4.0, 1)
            
            username = f"supplier{i}"
            email = f"supplier{i}@example.com"
            
            # Create user if it doesn't exist
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": "Supplier",
                    "last_name": f"{i}",
                    "is_active": True,
                    "role": supplier_role
                }
            )
            
            # Set password for new users
            if user_created:
                user.set_password(f"supplier{i}")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
            
            # Generate company name, code and other supplier-specific data
            company_name = company_names[i % len(company_names)] if i < 100 else f"Supplier {i}"
            code = f"SUP-{i*100 + random.randint(10, 99)}"
            business_type = random.choice(business_types)
            tax_id = f"TAX{i*1000 + random.randint(100, 999)}"
            city = random.choice(cities)
            created_at = timezone.now() - timedelta(days=random.randint(30, 365))
            updated_at = timezone.now() - timedelta(days=random.randint(1, 30))
            
            # Create or update supplier profile
            supplier, supplier_created = Supplier.objects.update_or_create(
                user=user,
                defaults={
                    "company_name": company_name,
                    "street_no": f"{random.randint(1, 999)}",
                    "street_name": f"{random.choice(['Main', 'Park', 'Lake', 'Hill', 'Ocean'])} Street",
                    "city": city,
                    "zipcode": f"{random.randint(10000, 99999)}"[:5],  # Ensure it's 5 digits
                    "code": code,
                    "business_type": business_type,
                    "tax_id": tax_id,
                    "compliance_score": compliance_score,
                    "active": True,
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            )
            
            if supplier_created:
                dummy_suppliers_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created supplier profile: {company_name}"))
            else:
                self.stdout.write(f"Updated supplier profile: {company_name}")
                
        self.stdout.write(self.style.SUCCESS(f"\nCreated {dummy_suppliers_created} new supplier profiles"))
        self.stdout.write(self.style.SUCCESS("All suppliers created with username format: supplier<id>"))
        self.stdout.write(self.style.SUCCESS("All suppliers created with password format: supplier<id>"))
        self.stdout.write(self.style.SUCCESS("Example: Username: supplier100, Password: supplier100"))