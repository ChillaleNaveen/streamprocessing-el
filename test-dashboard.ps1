# Quick Test Script - Verify Dashboard Fix
# Run this to test if the dashboard is receiving data properly

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  Dashboard Data Flow Test" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Check if Kafka is running"
Write-Host "  2. Check if Streamlit is running"
Write-Host "  3. Run a quick diagnostic test"
Write-Host "  4. Send test messages"
Write-Host ""

# Check Kafka
Write-Host "[1/4] Checking Kafka..." -ForegroundColor Yellow
$kafkaRunning = Test-NetConnection -ComputerName localhost -Port 9092 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($kafkaRunning.TcpTestSucceeded) {
    Write-Host "  ✅ Kafka is running on port 9092" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Kafka is NOT running!" -ForegroundColor Red
    Write-Host "     Run: .\launch_system.ps1" -ForegroundColor Yellow
    exit 1
}

# Check Streamlit
Write-Host "[2/4] Checking Streamlit..." -ForegroundColor Yellow
$streamlitRunning = Test-NetConnection -ComputerName localhost -Port 8501 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($streamlitRunning.TcpTestSucceeded) {
    Write-Host "  ✅ Streamlit is running on port 8501" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Streamlit is NOT running!" -ForegroundColor Red
    Write-Host "     Run: .\launch_system.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[3/4] Running Kafka flow test..." -ForegroundColor Yellow
Write-Host "      This will listen for messages for 5 seconds" -ForegroundColor Gray
Write-Host ""

# Start the diagnostic in background
$diagJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & ".\venv\Scripts\Python.exe" test_kafka_flow.py
}

Start-Sleep -Seconds 2

Write-Host "[4/4] Sending test messages..." -ForegroundColor Yellow
Write-Host ""

# Run a quick producer test
& ".\venv\Scripts\Python.exe" batch_producer.py --file data/quick_test.json --delay 2.0

# Wait for diagnostic to complete
Wait-Job $diagJob -Timeout 10 | Out-Null
$output = Receive-Job $diagJob
Write-Host ""
Write-Host "=== Diagnostic Output ===" -ForegroundColor Cyan
Write-Host $output
Remove-Job $diagJob -Force

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "  Test Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "  2. Check sidebar: Auto-Refresh should be ON ✅" -ForegroundColor White
Write-Host "  3. Go to '💬 Response Stream' tab" -ForegroundColor White
Write-Host "  4. You should see responses!" -ForegroundColor White
Write-Host ""

Write-Host "If you don't see responses:" -ForegroundColor Yellow
Write-Host "  • Check that Auto-Refresh is ON in sidebar" -ForegroundColor Gray
Write-Host "  • Click 'Manual Refresh' button" -ForegroundColor Gray
Write-Host "  • Wait 5 seconds for auto-refresh" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Open dashboard in browser? (y/n)"
if ($confirm -eq "y") {
    Start-Process "http://localhost:8501"
}
