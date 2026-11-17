"""Native Windows desktop shell for OpenMontage. No paid API calls are made here."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QProcess, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QPlainTextEdit, QProgressBar, QSplitter, QStackedWidget,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget, QSpinBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path.home() / "Documents" / "OpenMontage Studio"
PROVIDERS = ("OpenAI", "Google", "fal.ai", "ElevenLabs", "Other")
STYLE = """
QMainWindow,QWidget { background:#10151f; color:#eaf0fa; font-size:13px; }
QFrame#sidebar { background:#161e2b; border-right:1px solid #283344; }
QPushButton { background:#26364d; border:1px solid #354a67; padding:9px 13px; border-radius:7px; }
QPushButton:hover { background:#344e72; }
QPushButton#primary { background:#4e71df; border-color:#4e71df; font-weight:600; }
QLineEdit,QPlainTextEdit,QListWidget,QComboBox,QSpinBox { background:#1b2635; color:#f0f4fc; border:1px solid #344459; border-radius:6px; padding:6px; }
QTabWidget::pane { border:1px solid #344459; }
QTabBar::tab { padding:10px; background:#1b2635; }
QTabBar::tab:selected { background:#344e72; }
QLabel#heading { font-size:22px; font-weight:700; }
"""

def default_project():
    return {"title":"Untitled project", "prompt":"", "script":"", "pipeline":"documentary-montage",
            "ratio":"16:9", "duration":60, "media":[], "scenes":[]}

class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenMontage Pro Studio — Desktop")
        self.resize(1350, 850)
        self.setMinimumSize(900, 620)
        self.settings = QSettings("OpenMontage", "ProStudio")
        self.project = default_project()
        self.project_path = None
        self.process = None
        self.setStyleSheet(STYLE)
        self._ui()
        self._load_preferences()
        self.statusBar().showMessage("Ready — local desktop preview; AI generation is not connected yet.")

    def _button(self, text, callback, primary=False):
        b = QPushButton(text)
        if primary:
            b.setObjectName("primary")
        b.clicked.connect(callback)
        return b

    def _ui(self):
        base = QWidget()
        self.setCentralWidget(base)
        layout = QHBoxLayout(base)
        layout.setContentsMargins(0,0,0,0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        brand = QLabel("◆ OpenMontage\n   PRO STUDIO")
        brand.setStyleSheet("font-size:18px;font-weight:700;padding:18px 6px;")
        side.addWidget(brand)
        self.pages = QStackedWidget()
        for label, builder in [
            ("✦ AI Studio",self._build_ai), ("▤ Editor",self._build_editor),
            ("▧ Media Library",self._build_media), ("⚙ Settings & APIs",self._build_settings)
        ]:
            side.addWidget(self._button(label,lambda _, n=self.pages.count():self.pages.setCurrentIndex(n)))
            self.pages.addWidget(builder())
        side.addStretch()
        side.addWidget(QLabel("Local-first • No automatic API charges"))
        layout.addWidget(sidebar)
        layout.addWidget(self.pages,1)
        self.setStatusBar(QStatusBar())
        menu = self.menuBar().addMenu("Project")
        for name, cb, shortcut in [
            ("New",self.new_project,"Ctrl+N"), ("Open",self.open_project,"Ctrl+O"),
            ("Save",self.save_project,"Ctrl+S"), ("Save As",self.save_project_as,"Ctrl+Shift+S")
        ]:
            a=QAction(name,self);a.setShortcut(shortcut);a.triggered.connect(cb);menu.addAction(a)

    def _page(self, title):
        w=QWidget(); v=QVBoxLayout(w);v.setContentsMargins(22,18,22,18)
        h=QLabel(title);h.setObjectName("heading");v.addWidget(h)
        return w,v

    def _build_ai(self):
        w,v=self._page("AI Production Studio")
        v.addWidget(QLabel("Project title"))
        self.title_edit=QLineEdit();v.addWidget(self.title_edit)
        v.addWidget(QLabel("Describe the video in Arabic or English"))
        self.prompt_edit=QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("اكتب فكرة الفيديو أو البرومبت بالتفصيل...")
        v.addWidget(self.prompt_edit,2)
        row=QHBoxLayout()
        self.pipeline=QComboBox();self.pipeline.addItems(["documentary-montage","cinematic","animation","animated-explainer","hybrid","talking-head","screen-demo","clip-factory","podcast-repurpose","character-animation","avatar-spokesperson","localization-dub"])
        self.ratio=QComboBox();self.ratio.addItems(["16:9","9:16","1:1"])
        self.duration=QSpinBox();self.duration.setRange(5,3600);self.duration.setSuffix(" sec")
        for label,widget in [("Pipeline",self.pipeline),("Aspect",self.ratio),("Duration",self.duration)]:
            row.addWidget(QLabel(label));row.addWidget(widget)
        v.addLayout(row)
        v.addWidget(QLabel("Script / narration"))
        self.script_edit=QPlainTextEdit();self.script_edit.setPlaceholderText("السيناريو أو التعليق الصوتي...")
        v.addWidget(self.script_edit,2)
        actions=QHBoxLayout()
        actions.addWidget(self._button("Save project",self.save_project,True))
        actions.addWidget(self._button("Run local preflight",self.run_preflight))
        actions.addWidget(self._button("Export agent brief",self.export_agent_brief))
        self.generate=self._button("Generate with AI — coming next",self.generation_info)
        actions.addWidget(self.generate)
        v.addLayout(actions)
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumHeight(125)
        v.addWidget(self.log)
        return w

    def _build_editor(self):
        w,v=self._page("Storyboard & Editor")
        v.addWidget(QLabel("Scene plan (manual planning; rendering integration is next milestone)"))
        self.scenes=QListWidget();v.addWidget(self.scenes,2)
        bar=QHBoxLayout()
        for label,cb in [("Add scene",self.add_scene),("Remove scene",self.remove_scene),
                         ("Move up",lambda:self.move_scene(-1)),("Move down",lambda:self.move_scene(1))]:
            bar.addWidget(self._button(label,cb))
        v.addLayout(bar)
        self.video=QVideoWidget();self.video.setMinimumHeight(220);v.addWidget(self.video,2)
        self.player=QMediaPlayer(self);self.audio=QAudioOutput(self)
        self.player.setAudioOutput(self.audio);self.player.setVideoOutput(self.video)
        play=QHBoxLayout()
        play.addWidget(self._button("Preview selected media",self.preview_media))
        play.addWidget(self._button("Play",self.player.play))
        play.addWidget(self._button("Pause",self.player.pause))
        v.addLayout(play)
        return w

    def _build_media(self):
        w,v=self._page("Media Library")
        v.addWidget(QLabel("Import local images, audio and video files. Nothing is uploaded."))
        self.media=QListWidget();v.addWidget(self.media)
        bar=QHBoxLayout()
        bar.addWidget(self._button("Import files",self.import_media,True))
        bar.addWidget(self._button("Remove selected",self.remove_media))
        bar.addWidget(self._button("Open media folder",self.open_media_folder))
        v.addLayout(bar)
        return w

    def _build_settings(self):
        w,v=self._page("Settings & API Credentials")
        v.addWidget(QLabel("Provider API keys are stored in Windows Credential Manager via keyring, never in project JSON."))
        form=QFormLayout()
        self.provider=QComboBox();self.provider.addItems(PROVIDERS)
        self.api_key=QLineEdit();self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Paste key locally — never share it in chat")
        self.output_edit=QLineEdit()
        form.addRow("Provider",self.provider);form.addRow("API key",self.api_key)
        form.addRow("Output folder",self.output_edit)
        v.addLayout(form)
        row=QHBoxLayout()
        row.addWidget(self._button("Save API key securely",self.save_key))
        row.addWidget(self._button("Delete saved API key",self.delete_key))
        row.addWidget(self._button("Save preferences",self.save_preferences,True))
        v.addLayout(row)
        v.addWidget(QLabel("Saving a key does not validate a subscription or make a paid API request."))
        v.addWidget(self._button("Check environment",self.run_preflight))
        v.addStretch()
        return w

    def _capture(self):
        self.project.update(title=self.title_edit.text().strip() or "Untitled project",
            prompt=self.prompt_edit.toPlainText(),script=self.script_edit.toPlainText(),
            pipeline=self.pipeline.currentText(),ratio=self.ratio.currentText(),
            duration=self.duration.value(),
            scenes=[self.scenes.item(i).text() for i in range(self.scenes.count())],
            media=[self.media.item(i).text() for i in range(self.media.count())])

    def _show_project(self):
        p=self.project
        self.title_edit.setText(p.get("title","Untitled project"))
        self.prompt_edit.setPlainText(p.get("prompt",""))
        self.script_edit.setPlainText(p.get("script",""))
        for widget,value in [(self.pipeline,p.get("pipeline","documentary-montage")),(self.ratio,p.get("ratio","16:9"))]:
            i=widget.findText(value)
            if i>=0:widget.setCurrentIndex(i)
        self.duration.setValue(int(p.get("duration",60)))
        self.scenes.clear();self.scenes.addItems(p.get("scenes",[]))
        self.media.clear();self.media.addItems(p.get("media",[]))

    def new_project(self):
        self.project=default_project();self.project_path=None;self._show_project()

    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,"Open project",str(PROJECT_DIR),"OpenMontage Project (*.json)")
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data,dict):raise ValueError("Expected a project object")
            self.project={**default_project(),**data}
            self.project_path=Path(path);self._show_project()
            self.statusBar().showMessage("Opened "+path)
        except (OSError,ValueError,TypeError) as e:QMessageBox.warning(self,"Open failed",str(e))

    def save_project(self):
        if not self.project_path:return self.save_project_as()
        self._capture()
        try:
            self.project_path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.project_path.with_suffix(".tmp")
            temp.write_text(json.dumps(self.project,ensure_ascii=False,indent=2),encoding="utf-8")
            os.replace(temp,self.project_path)
            self.statusBar().showMessage("Saved "+str(self.project_path))
        except OSError as e:QMessageBox.critical(self,"Save failed",str(e))

    def save_project_as(self):
        PROJECT_DIR.mkdir(parents=True,exist_ok=True)
        path,_=QFileDialog.getSaveFileName(self,"Save project",str(PROJECT_DIR/"project.json"),"OpenMontage Project (*.json)")
        if path:
            self.project_path=Path(path)
            self.save_project()

    def add_scene(self):
        text,ok=QInputDialog.getMultiLineText(self,"New scene","Scene description:")
        if ok and text.strip():self.scenes.addItem(text.strip())

    def remove_scene(self):
        row=self.scenes.currentRow()
        if row>=0:self.scenes.takeItem(row)

    def move_scene(self,step):
        row=self.scenes.currentRow();target=row+step
        if row>=0 and 0<=target<self.scenes.count():
            item=self.scenes.takeItem(row);self.scenes.insertItem(target,item);self.scenes.setCurrentRow(target)

    def import_media(self):
        files,_=QFileDialog.getOpenFileNames(self,"Import media",str(Path.home()),
            "Media (*.mp4 *.mov *.mkv *.mp3 *.wav *.png *.jpg *.jpeg *.webp);;All files (*)")
        existing={self.media.item(i).text() for i in range(self.media.count())}
        for f in files:
            if f not in existing:self.media.addItem(f)

    def remove_media(self):
        for item in self.media.selectedItems():self.media.takeItem(self.media.row(item))

    def preview_media(self):
        item=self.media.currentItem()
        if not item:return QMessageBox.information(self,"Preview","Select an item in Media Library first.")
        p=Path(item.text())
        if not p.is_file():return QMessageBox.warning(self,"Missing file",str(p))
        if p.suffix.lower() in (".mp4",".mov",".mkv",".mp3",".wav"):
            self.player.setSource(QUrl.fromLocalFile(str(p)));self.player.play();self.pages.setCurrentIndex(1)
        else:QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def open_media_folder(self):
        folder=Path(self.output_edit.text()).expanduser()
        folder.mkdir(parents=True,exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _load_preferences(self):
        self.output_edit.setText(str(self.settings.value("output",str(PROJECT_DIR/"Exports"))))
        self.restoreGeometry(self.settings.value("geometry",self.saveGeometry()))

    def save_preferences(self):
        self.settings.setValue("output",self.output_edit.text().strip())
        self.settings.setValue("geometry",self.saveGeometry());self.settings.sync()
        self.statusBar().showMessage("Preferences saved")

    def save_key(self):
        key=self.api_key.text().strip()
        if not key:return QMessageBox.warning(self,"Missing key","Enter an API key.")
        try:
            import keyring
            keyring.set_password("OpenMontageProStudio",self.provider.currentText(),key)
            self.api_key.clear()
            QMessageBox.information(self,"Saved","Credential stored in OS credential store.")
        except Exception as e:QMessageBox.critical(self,"Credential error",str(e))

    def delete_key(self):
        try:
            import keyring
            keyring.delete_password("OpenMontageProStudio",self.provider.currentText())
            QMessageBox.information(self,"Deleted","Credential deleted.")
        except Exception as e:QMessageBox.warning(self,"Credential error",str(e))

    def run_preflight(self):
        if self.process is not None and self.process.state()!=QProcess.ProcessState.NotRunning:
            return
        self.pages.setCurrentIndex(0)
        self.log.appendPlainText("Running local readiness checks...")
        self.process=QProcess(self)
        self.process.setWorkingDirectory(str(ROOT))
        self.process.readyReadStandardOutput.connect(lambda:self.log.appendPlainText(bytes(self.process.readAllStandardOutput()).decode(errors="replace")))
        self.process.readyReadStandardError.connect(lambda:self.log.appendPlainText(bytes(self.process.readAllStandardError()).decode(errors="replace")))
        self.process.finished.connect(lambda code,status:self.statusBar().showMessage("Preflight exit code: "+str(code)))
        self.process.start(sys.executable,[str(ROOT/"scripts"/"production_readiness.py")])

    def export_agent_brief(self):
        """Export a reviewable brief for an OpenMontage-compatible agent, without execution."""
        self._capture()
        selected = self.project["pipeline"]
        manifest = ROOT / "pipeline_defs" / (selected + ".yaml")
        if not manifest.is_file():
            return QMessageBox.warning(self, "Pipeline missing", "Cannot locate manifest: " + str(manifest))
        output = Path(self.output_edit.text().strip() or str(PROJECT_DIR / "Exports")).expanduser()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export agent brief", str(PROJECT_DIR / "production_brief.md"), "Markdown (*.md)")
        if not path:
            return
        safe_title = self.project["title"].replace("\\r", " ").replace("\\n", " ")
        brief = (
            "# OpenMontage production request\\n\\n"
            "This is a handoff document, NOT an executed production.\\n"
            "Follow AGENT_GUIDE.md and PROJECT_CONTEXT.md. The AI agent must read the selected "
            "pipeline manifest, stage director skills and provider-specific skills, run preflight, "
            "estimate costs, and request approval before any paid or consequential generation.\\n\\n"
            f"## Title\\n{safe_title}\\n\\n"
            f"## Pipeline\\n{selected}\\n\\n"
            f"## Duration\\n{self.project['duration']} seconds\\n\\n"
            f"## Aspect ratio\\n{self.project['ratio']}\\n\\n"
            f"## Requested output directory\\n{output}\\n\\n"
            f"## Prompt\\n{self.project['prompt']}\\n\\n"
            f"## Script\\n{self.project['script']}\\n\\n"
            "## Planned scenes\\n" +
            "\\n".join("- " + str(scene) for scene in self.project["scenes"]) +
            "\\n\\n## Local media paths\\n" +
            "\\n".join("- " + str(media) for media in self.project["media"]) +
            "\\n\\n## Approval\\nDo not incur costs or publish without explicit user approval.\\n"
        )
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(brief, encoding="utf-8")
            self.statusBar().showMessage("Exported agent brief: " + str(target))
            QMessageBox.information(self, "Brief exported", "Saved production brief. No AI generation was started.")
        except OSError as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def generation_info(self):
        QMessageBox.information(self,"Not connected yet",
            "The desktop UI currently saves prompts, scripts, scenes, media and credentials. "
            "AI pipeline orchestration and paid generation are NOT connected. No API call was made.")

    def closeEvent(self,event):
        self.save_preferences()
        super().closeEvent(event)

def main():
    app=QApplication(sys.argv)
    app.setApplicationName("OpenMontage Pro Studio")
    app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    window=Studio();window.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())
