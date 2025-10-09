# Remote Long-Run Guide

## 🚀 Quick Start

Remote server: `andy@100.67.88.114` (Alienware via Tailscale)

### Prerequisites on Remote

1. **Start Qdrant service:**
   ```bash
   ssh andy@100.67.88.114 "docker-compose -f ~/searchforge/docker-compose.yml up -d qdrant"
   ```

2. **Populate Qdrant with demo data:**
   ```bash
   ssh andy@100.67.88.114 "cd ~/searchforge && python3 data/populate_qdrant.py"
   ```

## 📋 Configuration Variables

Edit these at the top of `run_long.sh` or pass as environment variables:

```bash
DURATION=3600        # Seconds per scenario (1 hour = 3600)
QPS=12              # Queries per second
BUCKET=10           # Bucket size in seconds
SCENARIOS="A"       # Space-separated: "A" or "A B C"
```

## 🎬 Control Commands

### 1. Check Status
```bash
ssh andy@100.67.88.114 "bash ~/searchforge/scripts/remote/status.sh"
```

### 2. View Live Logs (Scenario A)
```bash
ssh andy@100.67.88.114 "tail -f ~/runs/20251008_2113/logs/A.log"
```
Replace timestamp with current run (check status first).

### 3. Fetch Results to Local
```bash
export REMOTE_USER_HOST="andy@100.67.88.114"
export LOCAL_DST="$HOME/Downloads/autotuner_runs"
bash /Users/nanxinli/Documents/dev/searchforge/scripts/remote/fetch.sh
```

### 4. Kill Running Session
```bash
ssh andy@100.67.88.114 "tmux kill-session -t autotuner_long"
```

### 5. Attach to Session (Interactive)
```bash
ssh -t andy@100.67.88.114 "tmux attach -t autotuner_long"
```
Press `Ctrl+B` then `D` to detach without killing.

## 🔧 Modify Run Parameters

### Run B or C Scenarios
Edit `run_long.sh` and change:
```bash
SCENARIOS="B C"  # or "A B C" for all
```

### Extend Duration (2-3 hours)
```bash
DURATION=7200   # 2 hours
DURATION=10800  # 3 hours
```

Then re-upload and restart:
```bash
scp scripts/remote/run_long.sh andy@100.67.88.114:~/searchforge/scripts/remote/
ssh andy@100.67.88.114 'tmux kill-session -t autotuner_long; PACK_ROOT_TIMESTAMP=$(date +%Y%m%d_%H%M); tmux new-session -d -s autotuner_long "export DURATION=7200 QPS=12 BUCKET=10 SCENARIOS=\"B C\" PACK_ROOT=~/runs/${PACK_ROOT_TIMESTAMP} REMOTE_BASE=~/searchforge; cd ~/searchforge && bash ~/searchforge/scripts/remote/run_long.sh; exec bash"; echo "Started: ~/runs/${PACK_ROOT_TIMESTAMP}"'
```

## 📊 Results

After fetch completes:
```bash
open ~/Downloads/autotuner_runs/<timestamp>/index.html
```

## 🐛 Troubleshooting

### "Collection not found"
Start Qdrant and populate:
```bash
ssh andy@100.67.88.114 "cd ~/searchforge && docker-compose up -d qdrant && sleep 5 && python3 data/populate_qdrant.py"
```

### "ModuleNotFoundError"
Install dependencies:
```bash
ssh andy@100.67.88.114 "cd ~/searchforge && python3 -m pip install --user -r requirements.txt"
```

### Check tmux session status
```bash
ssh andy@100.67.88.114 "tmux list-sessions"
```

## 📝 File Locations

- **Scripts**: `~/searchforge/scripts/remote/`
- **Runs**: `~/runs/<timestamp>/`
- **Logs**: `~/runs/<timestamp>/logs/*.log`
- **Package**: `~/runs/<timestamp>.tgz`
