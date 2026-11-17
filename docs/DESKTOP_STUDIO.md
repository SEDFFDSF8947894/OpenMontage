# OpenMontage Pro Studio (Windows, first milestone)

This is a **native PySide6/Qt desktop window**, not a Chrome-based web application. It is an early functional foundation, **not** a complete AI generation or NLE system.

## Install on an already configured Windows clone

From PowerShell, in the repository root:

```powershell
git pull origin feature/arabic-video-production-readiness
powershell -ExecutionPolicy Bypass -File .\scripts\install_desktop_studio.ps1
```

Double-click **OpenMontage Pro Studio** on the desktop. The shortcut uses the project's virtual environment `pythonw.exe` and does not launch a console or browser. If the app does not appear, run `.\.venv\Scripts\python.exe -m desktop_studio` in PowerShell to see diagnostic errors.

## Working features

- AI Studio: project title, Arabic/English prompt, script, pipeline label, aspect ratio, target duration.
- Save / Open projects as UTF-8 JSON in your chosen location (default Documents/OpenMontage Studio).
- Storyboard: add, remove and reorder text scene descriptions.
- Media library: import local files, remove entries, preview supported video/audio using Qt multimedia, open images externally.
- Preferences: output directory saved with QSettings; window geometry restored.
- API credentials: `keyring` stores provider secrets in the OS credential store, **not** in project JSON, QSettings, logs, or the Git repository. Never commit secrets.
- Run existing `scripts/production_readiness.py` as a nonblocking subprocess.

## Important limitations

- **AI generation is not connected.** The Generate button explicitly says so and makes no requests.
- Saving provider credentials does **not** configure OpenMontage's existing agent/pipeline tools or validate connectivity. Provider mapping and pipeline adapters must be built and tested.
- No timeline compositor, AI media retrieval, automatic narration, export render, or installer EXE yet.
- No paid API requests are made from this app.
- Qt Multimedia playback depends on local codec support.
- Do not share `projects/*.json` if prompts/scripts are sensitive. API secrets are not stored in those files.
- The repository's existing `npm audit` warnings still require review before deploying to untrusted environments.

## Next development milestones

1. Integrate a pipeline preflight and provider capability audit with OpenMontage's existing agent-led pipeline contract.
2. Design a gated agent adapter with explicit cost and provider confirmation before paid calls.
3. Build real editable timeline data, preview and rendering integration.
4. Package and test a signed Windows installer.

See `AGENT_GUIDE.md` for the required pipeline orchestration and approval contract.
