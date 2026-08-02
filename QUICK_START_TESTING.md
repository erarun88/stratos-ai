# Quick Start: Testing Architecture View

## 🚀 Test It Now (3 minutes)

### Step 1: Open the App
```
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

### Step 2: Ask a Chat Question
```
1. Click "💬 AI Chat" in navbar
2. Ask: "What's the status of project 1?"
3. Or: "Tell me about project risks"
4. Wait for response
```

### Step 3: View Architecture
```
1. Click "🧠 AI Execution Studio" in navbar
2. See list of recent requests
3. Click the request you just made
4. 🎉 Scroll down to see the new "Architecture View"!
```

### Step 4: Explore
```
1. See the statistics at top (Duration, Tokens, Cost, etc.)
2. See the interactive diagram with all components
3. Click any component to see details
4. Check the "All Components" list at bottom
```

## 📊 What You Should See

### Statistics Panel (Top)
```
⏱️ 342ms | 🔤 2,340 tokens | 💰 $0.047 | ⚙️ 8 components | ✅ 0 errors
```

### Interactive Diagram
```
         💬 ChatEndpoint
              ↓
        🎯 Supervisor
        ↙        ↘
    📊 Project  ⚠️ Risk
      Agent      Agent
        ↓          ↓
      🧠 LLM    🧠 LLM
        ↘        ↙
        ✅ Reflection
        🔒 Approval
```

### Component Details Sidebar
```
🎯 Supervisor
orchestrator

Status: completed
Duration: 45.3ms
Tokens Used: 280
Cost: $0.0042
3 downstream components
```

## ✅ Success Criteria

- [ ] Can see statistics panel
- [ ] SVG diagram renders
- [ ] Components are clickable
- [ ] Component details show
- [ ] Colors indicate status (green=complete, red=error)
- [ ] Connections show between components

## 🐛 Troubleshooting

### "No architecture data"
- **Cause**: No semantic events in database
- **Fix**: Make sure you asked a chat question first

### "Diagram not rendering"
- **Cause**: SVG rendering issue
- **Fix**: Check browser console for errors
- **Fallback**: Click components to see grid list instead

### "Components list is empty"
- **Cause**: Registry not loading
- **Fix**: Check backend logs
- **Verify**: `curl http://localhost:8000/api/execution-studio/components`

## 📈 What's Next

After testing Architecture View:

1. **Phase 2: Learn Mode** (coming next)
   - Click component → see explanation
   - Learn design patterns
   - Performance tips

2. **Phase 3: Before/After**
   - See data transformations
   - Quality metrics
   - Efficiency analysis

3. **Phase 4: Interactive Replay**
   - Step through execution
   - Set breakpoints
   - Debug decisions

## 🎬 Demo Flow

```
1. Start app (both servers running)
2. Ask chat question
3. Go to Execution Studio
4. See Architecture View
5. Click components
6. Check metrics
7. Read component descriptions (coming Phase 2)
8. Step through execution (coming Phase 4)
```

## 📚 Files Modified

### Backend
- `/backend/app/execution_studio/component_registry.py` (NEW)
- `/backend/app/routers/execution_studio_api.py` (UPDATED)

### Frontend
- `/frontend/src/components/execution-studio/ArchitectureView.tsx` (NEW)
- `/frontend/src/pages/ExecutionStudio.tsx` (UPDATED)

## 🚀 Go Live Checklist

- ✅ Component registry created
- ✅ API endpoints working
- ✅ Frontend component built
- ✅ Integration complete
- ✅ Both servers running
- ✅ Ready to test!

**Just visit http://localhost:5173 and start exploring!**
