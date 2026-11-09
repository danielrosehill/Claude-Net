"""Agent Interconnect desktop client (Linux / Windows).

A small tray app showing the shared household thread (Alice, Bob and their
Claude agents). Polls the server every few seconds and raises a desktop
notification when someone else posts.

Config: ~/.config/agent-interconnect/config.json (Linux) or
%APPDATA%\\agent-interconnect\\config.json (Windows):
    {"server": "http://relay.example.ts.net:8790", "token": "..."}
Run with --tray to start hidden in the system tray (used for autostart).
"""

from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QPlainTextEdit, QPushButton, QSystemTrayIcon, QTextBrowser,
    QVBoxLayout, QWidget,
)

APP = "Agent Interconnect"
POLL_MS = 3000
COLOURS = {
    "alice": "#1f6feb",
    "bob": "#bf3989",
    "alice-claude": "#1a7f37",
    "bob-claude": "#9a6700",
}


def config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "agent-interconnect" / "config.json"


def load_config() -> dict:
    p = config_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_config(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def make_icon(unread: int = 0) -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#d97757" if unread else "#5b6b7a"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    p.setPen(QColor("white"))
    f = QFont()
    f.setBold(True)
    f.setPixelSize(28 if unread else 24)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, str(min(unread, 99)) if unread else "AI")
    p.end()
    return QIcon(pm)


class SetupDialog(QDialog):
    def __init__(self, cfg: dict):
        super().__init__()
        self.setWindowTitle(f"{APP} setup")
        form = QFormLayout(self)
        self.server = QLineEdit(cfg.get("server", "http://relay.example.ts.net:8790"))
        self.token = QLineEdit(cfg.get("token", ""))
        self.token.setEchoMode(QLineEdit.Password)
        form.addRow("Server", self.server)
        form.addRow("Token", self.token)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def values(self) -> dict:
        return {"server": self.server.text().strip().rstrip("/"), "token": self.token.text().strip()}


class ComposeBox(QPlainTextEdit):
    """Enter sends, Shift+Enter inserts a newline."""

    def __init__(self, on_send):
        super().__init__()
        self.on_send = on_send
        self.setPlaceholderText("Message (Enter to send, Shift+Enter for a new line)")
        self.setFixedHeight(70)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self.on_send()
            return
        super().keyPressEvent(e)


class Window(QMainWindow):
    def __init__(self, cfg: dict, start_hidden: bool):
        super().__init__()
        self.cfg = cfg
        self.me = None
        self.names: dict[str, str] = {}
        self.last_id = 0
        self.last_read = 0
        self.first_load = True
        self.messages: list[dict] = []
        self.net = QNetworkAccessManager(self)

        self.setWindowTitle(APP)
        self.resize(520, 640)
        self.setWindowIcon(make_icon())

        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(True)
        self.status = QLabel("Connecting…")
        self.to = QComboBox()
        self.to.addItem("Everyone", "all")
        self.compose = ComposeBox(self.send)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send)

        row = QHBoxLayout()
        row.addWidget(QLabel("To:"))
        row.addWidget(self.to, 1)
        row.addWidget(send_btn)
        lay = QVBoxLayout()
        lay.addWidget(self.view, 1)
        lay.addLayout(row)
        lay.addWidget(self.compose)
        lay.addWidget(self.status)
        w = QWidget()
        w.setLayout(lay)
        self.setCentralWidget(w)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=QApplication.quit)

        self.tray = QSystemTrayIcon(make_icon(), self)
        menu = QMenu()
        a_open = QAction("Open", self, triggered=self.show_window)
        a_setup = QAction("Settings…", self, triggered=self.setup)
        a_quit = QAction("Quit", self, triggered=QApplication.quit)
        menu.addAction(a_open)
        menu.addAction(a_setup)
        menu.addSeparator()
        menu.addAction(a_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.show_window() if r in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None
        )
        self.tray.messageClicked.connect(self.show_window)
        self.tray.setToolTip(APP)
        self.tray.show()

        self.timer = QTimer(self, interval=POLL_MS, timeout=self.poll)
        self.timer.start()
        self.load_me()
        if not start_hidden:
            self.show()

    # ---- networking ---------------------------------------------------------------
    def _req(self, path: str) -> QNetworkRequest:
        r = QNetworkRequest(QUrl(self.cfg["server"] + path))
        r.setRawHeader(b"Authorization", f"Bearer {self.cfg['token']}".encode())
        r.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        r.setTransferTimeout(10000)
        return r

    def _get(self, path, cb):
        reply = self.net.get(self._req(path))
        reply.finished.connect(lambda: self._done(reply, cb))

    def _post(self, path, data, cb):
        reply = self.net.post(self._req(path), QByteArray(json.dumps(data).encode()))
        reply.finished.connect(lambda: self._done(reply, cb))

    def _done(self, reply: QNetworkReply, cb):
        code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        body = bytes(reply.readAll())
        reply.deleteLater()
        if reply.error() != QNetworkReply.NoError and not code:
            self.status.setText(f"Offline: {reply.errorString()}")
            return
        if code == 401:
            self.status.setText("Token rejected: open Settings from the tray menu")
            return
        try:
            cb(json.loads(body or b"{}"))
        except Exception as e:  # noqa: BLE001
            self.status.setText(f"Error: {e}")

    # ---- behaviour ----------------------------------------------------------------
    def load_me(self):
        def got(d):
            self.me = d["you"]
            self.names = d["participants"]
            self.last_read = d.get("last_read", 0)
            self.to.clear()
            self.to.addItem("Everyone", "all")
            for k, v in self.names.items():
                if k != self.me:
                    self.to.addItem(v, k)
            self.setWindowTitle(f"{APP} — {d['name']}")
            self.poll()

        self._get("/api/me", got)

    def poll(self):
        if not self.me:
            self.load_me()
            return

        def got(d):
            new = d.get("messages", [])
            self.status.setText("Connected")
            if not new:
                return
            self.messages.extend(new)
            self.messages = self.messages[-500:]
            self.last_id = new[-1]["id"]
            self.render()
            incoming = [m for m in new if m["sender"] != self.me and m["id"] > self.last_read]
            if incoming and not self.first_load:
                m = incoming[-1]
                more = f" (+{len(incoming) - 1} more)" if len(incoming) > 1 else ""
                self.tray.showMessage(
                    f"{m['sender_name']}{more}", m["body"][:240], make_icon(1), 8000
                )
                if sys.platform == "win32":
                    QApplication.alert(self, 0)
            self.first_load = False
            self.update_unread()

        self._get(f"/api/messages?after={self.last_id}", got)

    def unread_count(self) -> int:
        return sum(1 for m in self.messages if m["sender"] != self.me and m["id"] > self.last_read)

    def update_unread(self):
        if self.isVisible() and self.isActiveWindow() and self.messages:
            self.mark_read()
        n = self.unread_count()
        self.tray.setIcon(make_icon(n))
        self.tray.setToolTip(f"{APP}: {n} unread" if n else APP)

    def mark_read(self):
        top = self.messages[-1]["id"]
        if top > self.last_read:
            self.last_read = top
            self._post("/api/read", {"last_id": top}, lambda d: None)
            self.tray.setIcon(make_icon(0))
            self.tray.setToolTip(APP)

    def render(self):
        parts = []
        for m in self.messages:
            colour = COLOURS.get(m["sender"], "#444")
            to = m.get("recipient", "all")
            to_txt = "" if to == "all" else f" → {html.escape(self.names.get(to, to))}"
            body = html.escape(m["body"]).replace("\n", "<br>")
            parts.append(
                f"<p style='margin:6px 0'><b style='color:{colour}'>{html.escape(m['sender_name'])}</b>"
                f"<span style='color:#888'>{to_txt} · {m['time']}</span><br>{body}</p>"
            )
        self.view.setHtml("".join(parts))
        sb = self.view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def send(self):
        text = self.compose.toPlainText().strip()
        if not text or not self.me:
            return
        self.compose.setEnabled(False)

        def sent(d):
            self.compose.setEnabled(True)
            if "error" in d:
                self.status.setText(f"Not sent: {d['error']}")
                return
            self.compose.clear()
            self.compose.setFocus()
            self.poll()

        self._post("/api/messages", {"body": text, "to": self.to.currentData()}, sent)

    def setup(self):
        dlg = SetupDialog(self.cfg)
        if dlg.exec():
            self.cfg.update(dlg.values())
            save_config(self.cfg)
            self.me, self.messages, self.last_id, self.first_load = None, [], 0, True
            self.load_me()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.mark_read() if self.messages else None

    def changeEvent(self, e):
        super().changeEvent(e)
        if self.isActiveWindow() and self.messages:
            self.mark_read()

    def closeEvent(self, e):
        e.ignore()
        self.hide()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setQuitOnLastWindowClosed(False)
    cfg = load_config()
    if not cfg.get("token"):
        dlg = SetupDialog(cfg)
        if not dlg.exec():
            return 0
        cfg.update(dlg.values())
        save_config(cfg)
    Window(cfg, start_hidden="--tray" in sys.argv)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
