import re

import jwt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import json
import uuid
from django.utils import timezone
from datetime import datetime, timedelta
import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User, PasswordResetToken, Supplier, Vendor, WarehouseManager, Driver

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Password validation - at least 8 chars, 1 uppercase, 1 lowercase, 1 number
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

# JWT token generation
def generate_jwt_token(user):
    """Generate JWT token for user authentication"""
    # Create token payload
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role_id': getattr(user, 'role_id', 2),
        'exp': datetime.utcnow() + timedelta(days=7)  # 7 days expiration
    }

    if user.role_id == 6:  # Driver
        try:
            driver = Driver.objects.get(user=user)
            payload['vehicle_id'] = driver.vehicle_id
        except Driver.DoesNotExist:
            pass
    
    elif user.role_id == 5:  # Warehouse Manager
        try:
            warehouse_manager = WarehouseManager.objects.get(user=user)
            payload['warehouse_id'] = warehouse_manager.warehouse_id
        except WarehouseManager.DoesNotExist:
            pass
    
    # Generate token
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm='HS256'
    )
    
    return token

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def register_view(request):
    data = request.data
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    role_id = data.get('role_id', 2)  # Default to regular user role
    phone = data.get('phone', '')
    
    # Extended validation
    if not username or not email or not password:
        return Response({
            'success': False,
            'message': 'Please provide username, email and password'
        }, status=400)
    
    # Email format validation
    if not EMAIL_REGEX.match(email):
        return Response({
            'success': False,
            'message': 'Invalid email format'
        }, status=400)
    
    # Password strength validation
    if not PASSWORD_REGEX.match(password):
        return Response({
            'success': False,
            'message': 'Password must be at least 8 characters and include uppercase, lowercase, and numbers'
        }, status=400)

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'message': 'Username already exists'
        }, status=400)

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'message': 'Email already exists'
        }, status=400)
    
    # Create new user using Django's User model create_user method
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,  # create_user handles password hashing
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    
    # Set role_id
    user.role_id = role_id
    user.save()
    
    # Create role-specific profile with all required fields
    try:
        if role_id == 3:  # Supplier
            # Get supplier-specific fields
            company_name = data.get('company_name')
            street_no = data.get('street_no')
            street_name = data.get('street_name')
            city = data.get('city')
            zipcode = data.get('zipcode')
            code = data.get('code', f"SUP-{user.id:03d}")  # Generate code if not provided
            business_type = data.get('business_type')
            tax_id = data.get('tax_id')
            
            # Validate required fields
            if not company_name or not business_type or not tax_id:
                user.delete()  # Clean up the user if profile creation fails
                return Response({
                    'success': False,
                    'message': 'Missing required fields for Supplier profile'
                }, status=400)
            
            # Create supplier profile
            Supplier.objects.create(
                user_id=user.id,
                company_name=company_name,
                street_no=street_no,
                street_name=street_name,
                city=city,
                zipcode=zipcode,
                code=code,
                business_type=business_type,
                tax_id=tax_id
            )
            
        elif role_id == 4:  # Vendor
            # Get vendor-specific fields
            shop_name = data.get('shop_name')
            location = data.get('location')
            business_license = data.get('business_license')
            
            # Validate required fields
            if not shop_name or not location or not business_license:
                user.delete()
                return Response({
                    'success': False,
                    'message': 'Missing required fields for Vendor profile'
                }, status=400)
            
            # Create vendor profile
            Vendor.objects.create(
                user_id=user.id,
                shop_name=shop_name,
                location=location,
                business_license=business_license
            )
            
        elif role_id == 5:  # Warehouse Manager
            # Get warehouse manager-specific fields
            warehouse_id = data.get('warehouse_id')
            department = data.get('department')
            
            # Validate required fields
            if not warehouse_id or not department:
                user.delete()
                return Response({
                    'success': False,
                    'message': 'Missing required fields for Warehouse Manager profile'
                }, status=400)
            
            # Create warehouse manager profile
            WarehouseManager.objects.create(
                user_id=user.id,
                warehouse_id=warehouse_id,
                department=department
            )
            
        elif role_id == 6:  # Driver
            # Get driver-specific fields
            license_number = data.get('license_number')
            vehicle_type = data.get('vehicle_type')
            vehicle_id = data.get('vehicle_id')  # New field we added
            
            # Validate required fields
            if not license_number or not vehicle_type:
                user.delete()
                return Response({
                    'success': False,
                    'message': 'Missing required fields for Driver profile'
                }, status=400)
            
            # Create driver profile with vehicle_id
            Driver.objects.create(
                user_id=user.id,
                license_number=license_number,
                vehicle_type=vehicle_type,
                vehicle_id=vehicle_id  # This is the new field we're adding
            )
            
    except Exception as e:
        # If profile creation fails, clean up the user to maintain data integrity
        user.delete()
        return Response({
            'success': False,
            'message': f'Error creating user profile: {str(e)}'
        }, status=500)
    
    return Response({
        'success': True,
        'message': 'User registered successfully',
        'user_id': user.id
    })

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')

    if (not username and not email) or not password:
        return Response({
            'success': False,
            'message': 'Please provide email/username and password'
        }, status=400)
    
    # Try to authenticate with username or email
    user = None
    if username:
        user = authenticate(request, username=username, password=password)
    elif email:
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    
    # Check if user is active
    if user and not user.is_active:
        return Response({
            'success': False, 
            'message': 'Account is inactive'
        }, status=401)
    
    if user is not None:
        login(request, user)
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role_id': getattr(user, 'role_id', 2),
                'role': getattr(user.role, 'name', 'Regular User'),
            }
        })
    else:
        return Response({
            'success': False,
            'message': 'Invalid credentials'
        }, status=401)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # JWT doesn't need server-side invalidation
    # Just instruct the client to remove the token
    logout(request)
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_view(request):
    user = request.user
    
    # Get role-specific data if available
    role_data = {}
    role_id = getattr(user, 'role_id', 2)
    
    try:
        if role_id == 3:  # Supplier
            supplier = Supplier.objects.get(user_id=user.id)
            role_data = {
                'company_name': supplier.company_name,
                'street_no': supplier.street_no,
                'street_name': supplier.street_name,
                'city': supplier.city,
                'zipcode': supplier.zipcode,
                'code': supplier.code,
                'business_type': supplier.business_type,
                'tax_id': supplier.tax_id,
                'compliance_score': supplier.compliance_score,
                'active': supplier.active,
                'created_at': supplier.created_at,
                'updated_at': supplier.updated_at
            }
        elif role_id == 4:  # Vendor
            vendor = Vendor.objects.get(user_id=user.id)
            role_data = {
                'shop_name': vendor.shop_name,
                'location': vendor.location,
                'business_license': vendor.business_license
            }
        elif role_id == 5:  # Warehouse Manager
            warehouse_manager = WarehouseManager.objects.get(user_id=user.id)
            role_data = {
                'warehouse_id': warehouse_manager.warehouse_id,
                'department': warehouse_manager.department
            }
        elif role_id == 6:  # Driver
            driver = Driver.objects.get(user_id=user.id)
            role_data = {
                'license_number': driver.license_number,
                'vehicle_type': driver.vehicle_type,
                'vehicle_id': driver.vehicle_id
            }
    except Exception as e:
        # Log the error for debugging
        print(f"Error getting role data: {str(e)}")
        # No role-specific data found
        pass
    
    return Response({
        'success': True,
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_id': role_id,
            'role': getattr(user.role, 'name', 'Regular User'),
            'is_verified': getattr(user, 'is_verified', False),
            'phone': user.phone,  # Added phone field
            'role_data': role_data
        }
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    user = request.user
    data = request.data
    
    # Update user fields if provided
    if 'username' in data:
        # Check if username is already taken by another user
        if User.objects.exclude(id=user.id).filter(username=data['username']).exists():
            return Response({
                'success': False,
                'message': 'Username already exists'
            }, status=400)
        user.username = data['username']
        
    if 'email' in data:
        # Validate email format
        if not EMAIL_REGEX.match(data['email']):
            return Response({
                'success': False,
                'message': 'Invalid email format'
            }, status=400)
            
        # Check if email is already taken by another user
        if User.objects.exclude(id=user.id).filter(email=data['email']).exists():
            return Response({
                'success': False,
                'message': 'Email already exists'
            }, status=400)
        user.email = data['email']
        
    if 'first_name' in data:
        user.first_name = data['first_name']
        
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    user.save()
    
    # Update role-specific data if provided
    role_id = getattr(user, 'role_id', 2)
    role_data = data.get('role_data', {})
    
    if role_data:
        try:
            if role_id == 3:  # Supplier
                supplier = Supplier.objects.get(user_id=user.id)
                if 'company_name' in role_data:
                    supplier.company_name = role_data['company_name']
                if 'contact_number' in role_data:
                    supplier.contact_number = role_data['contact_number']
                supplier.save()
            elif role_id == 4:  # Vendor
                vendor = Vendor.objects.get(user_id=user.id)
                if 'store_name' in role_data:
                    vendor.store_name = role_data['store_name']
                if 'business_address' in role_data:
                    vendor.business_address = role_data['business_address']
                vendor.save()
            # Add other role-specific data updates
        except:
            # Role-specific data not found
            pass
    
    return Response({
        'success': True,
        'message': 'Profile updated successfully'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change_view(request):
    data = request.data
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return Response({
            'success': False,
            'message': 'Please provide both old and new passwords'
        }, status=400)
    
    user = request.user
    
    # Use Django's check_password
    if not user.check_password(old_password):
        return Response({
            'success': False,
            'message': 'Incorrect old password'
        }, status=401)
    
    # Update password with Django's set_password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_view(request):
    data = request.data
    email = data.get('email', '')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Please provide email address'
        }, status=400)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        
        # Save token in the database
        PasswordResetToken.objects.filter(user=user).delete()  # Remove old tokens
        reset_token = PasswordResetToken.objects.create(user=user, token=token)
        
        # Create reset URL - Use getattr to provide a default value if FRONTEND_URL is not set
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/"
        
        # Create email message
        subject = "Password Reset Request"
        message = f"""Hello {user.username},

You requested a password reset for your account. Please click the link below to reset your password:

{reset_url}

If you didn't request this reset, you can safely ignore this email.

Thank you,
The Support Team"""
        
        # Default from email with fallback
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        
        # Send email
        send_mail(subject, message, from_email, [user.email])
        
        return Response({
            'success': True,
            'message': 'Password reset instructions sent to your email'
        })
    except User.DoesNotExist:
        # For security reasons, don't reveal that the email doesn't exist
        return Response({
            'success': True,
            'message': 'Password reset instructions sent to your email if account exists'
        })

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_confirm_view(request, uidb64, token):
    """Handle the password reset confirmation"""
    try:
        # Decode the user id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Verify token
        reset_token = PasswordResetToken.objects.get(user=user, token=token)
        if not reset_token.is_valid():
            return Response({
                'success': False,
                'message': 'Password reset link is invalid or has expired'
            }, status=400)
        
        # Get new password
        data = request.data
        new_password = data.get('new_password', '')
        
        if not new_password:
            return Response({
                'success': False,
                'message': 'Please provide a new password'
            }, status=400)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Delete the used token
        reset_token.delete()
        
        return Response({
            'success': True,
            'message': 'Password has been reset successfully'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Password reset link is invalid or has expired'
        }, status=400)

# Admin specific views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_all_users(request):
    """Admin endpoint to get all users"""
    user = request.user
    
    # Check if user is admin (role_id = 1)
    if getattr(user, 'role_id', 0) != 1:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    # Get query parameters for pagination
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    role_id = request.GET.get('role_id')
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Query all users
    users_query = User.objects.all()
    
    # Filter by role_id if provided
    if role_id:
        users_query = users_query.filter(role_id=role_id)
    
    # Get total count for pagination
    total_count = users_query.count()
    
    # Get paginated users
    users = users_query[offset:offset+limit]
    
    # Format user data
    user_list = []
    for user in users:
        # Get role-specific data if available
        role_data = {}
        role_id = getattr(user, 'role_id', 2)
        
        try:
            if role_id == 3:  # Supplier
                supplier = Supplier.objects.get(user_id=user.id)
                role_data = {
                    'company_name': supplier.company_name,
                    'contact_number': supplier.contact_number,
                }
            elif role_id == 4:  # Vendor
                vendor = Vendor.objects.get(user_id=user.id)
                role_data = {
                    'store_name': vendor.store_name,
                    'business_address': vendor.business_address,
                }
            # Add other role-specific data retrieval
        except:
            pass
            
        user_list.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_id': role_id,
            'role': getattr(user.role, 'name', 'Regular User'),
            'is_verified': getattr(user, 'is_verified', False),
            'role_data': role_data
        })
    
    return Response({
        'success': True,
        'users': user_list,
        'pagination': {
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit  # Ceiling division
        }
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_user(request, user_id):
    """Admin endpoint to update user"""
    admin = request.user
    
    # Check if user is admin (role_id = 1)
    if getattr(admin, 'role_id', 0) != 1:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        user = User.objects.get(pk=user_id)
        data = request.data
        
        # Update fields if provided
        if 'email' in data:
            # Validate email format
            if not EMAIL_REGEX.match(data['email']):
                return Response({
                    'success': False,
                    'message': 'Invalid email format'
                }, status=400)
                
            user.email = data['email']
        
        if 'role_id' in data:
            old_role_id = user.role_id
            new_role_id = data['role_id']
            user.role_id = new_role_id
            
            # Handle role change - create new role-specific record if needed
            if old_role_id != new_role_id:
                if new_role_id == 3 and not Supplier.objects.filter(user_id=user.id).exists():
                    Supplier.objects.create(user_id=user.id)
                elif new_role_id == 4 and not Vendor.objects.filter(user_id=user.id).exists():
                    Vendor.objects.create(user_id=user.id)
                # Add other role creations as needed
        
        if 'is_verified' in data:
            user.is_verified = data['is_verified']
            
        if 'username' in data:
            # Check for uniqueness
            if User.objects.exclude(id=user.id).filter(username=data['username']).exists():
                return Response({
                    'success': False,
                    'message': 'Username already exists'
                }, status=400)
            user.username = data['username']
            
        if 'first_name' in data:
            user.first_name = data['first_name']
            
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        user.save()
        
        # Update role-specific data if provided
        role_data = data.get('role_data', {})
        if role_data:
            try:
                role_id = user.role_id
                if role_id == 3:  # Supplier
                    supplier = Supplier.objects.get(user_id=user.id)
                    if 'company_name' in role_data:
                        supplier.company_name = role_data['company_name']
                    if 'contact_number' in role_data:
                        supplier.contact_number = role_data['contact_number']
                    supplier.save()
                elif role_id == 4:  # Vendor
                    vendor = Vendor.objects.get(user_id=user.id)
                    if 'store_name' in role_data:
                        vendor.store_name = role_data['store_name']
                    if 'business_address' in role_data:
                        vendor.business_address = role_data['business_address']
                    vendor.save()
                # Add other role-specific data updates
            except:
                # Role-specific data not found
                pass
        
        return Response({
            'success': True,
            'message': 'User updated successfully'
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_user(request, user_id):
    """Admin endpoint to delete user"""
    admin = request.user
    
    # Check if user is admin (role_id = 1)
    if getattr(admin, 'role_id', 0) != 1:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        user = User.objects.get(pk=user_id)
        
        # Prevent admin from deleting themselves
        if user.id == admin.id:
            return Response({
                'success': False,
                'message': 'Cannot delete your own account'
            }, status=400)
        
        # Role-specific tables will be deleted automatically if CASCADE is set on foreign key
        user.delete()
        
        return Response({
            'success': True,
            'message': 'User deleted successfully'
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=404)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def register_supplier_view(request):
    data = request.data
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    phone = data.get('phone', '')
    
    # Supplier-specific fields
    company_name = data.get('company_name', '')
    street_no = data.get('street_no', '')
    street_name = data.get('street_name', '')
    city = data.get('city', '')
    zipcode = data.get('zipcode', '')
    business_type = data.get('business_type', '')
    tax_id = data.get('tax_id', '')
    
    # Extended validation
    if not username or not email or not password:
        return Response({
            'success': False,
            'message': 'Please provide username, email and password'
        }, status=400)
    
    # Supplier-specific validation
    if not company_name:
        return Response({
            'success': False,
            'message': 'Company name is required for suppliers'
        }, status=400)
    
    # Email format validation
    if not EMAIL_REGEX.match(email):
        return Response({
            'success': False,
            'message': 'Invalid email format'
        }, status=400)
    
    # Password strength validation
    if not PASSWORD_REGEX.match(password):
        return Response({
            'success': False,
            'message': 'Password must be at least 8 characters and include uppercase, lowercase, and numbers'
        }, status=400)

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'message': 'Username already exists'
        }, status=400)

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'message': 'Email already exists'
        }, status=400)
    
    # Create new user 
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    
    # Set role_id to Supplier (3)
    user.role_id = 3
    user.save()

    
    code = data.get('code', f"SUP-{user.id:03d}")
    
    # Create supplier profile
    supplier = Supplier.objects.create(
        user=user,
        company_name=company_name,
        street_no=street_no,
        street_name=street_name,
        city=city,
        zipcode=zipcode,
        code=code,
        business_type=business_type,
        tax_id=tax_id
    )
    
    # Generate JWT token
    token = generate_jwt_token(user)
    
    return Response({
        'success': True,
        'message': 'Supplier registered successfully',
        'token': token,
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role_id': user.role_id,
            'role': getattr(user.role, 'name', 'Supplier'),
        }
    })

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def register_customer_view(request):
    data = request.data
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    
    # Vendor-specific fields
    shop_name = data.get('shop_name', '')
    location = data.get('location', '')
    business_license = data.get('business_license', '')
    
    # Extended validation
    if not username or not email or not password:
        return Response({
            'success': False,
            'message': 'Please provide username, email and password'
        }, status=400)
    
    # Vendor-specific validation
    if not shop_name:
        return Response({
            'success': False,
            'message': 'Shop name is required for vendors'
        }, status=400)
    
    # Email format validation
    if not EMAIL_REGEX.match(email):
        return Response({
            'success': False,
            'message': 'Invalid email format'
        }, status=400)
    
    # Password strength validation
    if not PASSWORD_REGEX.match(password):
        return Response({
            'success': False,
            'message': 'Password must be at least 8 characters and include uppercase, lowercase, and numbers'
        }, status=400)

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'message': 'Username already exists'
        }, status=400)

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'message': 'Email already exists'
        }, status=400)
    
    # Create new user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Set role_id to Vendor (4)
    user.role_id = 4
    user.save()
    
    # Create vendor profile
    vendor = Vendor.objects.create(
        user=user,
        shop_name=shop_name,
        location=location,
        business_license=business_license
    )
    
    # Generate JWT token
    token = generate_jwt_token(user)
    
    return Response({
        'success': True,
        'message': 'Vendor registered successfully',
        'token': token,
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role_id': user.role_id,
            'role': getattr(user.role, 'name', 'Vendor'),
        }
    })

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_all_drivers_view(request):
    """
    Get all drivers with their vehicle IDs, usernames, and user IDs
    Only accessible to authenticated users (may want to restrict further based on role)
    """
    # Query all drivers with their related user information
    drivers = Driver.objects.select_related('user').all()
    
    # Format the response data
    drivers_data = []
    for driver in drivers:
        drivers_data.append({
            'user_id': driver.user.id,
            'username': driver.user.username,
            'vehicle_id': driver.vehicle_id,
            'vehicle_type': driver.vehicle_type,
            'license_number': driver.license_number
        })
    
    return Response({
        'success': True,
        'count': len(drivers_data),
        'drivers': drivers_data
    })