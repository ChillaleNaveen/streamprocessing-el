# 🎮 Auto Streaming Feature - User Guide

## 🎉 What's New?

You no longer need to open a terminal and run `python batch_producer.py` every time!

The Streamlit dashboard now has a built-in **Auto Streaming** feature with Start/Stop buttons!

---

## 🚀 How to Use

### Step 1: Open the Dashboard
```
http://localhost:8501
```

### Step 2: Go to "🎮 Auto Streaming" Tab
Click on the **"🎮 Auto Streaming"** tab at the top of the dashboard

### Step 3: Configure Your Test
- **📁 Select Test File**: Choose from available files (e.g., `quick_test.json`)
- **⏱️ Set Delay**: Adjust delay between requests (1-10 seconds)
- **🔁 Loop Mode**: Enable to stream continuously in a loop

### Step 4: Click "▶️ Start Streaming"
That's it! The system will:
- ✅ Automatically send requests to the LLM
- ✅ Display progress in real-time
- ✅ Show success/failure statistics
- ✅ Update all monitoring tabs

### Step 5: Watch the Results
- Switch to **"💬 Response Stream"** tab to see responses
- Check **"📊 Real-time Metrics"** for charts
- Monitor **"📈 MLflow Tracking"** for historical data

---

## 🎛️ Control Buttons

| Button | Function |
|--------|----------|
| **▶️ Start Streaming** | Begin sending test data |
| **⏸️ Stop Streaming** | Pause the streaming process |
| **🔄 Reset Stats** | Clear statistics counters |
| **📁 Refresh Files** | Reload the list of test files |

---

## 📊 Features

### Real-Time Progress Tracking
- See how many requests have been sent
- Track success vs. failure rate
- Visual progress bar shows completion
- Current prompt being processed

### Status Indicators
- 🟢 **Streaming ACTIVE**: Currently sending data
- ⚪ **Streaming STOPPED**: Not active

### Statistics Display
- **📨 Total Sent**: Total number of requests  
- **✅ Success**: Successfully processed requests
- **❌ Failed**: Failed requests

### Loop Mode
- Enable **🔁 Loop Continuously** to keep streaming
- Perfect for demonstrations and continuous testing
- Automatically restarts from the beginning when done

---

## 💡 Benefits

### Before (Manual)
❌ Open new terminal  
❌ Activate virtual environment  
❌ Type long command  
❌ Remember file paths and options  
❌ Can't easily stop/restart  

### After (Auto Streaming)
✅ One-click start  
✅ All controls in UI  
✅ Visual progress tracking  
✅ Easy stop/restart  
✅ No terminal needed  

---

## 📖 Usage Examples

### Quick Test
1. Select `quick_test.json`
2. Set delay to `3.0` seconds
3. Loop mode: **OFF**
4. Click **Start Streaming**
5. Wait for completion (~30 seconds for 10 prompts)

### Continuous Demo
1. Select `quick_test.json`
2. Set delay to `2.0` seconds
3. Loop mode: **ON** ✅
4. Click **Start Streaming**
5. Let it run continuously for demonstrations
6. Click **Stop** when done

### Load Testing
1. Select `medium_test.json` or `load_test.json`
2. Set delay to `5.0` seconds (safer for larger tests)
3. Loop mode: **OFF**
4. Click **Start Streaming**
5. Monitor MLflow and Evidently for results

---

## ⚙️ Configuration Tips

### Recommended Delays
- **Quick Test (10 prompts)**: 3.0 seconds
- **Medium Test (30 prompts)**: 3.0-5.0 seconds
- **Load Test (100+ prompts)**: 5.0-10.0 seconds

### Why Delay Matters
- Prevents overwhelming your system
- Gives LLM time to generate quality responses
- Reduces risk of timeouts
- Better for monitoring accuracy

### Loop Mode Use Cases
✅ **Use Loop Mode when:**
- Running demos or presentations
- Long-term stress testing
- Continuous monitoring validation
- Keeping dashboard active

❌ **Don't use Loop Mode when:**
- Collecting specific sample sizes
- Running one-time tests
- Conserving system resources

---

## 🔍 Monitoring While Streaming

### Real-Time Feedback
While streaming is active, you'll see:
- Current request number (e.g., "Sending request 5/10")
- The prompt being sent
- Success/failure messages
- Request IDs for tracking

### Multi-Tab View
Keep multiple tabs open:
1. **🎮 Auto Streaming** - Control panel
2. **💬 Response Stream** - See live responses
3. **📊 Real-time Metrics** - Watch charts update

### Auto-Refresh
Make sure **"🔄 Auto Refresh (5s)"** is enabled in the sidebar for automatic updates!

---

## 🐛 Troubleshooting

### Streaming Won't Start
**Check:**
- ✅ Is a test file selected?
- ✅ Are Kafka and Ollama running?
- ✅ Is the button enabled (not grayed out)?

### No Responses Appearing
**Solutions:**
1. Enable Auto-Refresh in sidebar
2. Switch to "💬 Response Stream" tab
3. Wait 5 seconds for auto-refresh
4. Click "Manual Refresh" if needed

### High Failure Rate
**Try:**
- Increase the delay between requests
- Check if Ollama is responding (test in "🧪 Test LLM" tab)
- Reduce prompt complexity
- Check system resources

### Streaming Stuck
**Fix:**
1. Click "⏸️ Stop Streaming"
2. Wait a few seconds
3. Click "🔄 Reset Stats"
4. Try starting again with higher delay

---

## 🎯 Best Practices

### 1. Test Before Production
Always test with `quick_test.json` before using larger files

### 2. Monitor System Resources
Watch your CPU and memory usage during streaming

### 3. Use Appropriate Delays
Don't go below 2.0 seconds unless testing on powerful hardware

### 4. Check Results Regularly
Monitor the Response Stream tab to ensure quality responses

### 5. Stop When Done
Don't leave loop mode running indefinitely unless needed

---

## 🆚 Comparison: Auto Streaming vs Manual

| Feature | Auto Streaming | Manual CLI |
|---------|---------------|------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ One click | ⭐⭐ Multiple steps |
| **Visual Feedback** | ⭐⭐⭐⭐⭐ Real-time UI | ⭐⭐ Terminal output |
| **Control** | ⭐⭐⭐⭐⭐ Start/Stop anytime | ⭐⭐⭐ Ctrl+C only |
| **Monitoring** | ⭐⭐⭐⭐⭐ Integrated | ⭐⭐ Separate windows |
| **Loop Mode** | ⭐⭐⭐⭐⭐ One click | ⭐ Script needed |

---

## 🎊 Summary

**You can now:**
- ✅ Start/Stop streaming with one click
- ✅ Configure all settings in the UI
- ✅ Monitor progress in real-time
- ✅ Switch between test files easily
- ✅ Enable loop mode for continuous testing
- ✅ No need to touch the terminal!

**Perfect for:**
- Quick testing and validation
- Demos and presentations
- Continuous monitoring
- Learning and experimentation

---

## 🚀 Get Started Now!

1. Open dashboard: http://localhost:8501
2. Click **"🎮 Auto Streaming"** tab
3. Select `quick_test.json`
4. Click **"▶️ Start Streaming"**
5. Enjoy! 🎉

**Happy Streaming!** 🎮✨
