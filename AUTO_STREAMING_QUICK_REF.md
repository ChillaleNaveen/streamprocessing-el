# 🎮 AUTO STREAMING - Quick Reference

## ⚡ TL;DR - Get Started in 30 Seconds

```
1. Open: http://localhost:8501
2. Click: "🎮 Auto Streaming" tab
3. Select: quick_test.json
4. Click: "▶️ Start Streaming"
5. Done! ✨
```

---

## 🎛️ Control Panel

```
⚙️ Configuration                 📊 Streaming Status
┌─────────────────────┐         ┌─────────────────────┐
│ 📁 quick_test.json  │         │ 🟢 ACTIVE           │
│ ⏱️  Delay: 3.0s     │         │ 📨 Total: 10        │
│ 🔁 Loop: OFF        │         │ ✅ Success: 8       │
└─────────────────────┘         │ ❌ Failed: 0        │
                                 │ ████████░░ 80%      │
                                 └─────────────────────┘
```

---

## 🎯 Quick Actions

| Want to... | Click... |
|-----------|----------|
| Start sending data | **▶️ Start Streaming** |
| Stop sending data | **⏸️ Stop Streaming** |
| Clear counters | **🔄 Reset Stats** |
| Reload file list | **📁 Refresh Files** |

---

## 📁 Test Files

| File | Prompts | Time @ 3s | Best For |
|------|---------|-----------|----------|
| `quick_test.json` | ~10 | ~30 sec | Quick tests |
| `medium_test.json` | ~30 | ~90 sec | Regular testing |
| `load_test.json` | 100+ | 5+ min | Load testing |

---

## ⚙️ Settings Guide

### Delay (Seconds)
- **1.0-2.0**: ⚡ Fast (risky on 16GB RAM)
- **3.0**: ✅ Recommended (safe)
- **5.0-10.0**: 🐢 Slow (very safe)

### Loop Mode
- **OFF**: ⏹️ Run once and stop
- **ON**: 🔁 Repeat forever

---

## 👀 What You'll See

### When Running:
```
📡 Current Streaming Session
──────────────────────────────
File: quick_test.json
Prompts: 10
Delay: 3.0s

Sending request 3/10...
📝 Prompt: What is machine learning?

✅ Request 3 sent successfully! ID: a1b2c3d4
```

### When Complete:
```
🎉 Streaming completed!
🎈 [Balloons animation!]

Total: 10 | Success: 10 | Failed: 0
```

---

## 🔄 Workflow

```
┌──────────────┐
│ Select File  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Set Delay   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Start Stream │
└──────┬───────┘
       │
       ▼
┌──────────────┐     YES    ┌──────────────┐
│   Running?   ├───────────▶│  Continue    │
└──────┬───────┘            └──────┬───────┘
       │ NO                        │
       ▼                           │
┌──────────────┐                  │
│  Loop Mode?  │◀─────────────────┘
└──────┬───────┘
       │ NO
       ▼
┌──────────────┐
│   Complete   │
└──────────────┘
```

---

## 💡 Pro Tips

1. **Enable Auto-Refresh** in sidebar (5s interval)
2. **Watch Response Stream tab** for live responses
3. **Use Loop Mode** for demos
4. **Increase delay** if seeing failures
5. **Stop before changing settings**

---

## ⚡ Shortcuts

- Start: `▶️`
- Stop: `⏸️`
- Reset: `🔄`
- Refresh: `📁`

---

## 🎯 Common Tasks

### Run Quick Test
```
File: quick_test.json
Delay: 3.0s
Loop: OFF
Action: ▶️ Start
```

### Demo Mode
```
File: quick_test.json
Delay: 2.0s
Loop: ON ✅
Action: ▶️ Start
```

### Load Test
```
File: load_test.json
Delay: 5.0s
Loop: OFF
Action: ▶️ Start
```

---

## 🆘 Quick Fixes

| Problem | Fix |
|---------|-----|
| Button grayed out | Select a file first |
| No responses | Enable Auto-Refresh |
| Too many failures | Increase delay |
| Want to stop | Click ⏸️ Stop |
| Stuck at 100% | Click 🔄 Reset |

---

## 📊 Where to See Results

| Tab | Shows |
|-----|-------|
| 💬 Response Stream | Live LLM responses |
| 📊 Real-time Metrics | Charts & stats |
| 📈 MLflow Tracking | Historical data |
| 📉 Drift Analysis | Quality reports |

---

**🎮 No more command line needed!**  
**Everything you need is in the UI!** ✨
