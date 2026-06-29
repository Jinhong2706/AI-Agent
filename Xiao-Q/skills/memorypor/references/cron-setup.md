# Cron Setup Guide — Self-Improving Skill

This guide shows how to set up automated heartbeat maintenance using cron.

## Quick Setup

### For macOS/Linux

Add to your crontab (`crontab -e`):

```cron
# Self-Improving Heartbeat - Every hour
0 * * * * $HOME/self-improving/scripts/heartbeat.sh >> $HOME/self-improving/heartbeat.log 2>&1

# Self-Improving Stats - Daily at 9 AM
0 9 * * * $HOME/self-improving/scripts/stats.sh
```

> Note: If cron does not expand `~`, use `$HOME` instead as shown above, or use the full path like `/Users/yourname/self-improving/`.

### For Windows

Use Task Scheduler or create a `.bat` file:

```batch
# Create heartbeat-task.bat
@echo off
cd /d %USERPROFILE%\self-improving
call scripts\heartbeat.bat
```

Then schedule via Task Scheduler:
```
schtasks /create /tn "Self-Improving Heartbeat" /tr "path\to\heartbeat-task.bat" /sc hourly
```

## Cron Expressions Reference

| Schedule | Cron Expression |
|----------|---------------|
| Every hour | `0 * * * *` |
| Every 30 minutes | `*/30 * * * *` |
| Every 6 hours | `0 */6 * * *` |
| Daily at 9 AM | `0 9 * * *` |
| Daily at 9 PM | `0 21 * * *` |
| Weekly (Sunday 3 AM) | `0 3 * * 0` |
| Monthly (1st day 3 AM) | `0 3 1 * *` |

## Recommended Schedules

### Light Usage (<5h/day)

```cron
# Heartbeat every 6 hours
0 */6 * * * $HOME/self-improving/scripts/heartbeat.sh
```

### Normal Usage (5-10h/day)

```cron
# Heartbeat every 2 hours
0 */2 * * * $HOME/self-improving/scripts/heartbeat.sh

# Stats daily at 9 PM
0 21 * * * $HOME/self-improving/scripts/stats.sh
```

### Heavy Usage (>10h/day)

```cron
# Heartbeat every hour
0 * * * * $HOME/self-improving/scripts/heartbeat.sh

# Stats morning and evening
0 9 * * * $HOME/self-improving/scripts/stats.sh
0 21 * * * $HOME/self-improving/scripts/stats.sh
```

### Heavy Usage with Memory Compaction

```cron
# Heartbeat every hour
0 * * * * $HOME/self-improving/scripts/heartbeat.sh

# Memory stats every 12 hours
0 */12 * * * $HOME/self-improving/scripts/stats.sh

# Full export daily at midnight (before compaction)
0 0 * * * $HOME/self-improving/scripts/export.sh $HOME/self-improving/backups/self-improving-$(date +\%Y\%m\%d).zip
```

## Setup Instructions

### 1. Find Your Skill Directory

```bash
# Usually one of these:
ls ~/self-improving
ls ~/.claude/skills/self-improving
ls /path/to/skills/self-improving
```

### 2. Test Scripts Manually

Before scheduling, test that scripts work:

```bash
bash ~/self-improving/scripts/heartbeat.sh
bash ~/self-improving/scripts/stats.sh
```

### 3. Edit Crontab

```bash
crontab -e
```

### 4. Add Your Schedule

Copy the appropriate cron line from above, replacing `/path/to/scripts/` with your actual path.

### 5. Verify Installation

```bash
crontab -l
```

## Log Rotation

For hourly heartbeat, consider adding log rotation:

```cron
# Rotate heartbeat log weekly
0 0 * * 0 truncate -s 0 $HOME/self-improving/heartbeat.log
```

Or use `logrotate` (Linux/macOS):

```bash
# /etc/logrotate.d/self-improving
$HOME/self-improving/heartbeat.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user group
}
```

## Troubleshooting

### Cron Not Running?

Check if cron is running:
```bash
# Linux
ps aux | grep cron

# macOS
sudo launchctl list | grep cron
```

### Script Path Issues?

Use absolute paths in cron. The `~` and `$HOME` may not expand correctly.

### Permission Denied?

Make sure scripts are executable:
```bash
chmod +x ~/self-improving/scripts/*.sh
```

### Environment Variables?

Cron has minimal environment. If needed, set explicitly:
```cron
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/Users/yourname
SELF_IMPROVING_DIR=/Users/yourname/self-improving
0 * * * * $HOME/self-improving/scripts/heartbeat.sh
```

## Alternative: Launchd (macOS)

For macOS, consider `launchd` instead of cron:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.self-improving.heartbeat</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/yourname/self-improving/scripts/heartbeat.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer> <!-- seconds -->
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Save to `~/Library/LaunchAgents/com.self-improving.heartbeat.plist` and load with:
```bash
launchctl load ~/Library/LaunchAgents/com.self-improving.heartbeat.plist
```

## Manual Trigger

To manually trigger heartbeat from anywhere:

```bash
# Add to your shell profile
alias heartbeat-self-improving='bash ~/self-improving/scripts/heartbeat.sh'
```

Then use:
```bash
heartbeat-self-improving
```
