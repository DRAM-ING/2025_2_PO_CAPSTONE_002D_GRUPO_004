# apps/users/tests/test_management_commands.py
"""
Pruebas para los comandos de gestión de Django.
"""

import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestCreatePermanentAdmin:
    """Pruebas para el comando create_permanent_admin."""
    
    def test_create_permanent_admin_new_user(self):
        """Test crear nuevo usuario admin permanente."""
        # Verificar que no existe
        assert not User.objects.filter(username="admin").exists()
        
        # Ejecutar comando
        out = StringIO()
        call_command("create_permanent_admin", stdout=out)
        
        # Verificar que se creó
        user = User.objects.get(username="admin")
        assert user.email == "admin@example.com"
        assert user.rol == User.Rol.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
        assert user.is_permanent is True
        assert user.check_password("admin123")
        
        # Verificar output
        output = out.getvalue()
        assert "creado exitosamente" in output or "actualizado" in output
    
    def test_create_permanent_admin_existing_user(self):
        """Test actualizar usuario admin permanente existente."""
        # Crear usuario existente
        existing_user = User.objects.create_user(
            username="admin",
            email="old@example.com",
            password="oldpass",
            rol=User.Rol.SUPERVISOR,
            is_staff=False,
            is_superuser=False
        )
        assert existing_user.is_permanent is False
        
        # Ejecutar comando
        out = StringIO()
        call_command("create_permanent_admin", stdout=out)
        
        # Verificar que se actualizó
        user = User.objects.get(username="admin")
        assert user.email == "admin@example.com"
        assert user.rol == User.Rol.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
        assert user.is_permanent is True
        assert user.check_password("admin123")
        
        # Verificar output
        output = out.getvalue()
        assert "actualizado" in output or "marcado como permanente" in output


@pytest.mark.django_db
@pytest.mark.unit
class TestMarkPermanent:
    """Pruebas para el comando mark_permanent."""
    
    def test_mark_permanent_existing_user(self):
        """Test marcar usuario existente como permanente."""
        # Crear usuario
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            rol=User.Rol.SUPERVISOR
        )
        assert user.is_permanent is False
        
        # Ejecutar comando
        out = StringIO()
        call_command("mark_permanent", "testuser", stdout=out)
        
        # Verificar que se marcó como permanente
        user.refresh_from_db()
        assert user.is_permanent is True
        
        # Verificar output
        output = out.getvalue()
        assert "marcado como permanente" in output or "permanente" in output.lower()
    
    def test_mark_permanent_nonexistent_user(self):
        """Test que marcar usuario inexistente lanza error."""
        # Verificar que no existe
        assert not User.objects.filter(username="nonexistent").exists()
        
        # Ejecutar comando y verificar error
        out = StringIO()
        err = StringIO()
        
        try:
            call_command("mark_permanent", "nonexistent", stdout=out, stderr=err)
            # Si no lanza excepción, verificar que el output contiene error
            output = out.getvalue() + err.getvalue()
            assert "no encontrado" in output.lower() or "not found" in output.lower() or "error" in output.lower()
        except CommandError as e:
            assert "no encontrado" in str(e).lower() or "not found" in str(e).lower()
    
    def test_mark_permanent_already_permanent(self):
        """Test marcar usuario ya permanente (no debería fallar)."""
        # Crear usuario permanente
        user = User.objects.create_user(
            username="permanent_user",
            email="permanent@example.com",
            password="testpass123",
            rol=User.Rol.ADMIN
        )
        user.is_permanent = True
        user.save()
        
        # Ejecutar comando
        out = StringIO()
        call_command("mark_permanent", "permanent_user", stdout=out)
        
        # Verificar que sigue siendo permanente
        user.refresh_from_db()
        assert user.is_permanent is True
        
        # Verificar output
        output = out.getvalue()
        assert "permanente" in output.lower()

