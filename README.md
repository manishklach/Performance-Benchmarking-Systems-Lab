# speedtest-web

A lightweight web speed test (Ookla-style) with added quality metrics.

## Features
- Download speed (Mbps)
- Upload speed (Mbps)
- Latency (avg/min/max)
- Jitter
- Packet loss
- Loaded latency and bufferbloat estimate
- MOS estimate for call quality
- Data usage tracking (MB)
- Custom remote server URL for real WAN testing

## Project Structure
- `server.py` - Python HTTP API server + static hosting
- `static/index.html` - Web UI and test logic

## Prerequisites
- Python 3.9+
- Browser with Fetch/Web Crypto support

## Quick Start (Local Dev)

```powershell
cd C:\Users\ManishKL\Documents\Playground\speedtest-web
python server.py
```

Open in browser:
- `http://127.0.0.1:8765`

## Real Internet Speed Testing (Recommended)

Localhost/private-IP testing measures LAN speed, not ISP speed.

Deploy `server.py` on a public VPS/cloud host and set the UI **Server URL** to that public endpoint.

Example remote run:

```bash
export SPEEDTEST_HOST=0.0.0.0
export SPEEDTEST_PORT=8765
python3 server.py
```

Then use a public URL such as:
- `https://speed.yourdomain.com`
- `http://<public-ip>:8765`

## Environment Variables
- `SPEEDTEST_HOST` (default: `0.0.0.0`)
- `SPEEDTEST_PORT` (default: `8765`)

## Notes
- The test targets around 40 MB total transfer and may slightly exceed on fast links.
- For best accuracy, host server geographically close to your location (for India: Mumbai/Bangalore/Chennai/Hyderabad or Singapore fallback).

## License
MIT (see `LICENSE`)
