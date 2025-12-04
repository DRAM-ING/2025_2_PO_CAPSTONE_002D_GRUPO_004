"""
Tests para los permisos de vehículos.
"""

import pytest
from unittest.mock import Mock
from rest_framework.test import APIClient
from apps.vehicles.models import Vehiculo
from apps.vehicles.permissions import VehiclePermission
from apps.drivers.models import Chofer


@pytest.mark.permission
class TestVehiclePermission:
    """Tests para VehiclePermission"""
    
    def test_unauthenticated_user_denied(self):
        """Test que usuario no autenticado es denegado"""
        permission = VehiclePermission()
        request = Mock()
        request.user = None
        
        assert permission.has_permission(request, None) is False
    
    def test_safe_methods_allowed_for_authorized_roles(self, admin_user, supervisor_user, mecanico_user):
        """Test que métodos seguros están permitidos para roles autorizados"""
        permission = VehiclePermission()
        
        for user in [admin_user, supervisor_user, mecanico_user]:
            request = Mock()
            request.user = user
            # is_authenticated es una propiedad
            request.method = 'GET'
            
            assert permission.has_permission(request, None) is True
    
    def test_post_create_allowed_for_jefe_taller(self, jefe_taller_user):
        """Test que JEFE_TALLER puede crear vehículos"""
        permission = VehiclePermission()
        request = Mock()
        request.user = jefe_taller_user
        # is_authenticated es una propiedad
        request.method = 'POST'
        
        view = Mock()
        view.action = 'create'
        
        assert permission.has_permission(request, view) is True
    
    def test_post_create_denied_for_mecanico(self, mecanico_user):
        """Test que MECANICO no puede crear vehículos"""
        permission = VehiclePermission()
        request = Mock()
        request.user = mecanico_user
        # is_authenticated es una propiedad
        request.method = 'POST'
        
        view = Mock()
        view.action = 'create'
        
        assert permission.has_permission(request, view) is False
    
    def test_put_update_allowed_for_coordinador_zona(self, coordinador_user):
        """Test que COORDINADOR_ZONA puede actualizar vehículos"""
        permission = VehiclePermission()
        request = Mock()
        request.user = coordinador_user
        # is_authenticated es una propiedad
        request.method = 'PUT'
        
        view = Mock()
        view.action = 'update'
        
        assert permission.has_permission(request, view) is True
    
    def test_delete_allowed_only_for_admin(self, admin_user, jefe_taller_user):
        """Test que solo ADMIN puede eliminar vehículos"""
        permission = VehiclePermission()
        
        # Admin puede eliminar
        request = Mock()
        request.user = admin_user
        # is_authenticated es una propiedad
        request.method = 'DELETE'
        assert permission.has_permission(request, None) is True
        
        # Jefe de taller no puede eliminar
        request.user = jefe_taller_user
        assert permission.has_permission(request, None) is False
    
    def test_ingreso_action_allowed_for_guardia(self, guardia_user):
        """Test que GUARDIA puede registrar ingreso"""
        permission = VehiclePermission()
        request = Mock()
        request.user = guardia_user
        # is_authenticated es una propiedad
        request.method = 'POST'
        
        view = Mock()
        view.action = 'ingreso'
        
        assert permission.has_permission(request, view) is True
    
    def test_chofer_can_only_view_assigned_vehicle(self, chofer_user, vehiculo, db):
        """Test que CHOFER solo puede ver su vehículo asignado"""
        permission = VehiclePermission()
        
        # Asegurar que chofer_user tiene RUT
        if not chofer_user.rut:
            chofer_user.rut = "44444444-4"
            chofer_user.save()
        
        # Crear chofer con vehículo asignado
        # El RUT debe coincidir exactamente (sin guión en la BD)
        rut_sin_guion = chofer_user.rut.replace("-", "")
        chofer = Chofer.objects.create(
            rut=rut_sin_guion,
            nombre_completo="Test Chofer",
            activo=True,
            vehiculo_asignado=vehiculo
        )
        
        request = Mock()
        request.user = chofer_user
        # is_authenticated es una propiedad
        # El RUT debe coincidir exactamente (sin guión) para que el permiso funcione
        request.user.rut = rut_sin_guion  # Usar el mismo RUT sin guión que el chofer
        request.method = 'GET'
        
        # Puede ver su vehículo asignado
        # El permiso busca chofer por RUT, así que debe funcionar
        result = permission.has_object_permission(request, None, vehiculo)
        # Si el chofer está activo y tiene vehículo asignado, debería poder verlo
        assert result is True
        
        # No puede ver otro vehículo
        otro_vehiculo = Vehiculo.objects.create(
            patente="OTRO01",
            marca=vehiculo.marca,
            modelo="Otro Modelo",
            anio=2020,
            tipo=vehiculo.tipo,
            estado=vehiculo.estado,
            supervisor=vehiculo.supervisor,
            estado_operativo="OPERATIVO"
        )
        assert permission.has_object_permission(request, None, otro_vehiculo) is False
    
    def test_chofer_cannot_modify_vehicle(self, chofer_user, vehiculo, db):
        """Test que CHOFER no puede modificar vehículos"""
        permission = VehiclePermission()
        
        chofer = Chofer.objects.create(
            rut=chofer_user.rut.replace("-", ""),  # RUT sin guión
            nombre_completo="Test Chofer",
            activo=True,
            vehiculo_asignado=vehiculo
        )
        
        request = Mock()
        request.user = chofer_user
        # is_authenticated es una propiedad
        request.user.rut = chofer_user.rut
        request.method = 'PUT'
        
        assert permission.has_object_permission(request, None, vehiculo) is False
    
    def test_jefe_taller_cannot_delete_vehicle(self, jefe_taller_user, vehiculo):
        """Test que JEFE_TALLER no puede eliminar vehículos"""
        permission = VehiclePermission()
        
        request = Mock()
        request.user = jefe_taller_user
        # is_authenticated es una propiedad
        request.method = 'DELETE'
        
        assert permission.has_object_permission(request, None, vehiculo) is False

