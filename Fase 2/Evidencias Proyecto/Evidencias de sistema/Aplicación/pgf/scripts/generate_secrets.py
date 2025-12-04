import secrets
import string

def generate_secret_key():
    """Genera una SECRET_KEY segura para Django."""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for i in range(50))

def generate_password(length=20):
    """Genera una contraseña segura."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

print("# --- CREDENCIALES GENERADAS PARA PRODUCCIÓN ---")
print("# Copia esto en tu archivo .env.prod")
print(f"SECRET_KEY='{generate_secret_key()}'")
print(f"POSTGRES_PASSWORD='{generate_password()}'")
print(f"REDIS_PASSWORD='{generate_password()}'")
print(f"ADMIN_PASSWORD='{generate_password()}'")
print("# ----------------------------------------------")
