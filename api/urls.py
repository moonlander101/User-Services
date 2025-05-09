from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .supplier_api import SupplierViewSet

# Create a router and register our viewset
router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]