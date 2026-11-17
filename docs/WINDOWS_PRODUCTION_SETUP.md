# Windows production setup and verification

## Prerequisites

Install Python 3.10+, FFmpeg/ffprobe, and a patched Node.js release supported by `remotion-composer/package.json` (22.23.4+, 24.22.1+, or 26.12.1+). Restart PowerShell so commands appear on PATH.

In PowerShell, clone your fork and run:

```powershell
git clone https://github.com/SEDFFDSF8947894/OpenMontage.git
cd OpenMontage
git checkout feature/arabic-video-production-readiness
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

The setup creates a Python virtual environment, installs dependencies, installs Remotion packages, and copies `.env.example` to `.env` only when absent. Configure API keys locally; never commit `.env`.

## Offline checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_production_readiness.py -v
.\.venv\Scripts\python.exe scripts\production_readiness.py
```

After generating a real video using the documented OpenMontage pipeline, verify its container, dimensions, duration, and optional audio:

```powershell
.\.venv\Scripts\python.exe scripts\production_readiness.py --video 'C:\path\to\output.mp4' --require-audio
```

A passing probe verifies only basic file metadata, not the quality, correctness, licensing, synchronization, or suitability of the generated video. A complete end-to-end acceptance test additionally requires real pipeline execution, provider entitlements, user approvals, and inspection of the final video. Do not run paid provider calls without reviewing costs.
