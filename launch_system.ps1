# LLMOps Monitoring - Improved System Launcher
# Optimized for HP Pavilion i5-1240P with 16GB RAM

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("quick", "medium", "none")]
    [string]$AutoTest = "none",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipKafka,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipOllama,
    
    [Parameter(Mandatory = $false)]
    [string]$KafkaHome = "C:\kafka"
)

# Configuration
$ErrorActionPreference = "Continue"
$Global:ProcessList = @()

# Helper Functions
function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Number, [string]$Text)
    Write-Host ""
    Write-Host "[$Number] $Text" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "[INFO] $Text" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "[WARN] $Text" -ForegroundColor Yellow
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return $connection.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

function Wait-ForPort {
    param([int]$Port, [string]$Service, [int]$TimeoutSeconds = 30)
    
    Write-Info "Waiting for $Service on port $Port..."
    $elapsed = 0
    
    while ($elapsed -lt $TimeoutSeconds) {
        if (Test-Port -Port $Port) {
            Write-Success "$Service is ready on port $Port"
            return $true
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    Write-Error-Custom "$Service did not start within $TimeoutSeconds seconds"
    return $false
}

function Stop-ProcessOnPort {
    param([int]$Port)
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($proc in $processes) {
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
            Write-Info "Killed process $proc on port $Port"
        }
    }
    catch {
        # Port not in use
    }
}

function Start-BackgroundProcess {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory = (Get-Location).Path
    )
    
    $scriptBlock = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Write-Host '=========================================' -ForegroundColor Cyan
Write-Host '$Title' -ForegroundColor Cyan
Write-Host '=========================================' -ForegroundColor Cyan
Write-Host ''
cd '$WorkingDirectory'
$Command
"@
    
    $process = Start-Process powershell -ArgumentList `
        "-NoExit", `
        "-Command", `
        $scriptBlock `
        -PassThru `
        -WindowStyle Normal
    
    $Global:ProcessList += @{
        Name    = $Title
        Process = $process
    }
    
    return $process
}

# Main Execution
Write-Header "LLMOps Monitoring System - Optimized Launcher"

Write-Host "System Configuration:" -ForegroundColor White
Write-Host "  - Optimized for: HP Pavilion i5-1240P" -ForegroundColor Gray
Write-Host "  - RAM: 16GB" -ForegroundColor Gray
Write-Host "  - Max concurrent streams: 50" -ForegroundColor Gray
Write-Host "  - Batch size: 30 samples" -ForegroundColor Gray
Write-Host ""

Write-Host "This script will:" -ForegroundColor White
Write-Host "  1. Clean up any stuck ports" -ForegroundColor Gray
Write-Host "  2. Start Kafka infrastructure" -ForegroundColor Gray
Write-Host "  3. Start Ollama service" -ForegroundColor Gray
Write-Host "  4. Create Kafka topics" -ForegroundColor Gray
Write-Host "  5. Setup Python environment" -ForegroundColor Gray
Write-Host "  6. Start monitoring services" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# STEP 0: CLEANUP
Write-Step "0/9" "Cleaning Up Stuck Ports"

Write-Info "Checking for processes on critical ports..."
$portsToCheck = @(9092, 2181, 5000, 8501, 11434)
foreach ($port in $portsToCheck) {
    if (Test-Port -Port $port) {
        Write-Warning-Custom "Port $port is in use. Attempting to free it..."
        Stop-ProcessOnPort -Port $port
        Start-Sleep -Seconds 2
    }
}
Write-Success "Port cleanup complete"

# STEP 1: CHECK PREREQUISITES
Write-Step "1/9" "Checking Prerequisites"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python installed: $pythonVersion"
}
catch {
    Write-Error-Custom "Python not found. Please install Python 3.8+"
    exit 1
}

# Check virtual environment
if (!(Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Warning-Custom "Virtual environment not found. Creating..."
    python -m venv venv
    Write-Success "Virtual environment created"
}

# Check Kafka directory
if (!$SkipKafka) {
    if (!(Test-Path $KafkaHome)) {
        Write-Error-Custom "Kafka directory not found: $KafkaHome"
        Write-Info "Install Kafka or use -SkipKafka if already running"
        exit 1
    }
    Write-Success "Kafka directory found: $KafkaHome"
}

# STEP 2: START KAFKA
Write-Step "2/9" "Starting Kafka Infrastructure"

if ($SkipKafka) {
    Write-Warning-Custom "Skipping Kafka startup"
    if (!(Test-Port -Port 9092)) {
        Write-Error-Custom "Kafka not running on port 9092!"
        exit 1
    }
}
else {
    # Kill any existing Kafka/Zookeeper processes
    Write-Info "Stopping any existing Kafka processes..."
    Get-Process -Name "*kafka*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "*zookeeper*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    
    if (Test-Port -Port 9092) {
        Write-Success "Kafka is already running"
    }
    else {
        Write-Info "Starting Zookeeper..."
        $zkCmd = "cd '$KafkaHome'; .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"
        Start-BackgroundProcess -Title "Zookeeper" -Command $zkCmd
        
        Start-Sleep -Seconds 12
        
        Write-Info "Starting Kafka..."
        $kafkaCmd = "cd '$KafkaHome'; .\bin\windows\kafka-server-start.bat .\config\server.properties"
        Start-BackgroundProcess -Title "Kafka Server" -Command $kafkaCmd
        
        if (!(Wait-ForPort -Port 9092 -Service "Kafka" -TimeoutSeconds 60)) {
            Write-Error-Custom "Failed to start Kafka"
            Write-Info "Check the Kafka window for errors"
            exit 1
        }
    }
}

# STEP 3: START OLLAMA
Write-Step "3/9" "Starting Ollama LLM Service"

if ($SkipOllama) {
    Write-Warning-Custom "Skipping Ollama startup"
    if (!(Test-Port -Port 11434)) {
        Write-Error-Custom "Ollama not running on port 11434!"
        exit 1
    }
}
else {
    if (Test-Port -Port 11434) {
        Write-Success "Ollama is already running"
    }
    else {
        Write-Info "Starting Ollama service..."
        
        try {
            Start-BackgroundProcess -Title "Ollama Service" -Command "ollama serve"
            
            if (!(Wait-ForPort -Port 11434 -Service "Ollama" -TimeoutSeconds 30)) {
                Write-Warning-Custom "Ollama may not be installed"
                Write-Info "Install: https://ollama.ai/download"
                $skip = Read-Host "Continue without Ollama? (y/n)"
                if ($skip -ne "y") { exit 1 }
            }
        }
        catch {
            Write-Warning-Custom "Could not start Ollama"
            Write-Info "Start manually: ollama serve"
            Read-Host "Press Enter once Ollama is running..."
        }
    }
}

# Check Ollama model
Write-Info "Checking Ollama model..."
try {
    $models = ollama list 2>&1 | Out-String
    if ($models -match "tinyllama|llama") {
        Write-Success "Ollama model available"
    }
    else {
        Write-Warning-Custom "No models found"
        Write-Info "Pull a model: ollama pull tinyllama"
        Write-Info "Or update config.py to use a different model"
    }
}
catch {
    Write-Warning-Custom "Could not check Ollama models"
}

# STEP 4: CREATE KAFKA TOPICS
Write-Step "4/9" "Creating Kafka Topics"

Start-Sleep -Seconds 3

$topics = @("llm-requests", "llm-responses")

foreach ($topic in $topics) {
    Write-Info "Creating topic: $topic"
    
    $createCmd = "& '$KafkaHome\bin\windows\kafka-topics.bat' --create --bootstrap-server localhost:9092 --topic $topic --partitions 2 --replication-factor 1 --if-not-exists 2>&1"
    
    try {
        Invoke-Expression $createCmd | Out-Null
        Write-Success "Topic ready: $topic"
    }
    catch {
        Write-Warning-Custom "Topic may already exist: $topic"
    }
    
    Start-Sleep -Seconds 1
}

# Verify topics
Write-Info "Verifying topics..."
Start-Sleep -Seconds 2
try {
    $listCmd = "& '$KafkaHome\bin\windows\kafka-topics.bat' --list --bootstrap-server localhost:9092 2>&1"
    $topicList = Invoke-Expression $listCmd
    Write-Host "Available topics:" -ForegroundColor Cyan
    $topicList | ForEach-Object { 
        if ($_ -and $_ -notmatch "WARN") {
            Write-Host "  - $_" -ForegroundColor White 
        }
    }
}
catch {
    Write-Warning-Custom "Could not list topics"
}

# STEP 5: SETUP PYTHON ENVIRONMENT
Write-Step "5/9" "Setting Up Python Environment"

Write-Info "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

Write-Info "Installing/Upgrading dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

Write-Success "Python environment ready"

# STEP 6: GENERATE TEST PROMPTS
Write-Step "6/9" "Generating Test Prompts"

if (!(Test-Path ".\data")) {
    New-Item -ItemType Directory -Path ".\data" -Force | Out-Null
}

if (Test-Path ".\data\quick_test.json") {
    Write-Success "Test prompts already exist"
}
else {
    Write-Info "Generating test prompts..."
    python prompt_generator.py
    Write-Success "Test prompts generated"
}

# STEP 7: START MLFLOW
Write-Step "7/9" "Starting MLflow Tracking Server"

if (Test-Port -Port 5000) {
    Write-Success "MLflow already running"
}
else {
    Write-Info "Starting MLflow server..."
    $mlflowCmd = "& '.\venv\Scripts\Activate.ps1'; Write-Host 'MLflow UI: http://localhost:5000' -ForegroundColor Green; mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns"
    Start-BackgroundProcess -Title "MLflow Tracking Server" -Command $mlflowCmd
    
    if (!(Wait-ForPort -Port 5000 -Service "MLflow" -TimeoutSeconds 40)) {
        Write-Warning-Custom "MLflow still starting..."
    }
}

# STEP 8: START CONSUMERS
Write-Step "8/9" "Starting Kafka Consumers"

Write-Info "Starting MLflow Consumer..."
$mlflowConsumerCmd = "& '.\venv\Scripts\Activate.ps1'; python mlflow_consumer.py"
Start-BackgroundProcess -Title "MLflow Consumer" -Command $mlflowConsumerCmd
Start-Sleep -Seconds 3

Write-Info "Starting Evidently Consumer..."
$evidentlyConsumerCmd = "& '.\venv\Scripts\Activate.ps1'; python evidently_consumer.py"
Start-BackgroundProcess -Title "Evidently Consumer" -Command $evidentlyConsumerCmd
Start-Sleep -Seconds 3

Write-Success "Consumers started"

# STEP 9: START STREAMLIT
Write-Step "9/9" "Starting Streamlit Dashboard"

if (Test-Port -Port 8501) {
    Write-Success "Streamlit already running"
}
else {
    Write-Info "Starting Streamlit dashboard..."
    $streamlitCmd = "& '.\venv\Scripts\Activate.ps1'; Write-Host 'Dashboard: http://localhost:8501' -ForegroundColor Green; streamlit run streamlit_app.py --server.headless=true"
    Start-BackgroundProcess -Title "Streamlit Dashboard" -Command $streamlitCmd
    
    if (!(Wait-ForPort -Port 8501 -Service "Streamlit" -TimeoutSeconds 40)) {
        Write-Warning-Custom "Streamlit still starting..."
    }
}

# SYSTEM READY
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                   SYSTEM READY!                            " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  - Streamlit Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "  - MLflow UI:           http://localhost:5000" -ForegroundColor White
Write-Host "  - Kafka:               localhost:9092" -ForegroundColor White
Write-Host "  - Ollama:              localhost:11434" -ForegroundColor White
Write-Host ""

Write-Host "Running Services:" -ForegroundColor Cyan
$Global:ProcessList | ForEach-Object {
    Write-Host "  [OK] $($_.Name)" -ForegroundColor Green
}
Write-Host ""

# AUTO TEST
if ($AutoTest -ne "none") {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "Running Automatic Test: $AutoTest" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    
    Start-Sleep -Seconds 5
    
    $testFile = "$AutoTest`_test.json"
    Write-Info "Executing batch test with $testFile..."
    
    & ".\venv\Scripts\Activate.ps1"
    python batch_producer.py --file ".\data\$testFile" --delay 3.0 --save-results
    
    Write-Success "Test completed!"
}

# USAGE INSTRUCTIONS
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Open Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "  2. Run test:" -ForegroundColor White
Write-Host "     python batch_producer.py --file .\data\quick_test.json --delay 3.0" -ForegroundColor Gray
Write-Host ""

Write-Host "To Stop:" -ForegroundColor Yellow
Write-Host "  Run: .\stop-all.ps1" -ForegroundColor White
Write-Host ""

Write-Host "Opening dashboards in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    Start-Process "http://localhost:8501"
    Start-Process "http://localhost:5000"
    Write-Success "Dashboards opened"
}
catch {
    Write-Warning-Custom "Open manually in browser"
}

Write-Host ""
Write-Host "System running. Press Ctrl+C to stop monitoring." -ForegroundColor Green
Write-Host ""

# Keep running
try {
    while ($true) {
        Start-Sleep -Seconds 30
        
        # Health check
        $healthy = $true
        if (!(Test-Port -Port 9092)) { Write-Warning-Custom "Kafka offline"; $healthy = $false }
        if (!(Test-Port -Port 8501)) { Write-Warning-Custom "Streamlit offline"; $healthy = $false }
        if (!(Test-Port -Port 5000)) { Write-Warning-Custom "MLflow offline"; $healthy = $false }
        
        if ($healthy) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] System healthy [OK]" -ForegroundColor Green
        }
    }
}
catch {
    Write-Host ""
    Write-Info "Monitoring stopped. Services still running."
}