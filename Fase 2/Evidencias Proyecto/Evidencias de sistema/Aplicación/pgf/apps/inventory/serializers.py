# apps/inventory/serializers.py
from rest_framework import serializers
from .models import Repuesto, Stock, MovimientoStock, SolicitudRepuesto, HistorialRepuestoVehiculo


class RepuestoSerializer(serializers.ModelSerializer):
    stock_actual = serializers.SerializerMethodField()
    necesita_reorden = serializers.SerializerMethodField()
    
    class Meta:
        model = Repuesto
        fields = "__all__"
    
    def get_stock_actual(self, obj):
        # Intentar obtener el stock de diferentes maneras
        try:
            # Primero intentar con la relación directa
            if hasattr(obj, 'stock') and obj.stock is not None:
                return obj.stock.cantidad_actual
            # Si no existe, intentar obtenerlo desde la base de datos
            from .models import Stock
            stock = Stock.objects.filter(repuesto=obj).first()
            if stock:
                return stock.cantidad_actual
        except Exception:
            pass
        return 0
    
    def get_necesita_reorden(self, obj):
        # Intentar obtener el stock de diferentes maneras
        try:
            # Primero intentar con la relación directa
            if hasattr(obj, 'stock') and obj.stock is not None:
                return obj.stock.necesita_reorden
            # Si no existe, intentar obtenerlo desde la base de datos
            from .models import Stock
            stock = Stock.objects.filter(repuesto=obj).first()
            if stock:
                return stock.necesita_reorden
        except Exception:
            pass
        return False


class StockSerializer(serializers.ModelSerializer):
    repuesto_nombre = serializers.CharField(source="repuesto.nombre", read_only=True)
    repuesto_codigo = serializers.CharField(source="repuesto.codigo", read_only=True)
    necesita_reorden = serializers.SerializerMethodField()
    
    class Meta:
        model = Stock
        fields = "__all__"
    
    def get_necesita_reorden(self, obj):
        """Calcula si el stock necesita reorden"""
        return obj.necesita_reorden


class MovimientoStockSerializer(serializers.ModelSerializer):
    repuesto_codigo = serializers.CharField(source="repuesto.codigo", read_only=True)
    repuesto_nombre = serializers.CharField(source="repuesto.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True)
    ot_id = serializers.UUIDField(source="ot.id", read_only=True)
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    
    class Meta:
        model = MovimientoStock
        fields = "__all__"


class SolicitudRepuestoSerializer(serializers.ModelSerializer):
    repuesto_codigo = serializers.CharField(source="repuesto.codigo", read_only=True)
    repuesto_nombre = serializers.CharField(source="repuesto.nombre", read_only=True)
    ot_id = serializers.UUIDField(source="ot.id", read_only=True)
    ot_estado = serializers.CharField(source="ot.estado", read_only=True)
    ot_vehiculo_patente = serializers.CharField(source="ot.vehiculo.patente", read_only=True)
    ot_vehiculo_id = serializers.UUIDField(source="ot.vehiculo.id", read_only=True)
    ot_tipo = serializers.CharField(source="ot.tipo", read_only=True)
    ot_prioridad = serializers.CharField(source="ot.prioridad", read_only=True)
    solicitante_nombre = serializers.CharField(source="solicitante.get_full_name", read_only=True)
    aprobador_nombre = serializers.CharField(source="aprobador.get_full_name", read_only=True, allow_null=True)
    entregador_nombre = serializers.CharField(source="entregador.get_full_name", read_only=True, allow_null=True)
    
    class Meta:
        model = SolicitudRepuesto
        fields = "__all__"


class HistorialRepuestoVehiculoSerializer(serializers.ModelSerializer):
    repuesto_codigo = serializers.CharField(source="repuesto.codigo", read_only=True)
    repuesto_nombre = serializers.CharField(source="repuesto.nombre", read_only=True)
    vehiculo_patente = serializers.CharField(source="vehiculo.patente", read_only=True)
    ot_id = serializers.UUIDField(source="ot.id", read_only=True, allow_null=True)
    
    class Meta:
        model = HistorialRepuestoVehiculo
        fields = "__all__"

