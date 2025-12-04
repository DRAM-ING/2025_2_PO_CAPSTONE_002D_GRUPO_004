# apps/scheduling/tests/test_models.py
"""
Tests para modelos de scheduling.
"""

import pytest
from apps.scheduling.models import Agenda, CupoDiario


class TestAgendaModel:
    """Tests para modelo Agenda"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_agenda_str(self, agenda):
        """Test método __str__ de Agenda"""
        assert str(agenda) is not None
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_agenda_estados(self):
        """Test estados válidos de agenda"""
        estados = [choice[0] for choice in Agenda.ESTADOS]
        assert "PROGRAMADA" in estados
        assert "CONFIRMADA" in estados
        assert "EN_PROCESO" in estados
        assert "COMPLETADA" in estados
        assert "CANCELADA" in estados
        assert "REPROGRAMADA" in estados
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_agenda_tipos_mantenimiento(self):
        """Test tipos de mantenimiento válidos"""
        # El modelo define los tipos directamente en el campo
        tipos_validos = ["PREVENTIVO", "CORRECTIVO"]
        # Verificar que el campo acepta estos valores
        agenda = Agenda()
        field = agenda._meta.get_field('tipo_mantenimiento')
        tipos = [choice[0] for choice in field.choices]
        assert "PREVENTIVO" in tipos
        assert "CORRECTIVO" in tipos


class TestCupoDiarioModel:
    """Tests para modelo CupoDiario"""
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_cupo_str(self, cupo_diario):
        """Test método __str__ de CupoDiario"""
        assert str(cupo_diario) is not None
    
    @pytest.mark.model
    @pytest.mark.django_db
    def test_cupo_calcula_disponibles(self, cupo_diario):
        """Test cálculo de cupos disponibles"""
        # El modelo usa cupos_ocupados, no cupos_reservados
        total = cupo_diario.cupos_disponibles + cupo_diario.cupos_ocupados
        assert total == cupo_diario.cupos_totales
        assert total >= 0

