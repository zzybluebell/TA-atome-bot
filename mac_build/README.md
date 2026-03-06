# AtomeDeskBundle Quick Guide (macOS)

## Normal Startup

1. Open `AtomeDeskBundle`
2. Double-click `StartAtomeDesk.command`
3. Open `http://localhost:8000` in your browser

## If You See “StartAtomeDesk.command Not Opened”

This is a macOS Gatekeeper block. Follow these steps:

1. In Finder, right-click `StartAtomeDesk.command` and choose **Open**
2. In the popup, click **Open** again
3. If it is still blocked, go to:
   - System Settings → Privacy & Security
   - Click **Open Anyway** near the bottom
4. Double-click `StartAtomeDesk.command` again

## If You See `address already in use` (Port 8000 Occupied)

Run this in Terminal:

```bash
lsof -ti tcp:8000 | xargs kill -9
```

Then double-click `StartAtomeDesk.command` again.
