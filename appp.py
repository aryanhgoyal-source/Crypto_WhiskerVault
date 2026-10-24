import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from paths import KEYS, ENCRYPTED, DECRYPTED, SIGNATURES
from keygen import generate_keys
from cyphering import encrypt_file, decrypt_file
from integrity import sign_file, verify_file
from audit_log import get_logs

ctk.set_appearance_mode("dark")

# 🐱 cat palette: (light mode, dark mode)
BG = ("#fff6ea", "#2a1f17")
SIDEBAR = ("#f7dcc0", "#382a1f")
CARD = ("#ffffff", "#3d2e22")
ORANGE = ("#f4a261", "#e9853d")
ORANGE_HOVER = ("#e76f51", "#f4b27a")
NAV_TEXT = ("#5a3a22", "#f5e1cc")
TEXT = ("gray10", "gray90")
INK = "#2b1a0e"
GREEN, RED, AMBER = "#2e7d32", "#c62828", "#ef6c00"

CAT = "/\\_/\\\n( o.o )\n > ^ <"


def key(user, kind):
    return os.path.join(KEYS, f"{user}_{kind}.pem")


def btn(parent, text, command, **kw):
    opts = dict(fg_color=ORANGE, hover_color=ORANGE_HOVER, text_color=INK, corner_radius=20)
    opts.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **opts)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Whisker Vault")
        self.geometry("1000x660")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self.menus = []
        self.last_opened = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {
            "send": self.build_send(),
            "receive": self.build_receive(),
            "logs": self.build_logs(),
            "users": self.build_users(),
        }
        self.refresh_users()
        self.show("send")

    # ---------- layout helpers ----------
    def build_sidebar(self):
        bar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=SIDEBAR)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_propagate(False)

        ctk.CTkLabel(bar, text="🐱 Whisker\nVault", font=("Segoe UI", 24, "bold"),
                     justify="left", text_color=TEXT).pack(padx=20, pady=(30, 0), anchor="w")
        ctk.CTkLabel(bar, text="secure document vault", text_color=NAV_TEXT,
                     font=("Segoe UI", 11)).pack(padx=20, pady=(0, 25), anchor="w")

        self.nav = {}
        for k, text in (("send", "🐟  Send Document"), ("receive", "🐭  Receive Document"),
                        ("logs", "🐾  Audit Log"), ("users", "😺  Users & Keys")):
            b = btn(bar, text, lambda k=k: self.show(k), anchor="w", height=40,
                    fg_color="transparent", text_color=NAV_TEXT, hover_color=("#efc9a3", "#4d3a2b"))
            b.pack(fill="x", padx=12, pady=4)
            self.nav[k] = b

        self.sw = ctk.CTkSwitch(bar, text="Night mode", progress_color=ORANGE,
                                text_color=NAV_TEXT, command=self.toggle_theme)
        self.sw.select()
        self.sw.pack(side="bottom", pady=(0, 25))
        ctk.CTkLabel(bar, text=CAT, font=("Consolas", 18), text_color=NAV_TEXT).pack(side="bottom", pady=10)

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.sw.get() else "light")

    def show(self, name):
        for p in self.pages.values():
            p.grid_forget()
        self.pages[name].grid(row=0, column=0, sticky="nsew")
        for k, b in self.nav.items():
            if k == name:
                b.configure(fg_color=ORANGE, text_color=INK)
            else:
                b.configure(fg_color="transparent", text_color=NAV_TEXT)
        if name == "logs":
            self.refresh_logs()
        if name == "users":
            self.refresh_users()

    def page(self, title, sub):
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        ctk.CTkLabel(f, text=title, font=("Segoe UI", 28, "bold"), text_color=TEXT).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ctk.CTkLabel(f, text=sub, text_color=NAV_TEXT).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 20))
        return f

    def menu(self, parent, label, row):
        ctk.CTkLabel(parent, text=label, text_color=TEXT).grid(row=row, column=0, sticky="w", pady=10, padx=(0, 20))
        m = ctk.CTkOptionMenu(parent, values=["(none)"], width=220, fg_color=ORANGE,
                              button_color=ORANGE_HOVER, button_hover_color=ORANGE, text_color=INK,
                              dropdown_fg_color=CARD, dropdown_text_color=TEXT,
                              dropdown_hover_color=SIDEBAR)
        m.grid(row=row, column=1, sticky="w")
        self.menus.append(m)
        return m

    def file_picker(self, parent, label, row, initialdir=None):
        ctk.CTkLabel(parent, text=label, text_color=TEXT).grid(row=row, column=0, sticky="w", pady=10, padx=(0, 20))
        e = ctk.CTkEntry(parent, width=380, placeholder_text="No file selected 🐾",
                         fg_color=CARD, border_color=ORANGE, text_color=TEXT)
        e.grid(row=row, column=1, sticky="w")

        def browse():
            p = filedialog.askopenfilename(initialdir=initialdir)
            if p:
                e.delete(0, "end")
                e.insert(0, p)

        btn(parent, "Browse", browse, width=90).grid(row=row, column=2, padx=10)
        return e

    def result_card(self, parent, row):
        card = ctk.CTkLabel(parent, text="", corner_radius=14, height=60, wraplength=560,
                            font=("Segoe UI", 15, "bold"), fg_color="transparent")
        card.grid(row=row, column=0, columnspan=3, sticky="w", pady=20)
        return card

    def flash(self, card, text, color):
        card.configure(text=f"   {text}   ", fg_color=color, text_color="white")

    # ---------- pages ----------
    def build_send(self):
        f = self.page("Send Document 🐟", "Signed with your private key, sealed with the recipient's public key.")
        self.s_sender = self.menu(f, "Sender (you)", 2)
        self.s_recip = self.menu(f, "Recipient", 3)
        self.s_doc = self.file_picker(f, "Document", 4)
        btn(f, "🔏  Sign & Encrypt", self.send, height=42).grid(row=5, column=1, sticky="w", pady=20)
        self.s_card = self.result_card(f, 6)
        return f

    def build_receive(self):
        f = self.page("Receive Document 🐭", "The document only opens if decryption and signature checks succeed.")
        self.r_recip = self.menu(f, "Recipient (you)", 2)
        self.r_sender = self.menu(f, "Expected sender", 3)
        self.r_enc = self.file_picker(f, "Encrypted file", 4, ENCRYPTED)
        btn(f, "🔓  Decrypt & Verify", self.receive, height=42).grid(row=5, column=1, sticky="w", pady=20)
        self.r_card = self.result_card(f, 6)
        self.open_btn = btn(f, "🐾  Open Document", self.open_doc, state="disabled")
        self.open_btn.grid(row=7, column=1, sticky="w")
        return f

    def build_logs(self):
        f = self.page("Audit Log 🐾", "Every paw print is recorded. Failures show in red.")
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)
        self.log_box = ctk.CTkScrollableFrame(f, fg_color=CARD)
        self.log_box.grid(row=2, column=0, columnspan=3, sticky="nsew")
        btn(f, "Refresh", self.refresh_logs, width=100).grid(row=3, column=0, columnspan=3, sticky="e", pady=10)
        return f

    def build_users(self):
        f = self.page("Users & Keys 😺", "Each cat has an RSA-2048 key pair stored in the keys folder.")
        btn(f, "+ New User", self.new_user).grid(row=2, column=0, sticky="w")
        btn(f, "Open keys folder", lambda: os.startfile(KEYS), fg_color=("#c9a57e", "#5a4432"),
            hover_color=("#b8916a", "#6b5340"), text_color=TEXT).grid(row=2, column=1, sticky="w", padx=10)
        self.user_box = ctk.CTkScrollableFrame(f, height=350, fg_color=CARD)
        self.user_box.grid(row=3, column=0, columnspan=3, sticky="ew", pady=20)
        return f

    # ---------- data ----------
    def users(self):
        return sorted(f[:-12] for f in os.listdir(KEYS) if f.endswith("_private.pem"))

    def refresh_users(self):
        users = self.users()
        values = users or ["(none)"]
        for m in self.menus:
            m.configure(values=values)
            if m.get() not in values:
                m.set(values[0])
        for w in self.user_box.winfo_children():
            w.destroy()
        for u in users:
            ctk.CTkLabel(self.user_box, text=f"🐱  {u}", font=("Segoe UI", 14),
                         text_color=TEXT).pack(anchor="w", padx=10, pady=4)

    def refresh_logs(self):
        for w in self.log_box.winfo_children():
            w.destroy()
        widths = (150, 80, 130, 200, 110)

        def add(values, bold=False, color=None):
            row = ctk.CTkFrame(self.log_box, fg_color="transparent")
            row.pack(fill="x")
            for v, w in zip(values, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w", text_color=color or TEXT,
                             font=("Segoe UI", 12, "bold" if bold else "normal")).pack(side="left", padx=4)

        add(("Time", "User", "Action", "File", "Status"), bold=True)
        rows = get_logs()[:200]
        if not rows:
            ctk.CTkLabel(self.log_box, text="No paw prints yet 🐾", text_color=NAV_TEXT).pack(pady=20)
        for r in rows:
            failed = r[4] == "FAILED"
            status = ("😾 " if failed else "😺 ") + r[4]
            add((r[0], r[1], r[2], r[3], status), color="#ef5350" if failed else None)

    # ---------- actions ----------
    def new_user(self):
        name = ctk.CTkInputDialog(text="Name your cat (letters/numbers only):", title="New User").get_input()
        if not name:
            return
        if not name.isalnum():
            return messagebox.showwarning("Invalid", "Use letters and numbers only (no spaces or underscores).")
        if name in self.users():
            return messagebox.showwarning("Exists", f"Keys for '{name}' already exist.")
        generate_keys(name, KEYS)
        self.refresh_users()

    def send(self):
        doc, s, r = self.s_doc.get(), self.s_sender.get(), self.s_recip.get()
        if not doc or s not in self.users() or r not in self.users():
            return messagebox.showwarning("Missing info", "Choose sender, recipient and a document.")
        name = os.path.basename(doc)
        try:
            sign_file(doc, key(s, "private"), os.path.join(SIGNATURES, name + ".sig"))
            encrypt_file(doc, os.path.join(ENCRYPTED, name + ".enc"), key(r, "public"))
            self.flash(self.s_card, f"😺 Purr-fect! '{name}' signed and encrypted for {r}", GREEN)
        except Exception as e:
            self.flash(self.s_card, f"😿 Oops: {e}", RED)

    def receive(self):
        enc, r, s = self.r_enc.get(), self.r_recip.get(), self.r_sender.get()
        self.open_btn.configure(state="disabled")
        if not enc or s not in self.users() or r not in self.users():
            return messagebox.showwarning("Missing info", "Choose recipient, sender and an encrypted file.")
        name = os.path.basename(enc)
        if not name.endswith(".enc"):
            return messagebox.showwarning("Wrong file", "Select a .enc file.")
        orig = name[:-4]
        dec = os.path.join(DECRYPTED, orig)
        sig = os.path.join(SIGNATURES, orig + ".sig")

        if decrypt_file(enc, dec, key(r, "private")) is False:
            self.flash(self.r_card, "😾 Hiss! Decryption failed: wrong key or corrupted file", RED)
        elif not os.path.exists(sig):
            os.remove(dec)
            self.flash(self.r_card, "🙀 No signature found. Access blocked", AMBER)
        elif verify_file(dec, key(s, "public"), sig):
            self.last_opened = dec
            self.open_btn.configure(state="normal")
            self.flash(self.r_card, "😺 Purr-fect! Verified: authentic and untampered", GREEN)
        else:
            os.remove(dec)
            self.flash(self.r_card, "🙀 Smells fishy: file was tampered. Access blocked", RED)

    def open_doc(self):
        if self.last_opened and os.path.exists(self.last_opened):
            os.startfile(self.last_opened)


if __name__ == "__main__":
    App().mainloop()