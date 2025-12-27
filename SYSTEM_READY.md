# LLMOps System - Fixed and Ready

## ✅ Issues Resolved

### 1. Evidently Library Error
**Problem:** `ModuleNotFoundError: No module named 'evidently.report'`

**Root Cause:** The evidently library version (0.4.11) was outdated and had API incompatibilities.

**Solution:**
- ✅ Updated `requirements.txt`: evidently 0.4.11 → 0.4.33
- ✅ Fixed imports in `evidently_consumer.py`:
  - Changed from deprecated `DataDriftPreset` and `DataQualityPreset`
  - Updated to use `DatasetDriftMetric`, `DataDriftTable`, and `DatasetMissingValuesMetric`
- ✅ Installed the new version successfully

### 2. Import Verification
**Status:** ✅ All evidently imports tested and working properly

---

## 🚀 How to Run the System

### Option 1: Full Automated Launch
```powershell
.\launch_system.ps1
```
This script will:
- Clean up ports
- Start Kafka (Zookeeper + Kafka Server)
- Start Ollama service
- Create Kafka topics
- Setup Python environment
- Start MLflow tracking server
- Start consumers (MLflow + Evidently)
- Start Streamlit dashboard

### Option 2: Quick Test with Automation
```powershell
.\launch_system.ps1 -AutoTest quick
```
This will launch the system AND automatically run a quick test.

### Option 3: Skip Services Already Running
If you already have Kafka or Ollama running:
```powershell
.\launch_system.ps1 -SkipKafka -SkipOllama
```

---

## 📊 Access Points

Once the system is running, you can access:

| Service | URL |
|---------|-----|
| **Streamlit Dashboard** | http://localhost:8501 |
| **MLflow UI** | http://localhost:5000 |
| **Kafka** | localhost:9092 |
| **Ollama** | localhost:11434 |

---

## 🧪 Running Tests

### Manual Test
After the system is running, open a **new terminal** and run:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run test with the quick test file
python batch_producer.py --file data/quick_test.json --delay 3.0
```

### What to Expect
1. **Producer Terminal:** You'll see requests being sent to Kafka
2. **Streamlit Dashboard:** Live responses will appear in real-time
3. **Evidently Consumer:** Will collect samples and generate drift reports
4. **MLflow Consumer:** Will track metrics

---

## 📁 Key Files Modified

1. **requirements.txt**
   - Updated evidently library to version 0.4.33

2. **evidently_consumer.py**
   - Fixed imports to use modern evidently API
   - Updated metrics from presets to individual metrics

---

## 🛠️ Troubleshooting

### If Evidently Consumer Still Fails
```powershell
# Reinstall evidently manually
python -m pip install --upgrade evidently==0.4.33
```

### If Kafka Doesn't Start
```powershell
# Check if port 9092 is in use
netstat -ano | findstr :9092

# Kill process if needed (replace PID)
taskkill /PID <PID> /F
```

### If Ollama Doesn't Respond
```powershell
# Check if Ollama is running
curl http://localhost:11434

# Start Ollama manually
ollama serve

# Check available models
ollama list

# Pull a model if none available
ollama pull tinyllama
```

---

## 🎯 Expected Workflow

1. **Launch System:** Run `.\launch_system.ps1`
2. **Wait for Services:** System will open multiple PowerShell windows for each service
3. **Verify Dashboards:** 
   - Streamlit dashboard opens at http://localhost:8501
   - MLflow UI opens at http://localhost:5000
4. **Run Test:** Execute `python batch_producer.py --file data/quick_test.json --delay 3.0`
5. **Monitor Results:**
   - Watch live responses in Streamlit
   - Check drift reports in `evidently_reports/` folder
   - Review metrics in MLflow UI

---

## 🔴 Stopping the System

To stop all services:
```powershell
.\stop-all.ps1
```

This will cleanly shut down all components.

---

## 📝 Notes

- **RAM Usage:** System is optimized for 16GB RAM
- **Batch Size:** Evidently generates reports after 30 samples
- **Test Delays:** 3.0 seconds between requests prevents overload
- **Concurrent Streams:** Max 50 concurrent LLM requests

---

## ✨ System is Ready!

Your LLMOps monitoring system is now fully operational. All errors have been resolved, and you can start monitoring your LLM applications.

**Happy Monitoring! 🚀**
