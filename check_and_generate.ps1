# check_and_generate.ps1
# Verifica si el CSV más reciente fue modificado hoy.
# Si sí → genera dashboards HTML y hace git push.
# Si no → no hace nada.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Rutas ─────────────────────────────────────────────────────────────────────
$BASE    = "C:\Users\FranciscoLinares\OneDrive - Solusoft\Documents\2026\Claude\Dashboard Celulas"
$REPO    = "C:\Users\FranciscoLinares\Informes"
$SCRIPT  = "$REPO\generar_dashboards.py"
$LOG     = "$REPO\log_generacion.txt"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Log($msg) {
    $ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

# ── 1. Buscar CSV más reciente ─────────────────────────────────────────────────
Log "=== Inicio de ejecución ==="

$csv = Get-ChildItem -Path $BASE -Filter "*.csv" -File -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending |
       Select-Object -First 1

if (-not $csv) {
    Log "No se encontró ningún CSV en $BASE. Saliendo."
    exit 0
}

Log "CSV más reciente: $($csv.FullName) | Modificado: $($csv.LastWriteTime)"

# ── 2. Verificar si fue modificado hoy ────────────────────────────────────────
$hoy = (Get-Date).Date

if ($csv.LastWriteTime.Date -ne $hoy) {
    Log "El CSV no fue modificado hoy ($($csv.LastWriteTime.ToString('yyyy-MM-dd'))). No se generan dashboards."
    exit 0
}

Log "CSV modificado hoy. Procediendo con la generación..."

# ── 3. Preparar carpeta de salida ─────────────────────────────────────────────
$fecha   = Get-Date -Format "yyyy-MM-dd"
$outputDashboard = "$BASE\$fecha"
$outputRepo      = "$REPO\$fecha"

if (-not (Test-Path $outputDashboard)) {
    New-Item -ItemType Directory -Path $outputDashboard | Out-Null
    Log "Carpeta creada: $outputDashboard"
}

# ── 4. Detectar Python ────────────────────────────────────────────────────────
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) { $python = $cmd; break }
    } catch {}
}

if (-not $python) {
    Log "ERROR: Python no encontrado en PATH. Instala Python 3 y vuelve a intentarlo."
    exit 1
}

Log "Python encontrado: $python"

# ── 5. Generar dashboards HTML ────────────────────────────────────────────────
Log "Ejecutando generador de dashboards..."
& $python $SCRIPT --csv $csv.FullName --output $outputDashboard --date $fecha

if ($LASTEXITCODE -ne 0) {
    Log "ERROR: El script Python falló con código $LASTEXITCODE."
    exit 1
}

Log "Dashboards generados en: $outputDashboard"

# ── 6. Copiar HTMLs al repo ────────────────────────────────────────────────────
if (-not (Test-Path $outputRepo)) {
    New-Item -ItemType Directory -Path $outputRepo | Out-Null
}

Copy-Item "$outputDashboard\*.html" -Destination $outputRepo -Force
Log "HTMLs copiados a: $outputRepo"

# ── 7. Git push ────────────────────────────────────────────────────────────────
Log "Haciendo git commit y push..."
Set-Location $REPO

git add .
git commit -m "Informes $fecha"

if ($LASTEXITCODE -ne 0) {
    Log "AVISO: git commit falló (puede que no haya cambios nuevos)."
} else {
    git push
    if ($LASTEXITCODE -eq 0) {
        Log "Git push exitoso."
    } else {
        Log "ERROR: git push falló. Revisa la conexión o el token de GitHub."
    }
}

Log "=== Fin de ejecución. Dashboards disponibles en $outputRepo ==="
