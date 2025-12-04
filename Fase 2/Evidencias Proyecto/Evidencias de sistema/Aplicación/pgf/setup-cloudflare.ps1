# Script de configuración para Cloudflare Tunnel en Windows
# Ejecutar como Administrador

Write-Host "🚀 Configurando Cloudflare Tunnel para PGF..." -ForegroundColor Green
Write-Host ""

# Verificar si cloudflared está instalado
$cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue

if (-not $cloudflaredPath) {
    Write-Host "⚠️  cloudflared no está instalado" -ForegroundColor Yellow
    Write-Host "Instalando cloudflared..." -ForegroundColor Cyan
    
    # Crear directorio si no existe
    $installDir = "$env:ProgramFiles\cloudflared"
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }
    
    # Descargar cloudflared
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    $outputPath = "$installDir\cloudflared.exe"
    
    Write-Host "Descargando cloudflared..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath
    
    # Agregar al PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installDir", "Machine")
        $env:Path += ";$installDir"
    }
    
    Write-Host "✅ cloudflared instalado en $installDir" -ForegroundColor Green
} else {
    Write-Host "✅ cloudflared ya está instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Ve a https://dash.cloudflare.com y crea un túnel" -ForegroundColor White
Write-Host "2. Copia el TUNNEL_ID y el archivo credentials.json" -ForegroundColor White
Write-Host "3. Edita cloudflare-tunnel/config.yml con tu información" -ForegroundColor White
Write-Host "4. Coloca credentials.json en cloudflare-tunnel/" -ForegroundColor White
Write-Host "5. Configura los registros DNS en Cloudflare" -ForegroundColor White
Write-Host "6. Ejecuta: .\start-cloudflare.ps1" -ForegroundColor White
Write-Host ""

# Verificar si existe el directorio cloudflare-tunnel
if (-not (Test-Path "cloudflare-tunnel")) {
    New-Item -ItemType Directory -Path "cloudflare-tunnel" -Force | Out-Null
    Write-Host "✅ Directorio cloudflare-tunnel creado" -ForegroundColor Green
}

Write-Host ""
Write-Host "📝 Para iniciar sesión en Cloudflare:" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel login" -ForegroundColor White
Write-Host ""
Write-Host "📝 Para crear un túnel:" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel create pgf-tunnel" -ForegroundColor White
Write-Host ""

