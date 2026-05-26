import json
import ssl
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import paho.mqtt.client as mqtt


MQTT_HOST = "AquaHub2.azure-devices.net"
MQTT_PORT = 8883
MQTT_CLIENT_ID = "aqsdemo_evergreen5"
MQTT_TOPIC = "devices/aqsdemo_evergreen5/messages/events/"
MQTT_KEEPALIVE = 900
MQTT_QOS = 1
MQTT_CLEAN_SESSION = True

DEFAULT_RSSI = -65
DEFAULT_MAC = "AA:BB:CC:DD:EE:FF"
DEFAULT_DATA = "0201041AFFFFFF0215AACC00AA55EE7755AACC00AA55EE77555115511500"
DEFAULT_GWID = "1"


class AquaMQTTPublisherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AquaHub2 MQTT Publisher")
        self.root.geometry("780x680")
        self.root.resizable(True, True)

        self.client = None
        self.connected = False

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.mac_var = tk.StringVar(value=DEFAULT_MAC)
        self.status_var = tk.StringVar(value="Not connected")

        self.payload_text = None
        self.log_text = None

        self._apply_theme()
        self._build_ui()
        self._refresh_payload()

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        BG   = "#1e1e2e"
        SURF = "#2a2a3e"
        ACC  = "#7c6af7"
        TXT  = "#e0e0f0"
        SUB  = "#8888aa"

        self.root.configure(bg=BG)

        style.configure(".",
            background=BG,
            foreground=TXT,
            fieldbackground=SURF,
            bordercolor="#3a3a5a",
            troughcolor=SURF,
            font=("Segoe UI", 10),
        )
        style.configure("TFrame",       background=BG)
        style.configure("TLabelframe",  background=BG, foreground=SUB, bordercolor="#3a3a5a")
        style.configure("TLabelframe.Label", background=BG, foreground=SUB, font=("Segoe UI", 9, "bold"))
        style.configure("TLabel",       background=BG, foreground=TXT)
        style.configure("Sub.TLabel",   background=BG, foreground=SUB, font=("Segoe UI", 9))
        style.configure("TEntry",       fieldbackground=SURF, foreground=TXT, bordercolor="#3a3a5a", insertcolor=TXT)
        style.configure("TButton",      background=SURF, foreground=TXT, bordercolor="#3a3a5a", focuscolor=SURF)
        style.map("TButton",
            background=[("active", "#3a3a5a"), ("pressed", "#2a2a3e")],
            foreground=[("active", TXT)],
        )

        # Publish button — accent colour
        style.configure("Publish.TButton",
            background=ACC,
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
            padding=(20, 8),
        )
        style.map("Publish.TButton",
            background=[("active", "#9980ff"), ("pressed", "#6655dd")],
        )

        # Status colours
        style.configure("OK.TLabel",    background=BG, foreground="#4ec97c", font=("Segoe UI", 10, "bold"))
        style.configure("ERR.TLabel",   background=BG, foreground="#f07070", font=("Segoe UI", 10, "bold"))
        style.configure("INFO.TLabel",  background=BG, foreground="#f0c070", font=("Segoe UI", 10, "bold"))

        self._colors = dict(BG=BG, SURF=SURF, ACC=ACC, TXT=TXT, SUB=SUB)

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        C = self._colors
        pad = dict(padx=16, pady=6)

        root_frame = ttk.Frame(self.root)
        root_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Header
        ttk.Label(root_frame,
            text="AquaHub2 MQTT Publisher",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 2))
        ttk.Label(root_frame,
            text="Fill in credentials and beacon MAC, then click Publish.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        # Fixed settings (collapsible-style read-only block)
        fixed = ttk.LabelFrame(root_frame, text="Connection Settings (read-only)", padding=10)
        fixed.pack(fill=tk.X, pady=(0, 10))
        settings = [
            ("Host",      MQTT_HOST),
            ("Port",      str(MQTT_PORT)),
            ("Client ID", MQTT_CLIENT_ID),
            ("Topic",     MQTT_TOPIC),
            ("QoS",       str(MQTT_QOS)),
            ("Keepalive", f"{MQTT_KEEPALIVE} s"),
        ]
        grid = ttk.Frame(fixed)
        grid.pack(fill=tk.X)
        for i, (lbl, val) in enumerate(settings):
            col = (i % 3) * 2
            row = i // 3
            ttk.Label(grid, text=lbl + ":", style="Sub.TLabel").grid(row=row, column=col,   sticky="w", padx=(0, 4), pady=2)
            ttk.Label(grid, text=val).grid(                         row=row, column=col+1,  sticky="w", padx=(0, 24), pady=2)

        # Credentials
        creds = ttk.LabelFrame(root_frame, text="Credentials", padding=10)
        creds.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(creds, text="Username").grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Entry(creds, textvariable=self.username_var).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(creds, text="Password / SAS Token").grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 2))
        ttk.Entry(creds, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky="ew", padx=(16, 0), pady=(0, 8))

        ttk.Label(creds, text="Beacon MAC Address").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.mac_entry = ttk.Entry(creds, textvariable=self.mac_var, width=22)
        self.mac_entry.grid(row=3, column=0, sticky="w")
        self.mac_var.trace_add("write", lambda *_: self._refresh_payload())

        creds.columnconfigure(0, weight=1)
        creds.columnconfigure(1, weight=3)

        # Payload preview
        prev = ttk.LabelFrame(root_frame, text="Payload Preview", padding=10)
        prev.pack(fill=tk.X, pady=(0, 10))
        self.payload_text = scrolledtext.ScrolledText(
            prev,
            height=3,
            font=("Consolas", 10),
            bg=C["SURF"], fg=C["TXT"],
            insertbackground=C["TXT"],
            relief="flat",
            bd=0,
        )
        self.payload_text.pack(fill=tk.X)

        # Publish button + status on the same row
        action_row = ttk.Frame(root_frame)
        action_row.pack(fill=tk.X, pady=(0, 10))

        self.publish_btn = ttk.Button(
            action_row,
            text="  ▶  Publish",
            style="Publish.TButton",
            command=self._publish_clicked,
        )
        self.publish_btn.pack(side=tk.LEFT)

        self.disconnect_btn = ttk.Button(
            action_row,
            text="Disconnect",
            command=self._disconnect_clicked,
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.status_label = ttk.Label(
            action_row,
            textvariable=self.status_var,
            style="INFO.TLabel",
        )
        self.status_label.pack(side=tk.LEFT, padx=(16, 0))

        # Log
        log_frame = ttk.LabelFrame(root_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Consolas", 9),
            bg=C["SURF"], fg=C["TXT"],
            relief="flat",
            bd=0,
            state=tk.DISABLED,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _log(self, message):
        if not self.log_text:
            return
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _set_status(self, message, style="INFO.TLabel"):
        self.status_var.set(message)
        self.status_label.configure(style=style)
        self._log(message)

    def _normalize_mac(self, mac):
        return mac.strip().upper()

    def _is_valid_mac(self, mac):
        parts = mac.split(":")
        if len(parts) != 6:
            return False
        for part in parts:
            if len(part) != 2:
                return False
            try:
                int(part, 16)
            except ValueError:
                return False
        return True

    def _build_payload(self):
        return json.dumps({
            "RSSI": DEFAULT_RSSI,
            "MAC":  self._normalize_mac(self.mac_var.get()),
            "Data": DEFAULT_DATA,
            "GWID": DEFAULT_GWID,
        }, separators=(",", ":"))

    def _refresh_payload(self):
        if not self.payload_text:
            return
        mac = self._normalize_mac(self.mac_var.get())
        payload = json.dumps({
            "RSSI": DEFAULT_RSSI,
            "MAC":  mac,
            "Data": DEFAULT_DATA,
            "GWID": DEFAULT_GWID,
        }, separators=(",", ":"))
        self.payload_text.delete("1.0", tk.END)
        self.payload_text.insert(tk.END, payload)

    def _validate_inputs(self):
        if not self.username_var.get().strip():
            messagebox.showerror("Missing Username", "Enter the MQTT username.")
            return False
        if not self.password_var.get().strip():
            messagebox.showerror("Missing Password", "Enter the MQTT password / SAS token.")
            return False
        mac = self._normalize_mac(self.mac_var.get())
        if not self._is_valid_mac(mac):
            messagebox.showerror("Invalid MAC", "MAC must be in the format AA:BB:CC:DD:EE:FF")
            return False
        self.mac_var.set(mac)
        self._refresh_payload()
        return True

    # ── Publish flow ───────────────────────────────────────────────────────

    def _publish_clicked(self):
        if not self._validate_inputs():
            return
        self.publish_btn.config(state=tk.DISABLED)
        self._set_status("Connecting…", "INFO.TLabel")
        threading.Thread(target=self._connect_and_publish, daemon=True).start()

    def _connect_and_publish(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        payload  = self.payload_text.get("1.0", tk.END).strip()

        try:
            client = mqtt.Client(
                client_id=MQTT_CLIENT_ID,
                clean_session=MQTT_CLEAN_SESSION,
                protocol=mqtt.MQTTv311,
            )
            client.username_pw_set(username=username, password=password)
            client.tls_set(
                ca_certs=None, certfile=None, keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
                ciphers=None,
            )
            client.tls_insecure_set(False)

            # Block until connected (or timeout)
            connected_event = threading.Event()
            connect_rc = [None]

            def on_connect(c, ud, flags, rc):
                connect_rc[0] = rc
                connected_event.set()

            client.on_connect = on_connect
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
            client.loop_start()

            if not connected_event.wait(timeout=15):
                raise TimeoutError("Timed out waiting for broker connection.")

            if connect_rc[0] != 0:
                raise ConnectionRefusedError(f"Broker rejected connection (rc={connect_rc[0]}).")

            self.root.after(0, lambda: self._set_status("Connected — publishing…", "INFO.TLabel"))

            # Publish
            published_event = threading.Event()
            pub_mid = [None]

            def on_publish(c, ud, mid):
                pub_mid[0] = mid
                published_event.set()

            client.on_publish = on_publish
            result = client.publish(MQTT_TOPIC, payload=payload, qos=MQTT_QOS, retain=False)

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Publish call failed (rc={result.rc}).")

            published_event.wait(timeout=10)

            client.loop_stop()
            client.disconnect()

            msg_id = pub_mid[0]
            self.root.after(0, lambda: self._set_status(
                f"Published successfully  (mid={msg_id})", "OK.TLabel"
            ))
            self.root.after(0, lambda: self._log(f"Topic:   {MQTT_TOPIC}"))
            self.root.after(0, lambda: self._log(f"Payload: {payload}"))

        except Exception as exc:
            self.root.after(0, lambda: self._set_status(f"Error: {exc}", "ERR.TLabel"))

        finally:
            self.root.after(0, lambda: self.publish_btn.config(state=tk.NORMAL))

    # ── Disconnect ─────────────────────────────────────────────────────────

    def _disconnect_clicked(self):
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
            self.connected = False
            self._set_status("Disconnected.", "INFO.TLabel")
        except Exception as exc:
            self._set_status(f"Disconnect error: {exc}", "ERR.TLabel")


def main():
    root = tk.Tk()
    AquaMQTTPublisherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
