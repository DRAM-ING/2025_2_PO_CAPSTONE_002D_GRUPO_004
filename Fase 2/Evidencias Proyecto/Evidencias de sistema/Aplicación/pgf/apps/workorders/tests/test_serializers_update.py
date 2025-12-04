# apps/workorders/tests/test_serializers_update.py
"""
Tests específicos para el método update de OrdenTrabajoSerializer.
Cubre los casos críticos que fueron corregidos recientemente.
"""

import pytest
from decimal import Decimal
from apps.workorders.serializers import OrdenTrabajoSerializer
from apps.workorders.models import OrdenTrabajo, ItemOT
from apps.inventory.models import Repuesto


@pytest.mark.django_db
class TestOrdenTrabajoSerializerUpdate:
    """Tests para el método update de OrdenTrabajoSerializer"""

    def test_update_without_vehiculo(self, orden_trabajo, jefe_taller_user):
        """
        Test que vehiculo no es requerido en actualizaciones.
        Este es el caso crítico que causaba errores antes.
        """
        data = {
            "motivo": "Motivo actualizado",
            "prioridad": "ALTA",
            "responsable": jefe_taller_user.id,
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        assert updated_ot.motivo == "Motivo actualizado"
        assert updated_ot.prioridad == "ALTA"
        # El vehículo original debe mantenerse
        assert updated_ot.vehiculo == orden_trabajo.vehiculo

    def test_update_preserves_responsable_if_not_provided(self, orden_trabajo, jefe_taller_user):
        """
        Test que responsable se preserva si no se proporciona en la actualización.
        """
        # Asegurar que la OT tiene un responsable
        orden_trabajo.responsable = jefe_taller_user
        orden_trabajo.save()
        
        data = {
            "motivo": "Motivo actualizado",
            "prioridad": "ALTA",
            # No incluir responsable
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        # El responsable original debe mantenerse
        assert updated_ot.responsable == jefe_taller_user

    def test_update_with_items_data_replaces_all_items(self, orden_trabajo, jefe_taller_user, repuesto):
        """
        Test que items_data reemplaza todos los items existentes.
        """
        # Crear items existentes
        ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="SERVICIO",
            descripcion="Servicio antiguo",
            cantidad=1,
            costo_unitario=Decimal("100.00")
        )
        ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="REPUESTO",
            descripcion="Repuesto antiguo",
            cantidad=2,
            costo_unitario=Decimal("50.00")
        )
        
        assert orden_trabajo.items.count() == 2
        
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Nuevo servicio",
                    "cantidad": 3,
                    "costo_unitario": "200.00"
                },
                {
                    "tipo": "REPUESTO",
                    "descripcion": "Nuevo repuesto",
                    "cantidad": 1,
                    "costo_unitario": "150.00",
                    "repuesto": str(repuesto.id)
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        # Los items antiguos deben ser eliminados
        assert updated_ot.items.count() == 2
        # Verificar que son los nuevos items
        items = list(updated_ot.items.all())
        assert items[0].descripcion == "Nuevo servicio"
        assert items[1].descripcion == "Nuevo repuesto"

    def test_update_items_data_validates_required_fields(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data valida campos requeridos.
        """
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    # Falta descripcion
                    "cantidad": 1,
                    "costo_unitario": "100.00"
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is False
        assert "items_data[0].descripcion" in str(serializer.errors)

    def test_update_items_data_validates_cantidad(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data valida que cantidad sea mayor a 0.
        """
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 0,  # Inválido
                    "costo_unitario": "100.00"
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is False
        # El formato del error es {'items_data': [{'cantidad': [...]}]}
        assert "cantidad" in str(serializer.errors) and "items_data" in str(serializer.errors)

    def test_update_items_data_validates_costo_unitario(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data valida costo_unitario.
        """
        # Test costo negativo
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "-10.00"  # Inválido
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is False
        # El formato del error es {'items_data': [{'costo_unitario': [...]}]}
        assert "costo_unitario" in str(serializer.errors) and "items_data" in str(serializer.errors)

    def test_update_items_data_handles_string_costo_unitario(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data acepta costo_unitario como string.
        """
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": "100.50"  # String
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        item = updated_ot.items.first()
        assert item.costo_unitario == Decimal("100.50")

    def test_update_items_data_handles_number_costo_unitario(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data acepta costo_unitario como número.
        """
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": [
                {
                    "tipo": "SERVICIO",
                    "descripcion": "Servicio test",
                    "cantidad": 1,
                    "costo_unitario": 100.50  # Number
                }
            ]
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        item = updated_ot.items.first()
        assert item.costo_unitario == Decimal("100.50")

    def test_update_rejects_empty_items_data(self, orden_trabajo, jefe_taller_user):
        """
        Test que items_data no puede estar vacío.
        """
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "items_data": []  # Vacío
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is False
        assert "items_data" in str(serializer.errors)

    def test_update_without_items_data_preserves_existing_items(self, orden_trabajo, jefe_taller_user):
        """
        Test que si no se proporciona items_data, los items existentes se preservan.
        """
        # Crear items existentes
        item1 = ItemOT.objects.create(
            ot=orden_trabajo,
            tipo="SERVICIO",
            descripcion="Servicio existente",
            cantidad=1,
            costo_unitario=Decimal("100.00")
        )
        
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            # No incluir items_data
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        # Los items existentes deben mantenerse
        assert updated_ot.items.count() == 1
        assert updated_ot.items.first().id == item1.id

    def test_update_vehiculo_is_ignored(self, db, vehiculo, supervisor_user, jefe_taller_user):
        """
        Test que vehiculo no se puede cambiar en actualizaciones.
        """
        from apps.workorders.models import OrdenTrabajo
        from datetime import datetime
        
        # Crear un vehículo diferente para la OT
        from apps.vehicles.models import Vehiculo, Marca
        marca = Marca.objects.create(nombre="TestMarca", activa=True)
        otro_vehiculo = Vehiculo.objects.create(
            patente="TEST02",
            marca=marca,
            modelo="Modelo Test",
            anio=2020,
            zona="ZONA_TEST",
            sucursal="SUCURSAL_TEST"
        )
        
        # Crear OT con otro_vehiculo
        orden_trabajo = OrdenTrabajo.objects.create(
            vehiculo=otro_vehiculo,
            supervisor=supervisor_user,
            jefe_taller=jefe_taller_user,
            responsable=supervisor_user,
            motivo="Prueba de OT",
            estado=OrdenTrabajo.ESTADOS[0][0],  # ABIERTA
            zona="ZONA_TEST",
            apertura=datetime.now()
        )
        
        original_vehiculo = orden_trabajo.vehiculo
        
        data = {
            "motivo": "Motivo actualizado",
            "responsable": jefe_taller_user.id,
            "vehiculo": vehiculo.id,  # Intentar cambiar vehículo
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is True, f"Errores: {serializer.errors}"
        
        updated_ot = serializer.save()
        # El vehículo original debe mantenerse (no debe cambiar a vehiculo)
        assert updated_ot.vehiculo == original_vehiculo
        assert updated_ot.vehiculo != vehiculo

    def test_update_requires_responsable_if_not_present(self, orden_trabajo):
        """
        Test que si la OT no tiene responsable y no se proporciona, falla.
        """
        # Asegurar que la OT no tiene responsable
        orden_trabajo.responsable = None
        orden_trabajo.save()
        
        data = {
            "motivo": "Motivo actualizado",
            "prioridad": "ALTA",
            # No incluir responsable
        }
        serializer = OrdenTrabajoSerializer(orden_trabajo, data=data, partial=True)
        assert serializer.is_valid() is False
        assert "responsable" in str(serializer.errors)

