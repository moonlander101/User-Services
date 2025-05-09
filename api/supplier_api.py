"""
API endpoints for suppliers in the Auth Service
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from accounts.models import User, Supplier
from accounts.serializers import SupplierSerializer, SupplierDetailSerializer
from utils.kafka_utils import supplier_producer
import logging

logger = logging.getLogger(__name__)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing suppliers
    """
    permission_classes = [AllowAny]
    serializer_class = SupplierSerializer
    
    def get_queryset(self):
        """
        Get the list of suppliers, filtered by active status if specified
        """
        queryset = Supplier.objects.select_related('user')
        
        # Filter by active status if specified
        active = self.request.query_params.get('active')
        if active is not None:
            is_active = active.lower() == 'true'
            queryset = queryset.filter(active=is_active)
            
        return queryset
    
    def get_serializer_class(self):
        """
        Return different serializer based on the action
        """
        if self.action == 'info':
            return SupplierDetailSerializer
        return SupplierSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new supplier
        """
        response = super().create(request, *args, **kwargs)
        
        # Publish supplier created event to Kafka
        if response.status_code == status.HTTP_201_CREATED:
            supplier_id = response.data.get('user', {}).get('id')
            supplier_producer.publish_supplier_created(supplier_id, response.data)
            
        return response
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing supplier
        """
        response = super().update(request, *args, **kwargs)
        
        # Publish supplier updated event to Kafka
        if response.status_code == status.HTTP_200_OK:
            supplier_id = response.data.get('user', {}).get('id')
            supplier_producer.publish_supplier_updated(supplier_id, response.data)
            
        return response
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a supplier
        """
        instance = self.get_object()
        supplier_id = instance.user.id
        
        response = super().destroy(request, *args, **kwargs)
        
        # Publish supplier deleted event to Kafka
        if response.status_code == status.HTTP_204_NO_CONTENT:
            supplier_producer.publish_supplier_deleted(supplier_id)
            
        return response
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """
        Get the count of suppliers, filtered by active status if specified
        """
        count = self.get_queryset().count()
        return Response({'count': count})
    
    @action(detail=True, methods=['get'])
    def info(self, request, pk=None):
        """
        Get detailed information about a supplier including compliance score
        """
        try:
            supplier = self.get_object()
            serializer = self.get_serializer(supplier)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving supplier info: {str(e)}")
            return Response(
                {"detail": "Failed to retrieve supplier information"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )