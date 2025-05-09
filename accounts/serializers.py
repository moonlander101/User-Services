"""
Serializers for the Supplier model and related endpoints
"""

from rest_framework import serializers
from .models import User, Supplier, Role


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for the Supplier model"""
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Supplier
        fields = [
            'user', 'company_name', 'code', 'business_type', 'tax_id', 
            'compliance_score', 'active', 'created_at', 'updated_at',
            'username', 'email', 'first_name', 'last_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new supplier with associated user"""
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
            'is_active': True
        }
        
        # Get or create supplier role
        supplier_role, _ = Role.objects.get_or_create(
            id=3, 
            defaults={'name': 'Supplier', 'description': 'Supplier role'}
        )
        
        # Create user with supplier role
        user = User.objects.create_user(
            **user_data,
            role=supplier_role,
            is_verified=False
        )
        
        # Generate supplier code if not provided
        if 'code' not in validated_data or not validated_data['code']:
            # Format: S + user_id padded to 4 digits
            validated_data['code'] = f"S{user.id:04d}"
        
        # Create supplier
        supplier = Supplier.objects.create(user=user, **validated_data)
        return supplier


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for supplier information including compliance score"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Supplier
        fields = [
            'user', 'company_name', 'code', 'business_type', 'tax_id', 
            'compliance_score', 'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Add calculated compliance score to the representation"""
        ret = super().to_representation(instance)
        # In a real implementation, this would calculate a compliance score
        # based on various factors like document validation, history, etc.
        # For now we'll use a placeholder with a random value between 0-10
        # with higher values for older IDs (more established suppliers)
        import random
        base_score = min(instance.user.id / 10, 7)  # Older suppliers (lower IDs) get higher base scores
        variation = random.uniform(-2, 2)  # Add some random variation
        compliance_score = max(0, min(10, base_score + variation))  # Keep between 0-10
        ret['compliance_score'] = round(compliance_score, 1)
        return ret