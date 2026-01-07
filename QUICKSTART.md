# 🚀 Quick Start Guide - Claude Code CLI

## Your Files Are Ready!

You now have a complete setup for building with Claude Code CLI:

```
your_project/
├── kalshi_nba_paper_trading_prd.md    ✅ Complete PRD (68 pages)
├── kalshi_openapi.yaml                ✅ Kalshi API spec
├── sports_openapi.yaml                ✅ balldontlie.io API spec
├── CLAUDE.md                          ✅ Instructions for Claude (READ THIS!)
├── PROGRESS.md                        ✅ Iteration tracker
└── ARCHITECTURE.md                    ✅ Current state tracker
```

---

## 🎯 Your First Prompt (Copy-Paste Ready)

**Open your terminal in the project directory and run:**

```bash
claude-code "Read CLAUDE.md and complete the task for Iteration 1. Create the complete backend project structure, implement the Supabase database schema with all 12 tables and indexes from the PRD, setup FastAPI skeleton, and configure environment management. When complete, update PROGRESS.md with Iteration 1 status and ARCHITECTURE.md with what was implemented."
```

---

## 📋 How This System Works

### The 3-File System

**CLAUDE.md** (Instructions)
- Claude reads this FIRST every session
- Contains current task and rules
- You update the "Your Task This Session" section before each prompt

**PROGRESS.md** (What's Done)
- Tracks each iteration with status
- Claude checks this to avoid redoing work
- Claude updates this after completing tasks

**ARCHITECTURE.md** (How It Works)
- Living documentation of current system state
- Shows what's implemented and how to use it
- Claude updates this as components are built

### The Workflow

```
1. You update CLAUDE.md with next task
   ↓
2. Claude reads CLAUDE.md for instructions
   ↓
3. Claude checks PROGRESS.md (what's already done)
   ↓
4. Claude checks ARCHITECTURE.md (current state)
   ↓
5. Claude builds the feature
   ↓
6. Claude updates PROGRESS.md (new iteration)
   ↓
7. Claude updates ARCHITECTURE.md (new components)
   ↓
8. REPEAT for next feature
```

---

## 🎮 Example: Second Iteration

After Iteration 1 completes, you'd update CLAUDE.md:

**Change this section:**
```markdown
## Your Task This Session
Build the Kalshi API integration (REST + WebSocket)

Specifically:
1. Implement Kalshi REST API client from kalshi_openapi.yaml
2. Create WebSocket connection with async processing
3. Implement orderbook update handling
4. Add reconnection logic with exponential backoff
5. Parse Kalshi tickers to extract game info
6. Test connection and data flow
```

**Then run:**
```bash
claude-code "Read CLAUDE.md and complete the Iteration 2 task. Build the complete Kalshi integration with REST API client and WebSocket connection. Update PROGRESS.md and ARCHITECTURE.md when complete."
```

---

## 💡 Pro Tips

### 1. Be Specific in CLAUDE.md
✅ Good: "Implement Sharp Line Detection strategy from PRD Section 5.1 with configurable threshold parameter"
❌ Bad: "Add a trading strategy"

### 2. Let Claude Work Autonomously
- Don't micromanage - let it figure out implementation details
- Trust the PRD specifications
- Check results after completion

### 3. Use PROGRESS.md to Track Issues
If something doesn't work, add it to "Known Issues" section:
```markdown
## 🐛 Known Issues
- Kalshi WebSocket disconnects after 1 hour (need keep-alive)
- Ticker parser fails on playoff games (add handling)
```

### 4. Keep ARCHITECTURE.md Updated
After each iteration, make sure Claude added:
- What was implemented
- How to use it (code examples)
- Any decisions made

### 5. Review Before Next Iteration
Before starting Iteration 2, check:
- [ ] Did Iteration 1 complete successfully?
- [ ] Are files in expected locations?
- [ ] Does code match PRD specifications?
- [ ] Are PROGRESS.md and ARCHITECTURE.md updated?

---

## 📅 Suggested Iteration Plan

### Week 1 (Iterations 1-3)
**Iteration 1:** Backend structure + Supabase schema (TODAY!)
**Iteration 2:** Kalshi API integration
**Iteration 3:** balldontlie.io API integration

### Week 2 (Iterations 4-8)
**Iteration 4:** Data aggregation layer
**Iteration 5:** Implement Strategy 1 (Sharp Line)
**Iteration 6:** Implement Strategy 2 (Momentum)
**Iteration 7:** Implement Strategy 3 (EV Multi)
**Iteration 8:** Implement Strategies 4-5 (Mean Rev, Correlation)

### Week 3 (Iterations 9-12)
**Iteration 9:** Order execution simulator
**Iteration 10:** Position manager + P&L calculator
**Iteration 11:** Risk management system
**Iteration 12:** Backend WebSocket server for frontend

### Week 4 (Switch to Cursor for Frontend)
**Iteration 13+:** Build Next.js dashboard

---

## 🐛 Troubleshooting

### "Claude keeps redoing the same work"
→ Make sure it's checking PROGRESS.md. Add to CLAUDE.md:
```markdown
CRITICAL: Before starting ANY work, read PROGRESS.md to see what's already done!
```

### "Claude isn't updating tracking files"
→ Explicitly remind it in your prompt:
```bash
claude-code "Complete the task AND UPDATE BOTH PROGRESS.MD AND ARCHITECTURE.MD"
```

### "Code doesn't match PRD"
→ Add to CLAUDE.md rules:
```markdown
MANDATORY: Follow PRD specifications EXACTLY. Do not deviate.
```

---

## 🎯 Success Checklist (After Iteration 1)

- [ ] `backend/` directory exists with proper structure
- [ ] `backend/database/schema.sql` has all 12 tables
- [ ] `backend/main.py` runs without errors
- [ ] `.env.example` created with all variables
- [ ] `requirements.txt` has all dependencies
- [ ] PROGRESS.md shows "Iteration 1: ✅ Complete"
- [ ] ARCHITECTURE.md shows "Backend Infrastructure: ✅ Complete"

---

## 🚀 Ready to Build!

**Your next steps:**
1. Copy all 6 files to your project directory
2. Open terminal in that directory
3. Run the first prompt (see "Your First Prompt" above)
4. Watch Claude build your backend infrastructure!
5. Review results and proceed to Iteration 2

---

## 📞 Need Help?

**Common Questions:**

**Q: Can I change the task mid-iteration?**
A: Yes! Just update CLAUDE.md and give a new prompt.

**Q: What if Claude makes a mistake?**
A: Tell it specifically what's wrong and ask it to fix. Add the issue to PROGRESS.md so it doesn't repeat.

**Q: Should I review code after each iteration?**
A: Yes! Quickly check that it matches PRD specs. Better to catch issues early.

**Q: Can I skip the tracking files?**
A: You CAN, but you'll lose context across sessions. The tracking files are what make this system work well.

---

**Good luck! Let's build this thing! 🏀📈**
