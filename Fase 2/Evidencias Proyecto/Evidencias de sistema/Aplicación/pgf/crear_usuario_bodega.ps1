# Script para crear usuario BODEGA y datos de prueba
# Uso: .\crear_usuario_bodega.ps1

Write-Host "🔧 Creando usuario BODEGA y datos de prueba..." -ForegroundColor Cyan
Write-Host ""

# Verificar que docker-compose esté disponible
$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerCompose) {
    Write-Host "❌ Error: docker-compose no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

# Verificar que el contenedor api esté corriendo
$apiRunning = docker-compose ps api 2>$null | Select-String -Pattern "Up"
if (-not $apiRunning) {
    Write-Host "⚠️  El contenedor 'api' no está corriendo. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d api
    Start-Sleep -Seconds 5
}

Write-Host "📦 Creando usuario BODEGA..." -ForegroundColor Cyan
docker-compose exec -T api python manage.py create_bodega

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Usuario BODEGA creado exitosamente!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Error al crear usuario BODEGA" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Creando repuestos de prueba..." -ForegroundColor Cyan
docker-compose exec -T api python manage.py seed_repuestos --cantidad 20

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Repuestos de prueba creados exitosamente!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  Error al crear repuestos (puede que ya existan)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ PROCESO COMPLETADO" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Credenciales por defecto:" -ForegroundColor Yellow
Write-Host "   Username: bodega" -ForegroundColor White
Write-Host "   Password: (se mostrará arriba)" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Puedes iniciar sesión en el frontend con estas credenciales" -ForegroundColor Cyan
Write-Host ""

