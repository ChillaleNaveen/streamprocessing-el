# Stop All LLMOps Services - Improved

param(
    [Parameter(Mandatory = $false)]
    [switch]$Force,
    
    [Parameter(Mandatory = $false)]
    [switch]$KeepKafka,
    
    [Parameter(Mandatory = $false)]
    [switch]$KeepOllama
)

Write-Host "🛑 Stopping LLMOps Monitoring System" -ForegroundColor Red
Write-Host "=====================================" -ForegroundColor Red
Write-Host ""

if (!$Force) {
    Write-Host "This will stop:" -ForegroundColor Yellow
    Write-Host "  - Streamlit Dashboard" -ForegroundColor Gray
    Write-Host "  - MLflow Server" -ForegroundColor Gray
    Write-Host "  - Kafka Consumers" -ForegroundColor Gray
    if (!$KeepKafka) {
        Write-Host "  - Kafka & Zookeeper" -ForegroundColor Gray
    }
    if (!$KeepOllama) {
        Write-Host "  - Ollama Service" -ForegroundColor Gray
    }
    Write-Host ""
    
    $choice = Read-Host "Continue? (y/n)"
    
    if ($choice -ne "y") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""

# Function to kill processes safely
function Stop-ProcessSafely {
    param(
        [string]$ProcessName,
        [string]$DisplayName
    )
    
    try {
        $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        
        if ($processes) {
            Write-Host "Stopping $DisplayName..." -ForegroundColor Yellow
            $processes | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            Write-Host "✅ $DisplayName stopped" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "ℹ️ $DisplayName not running" -ForegroundColor Gray
            return $false
        }
    }
    catch {
        Write-Host "⚠️ Error stopping $DisplayName" -ForegroundColor Yellow
        return $false
    }
}

# Function to kill process on specific port
function Stop-ProcessOnPort {
    param([int]$Port, [string]$ServiceName)
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        
        if ($connections) {
            Write-Host "Stopping $ServiceName on port $Port..." -ForegroundColor Yellow
            
            foreach ($conn in $connections) {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process) {
                    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                }
            }
            
            Start-Sleep -Seconds 1
            Write-Host "✅ $ServiceName stopped (port $Port)" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "ℹ️ $ServiceName not using port $Port" -ForegroundColor Gray
            return $false
        }
    }
    catch {
        Write-Host "⚠️ Error stopping $ServiceName" -ForegroundColor Yellow
        return $false
    }
}

Write-Host "Stopping Services..." -ForegroundColor Cyan
Write-Host ""

# Stop Streamlit
Stop-ProcessOnPort -Port 8501 -ServiceName "Streamlit"

# Stop MLflow
Stop-ProcessOnPort -Port 5000 -ServiceName "MLflow"

# Stop Python processes (consumers)
Write-Host "Stopping Python consumers..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*consumer*" -or $_.CommandLine -like "*streamlit*" -or $_.CommandLine -like "*mlflow*" }

if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Python consumers stopped" -ForegroundColor Green
}
else {
    Write-Host "ℹ️ No Python consumers running" -ForegroundColor Gray
}

Start-Sleep -Seconds 2

# Stop Kafka if not keeping
if (!$KeepKafka) {
    Write-Host ""
    Write-Host "Stopping Kafka infrastructure..." -ForegroundColor Cyan
    
    # Stop Kafka
    $kafkaProcesses = Get-Process -Name "java*" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*kafka*" -and $_.CommandLine -notlike "*zookeeper*" }
    
    if ($kafkaProcesses) {
        Write-Host "Stopping Kafka server..." -ForegroundColor Yellow
        $kafkaProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "✅ Kafka stopped" -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️ Kafka not running" -ForegroundColor Gray
    }
    
    # Stop Zookeeper
    $zkProcesses = Get-Process -Name "java*" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*zookeeper*" }
    
    if ($zkProcesses) {
        Write-Host "Stopping Zookeeper..." -ForegroundColor Yellow
        $zkProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "✅ Zookeeper stopped" -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️ Zookeeper not running" -ForegroundColor Gray
    }
}
else {
    Write-Host ""
    Write-Host "ℹ️ Keeping Kafka running (--KeepKafka flag)" -ForegroundColor Cyan
}

# Stop Ollama if not keeping
if (!$KeepOllama) {
    Write-Host ""
    Stop-ProcessOnPort -Port 11434 -ServiceName "Ollama"
}
else {
    Write-Host ""
    Write-Host "ℹ️ Keeping Ollama running (--KeepOllama flag)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ All services stopped!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Verify ports are free
Write-Host "Verifying ports..." -ForegroundColor Cyan

$ports = @{
    8501 = "Streamlit"
    5000 = "MLflow"
}

if (!$KeepKafka) {
    $ports[9092] = "Kafka"
    $ports[2181] = "Zookeeper"
}

if (!$KeepOllama) {
    $ports[11434] = "Ollama"
}

$allClear = $true

foreach ($port in $ports.Keys) {
    $serviceName = $ports[$port]
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    
    if ($connection) {
        Write-Host "⚠️ Port $port ($serviceName) still in use" -ForegroundColor Yellow
        $allClear = $false
    }
    else {
        Write-Host "✅ Port $port ($serviceName) free" -ForegroundColor Green
    }
}

Write-Host ""

if ($allClear) {
    Write-Host "✅ All ports are free!" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Some ports still in use. You may need to:" -ForegroundColor Yellow
    Write-Host "   1. Close PowerShell windows manually" -ForegroundColor Gray
    Write-Host "   2. Run this script again with -Force" -ForegroundColor Gray
    Write-Host "   3. Restart your computer if issues persist" -ForegroundColor Gray
}

Write-Host ""
Write-Host "To restart the system, run:" -ForegroundColor Cyan
Write-Host "  .\launch_system.ps1" -ForegroundColor White
Write-Host ""