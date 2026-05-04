import customtkinter as ctk
import pandas as pd
import re
import threading
import sys
from pathlib import Path
from tkinter import filedialog, messagebox
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

CHAR_IMG = BASE_DIR / "assets" / "character.png"

BG        = "#1a1a1a"
SURFACE   = "#242424"
SURFACE2  = "#2e2e2e"
BORDER    = "#3a3a3a"
BORDER2   = "#484848"
ACCENT    = "#4a9eff"
ACCENT_H  = "#5aaeff"
TEXT      = "#f0f0f0"
TEXT_2    = "#aaaaaa"
TEXT_3    = "#666666"
GREEN     = "#4ec94e"
GREEN_BG  = "#1a2e1a"
RED       = "#f05050"
RED_BG    = "#2e1a1a"
BLUE_BG   = "#1a2233"
DARK_CARD = "#000000"


def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip().lower()


def parse_input(text):
    lines = text.strip().split("\n")
    parsed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        name = re.split(r'@', line)[0]
        name = re.sub(r'[-–—]\s*$', '', name).strip()
        if name:
            parsed.append({"original": name, "clean": clean_text(name)})
    return parsed


class GameSeedApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GAMESEED 2026 — Participant Checker")
        self.geometry("960x640")
        self.minsize(820, 540)
        self.configure(fg_color=BG)

        icon_path = BASE_DIR / "assets" / "icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        self.mobile_path  = ctk.StringVar(value="No file selected")
        self.pc_path      = ctk.StringVar(value="No file selected")
        self._mobile_full = None
        self._pc_full     = None
        self.df_all       = None
        self._result_text = ""

        self._build()

    def _build(self):
        titlebar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=48)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        ctk.CTkLabel(
            titlebar,
            text="GAMESEED 2026",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=ACCENT
        ).pack(side="left", padx=(20, 6), pady=13)

        ctk.CTkLabel(
            titlebar,
            text="Participant Checker",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_2
        ).pack(side="left", pady=13)

        self.status_lbl = ctk.CTkLabel(
            titlebar,
            text="○  No CSV loaded",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_3
        )
        self.status_lbl.pack(side="right", padx=20)

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=14)
        body.columnconfigure(0, weight=3, minsize=260)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = ctk.CTkScrollableFrame(
            parent, fg_color=SURFACE, corner_radius=10,
            border_color=BORDER, border_width=1,
            scrollbar_button_color=BORDER2,
            scrollbar_button_hover_color=BORDER2
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._section(left, "Data Source")
        self._csv_card(left, "Mobile", "mobile", self.mobile_path, self._load_mobile)
        self._csv_card(left, "PC",     "pc",     self.pc_path,     self._load_pc)

        ctk.CTkFrame(left, fg_color=BORDER, height=1).pack(fill="x", pady=(12, 0), padx=2)

        self._section(left, "Paste Names")

        ctk.CTkLabel(
            left,
            text="Format: Nama Lengkap @discord",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=TEXT_3, anchor="w"
        ).pack(fill="x", padx=4, pady=(0, 6))

        self.input_box = ctk.CTkTextbox(
            left, height=195, fg_color=SURFACE2,
            border_color=BORDER, border_width=1, corner_radius=8,
            font=ctk.CTkFont("Consolas", 12), text_color=TEXT, wrap="word"
        )
        self.input_box.pack(fill="x", padx=4, pady=(0, 10))
        self.input_box.insert("0.0", "Waguri @Wagureng\nRentarou @BossTokoKue ,\n")

        self.check_btn = ctk.CTkButton(
            left,
            text="Check Participants",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_H,
            corner_radius=8, height=40,
            command=self._run_check
        )
        self.check_btn.pack(fill="x", padx=4, pady=(0, 6))

        ctk.CTkButton(
            left, text="Clear",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=SURFACE2, hover_color=BORDER,
            text_color=TEXT_2, border_color=BORDER, border_width=1,
            corner_radius=8, height=34,
            command=self._clear
        ).pack(fill="x", padx=4, pady=(0, 14))

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=0)

        top_row = ctk.CTkFrame(right, fg_color="transparent")
        top_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top_row.columnconfigure(0, weight=1)

        stats = ctk.CTkFrame(top_row, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew")
        for i in range(5):
            stats.columnconfigure(i, weight=1)

        self.stat_total    = self._stat(stats, 0, "Total",      ACCENT, BLUE_BG)
        self.stat_found    = self._stat(stats, 1, "Registered", GREEN,  GREEN_BG)
        self.stat_notfound = self._stat(stats, 2, "Not Found",  RED,    RED_BG)
        self.stat_mobile   = self._stat(stats, 3, "Mobile",     ACCENT, SURFACE)
        self.stat_pc       = self._stat(stats, 4, "PC",         ACCENT, SURFACE)

        mid_row = ctk.CTkFrame(right, fg_color="transparent")
        mid_row.grid(row=1, column=0, columnspan=2, sticky="nsew")
        mid_row.rowconfigure(0, weight=1)
        mid_row.columnconfigure(0, weight=1)
        mid_row.columnconfigure(1, weight=0)

        panel = ctk.CTkFrame(mid_row, fg_color=SURFACE, corner_radius=10,
                              border_color=BORDER, border_width=1)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.rowconfigure(2, weight=1)
        panel.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(panel, fg_color="transparent", height=44)
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Results",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TEXT, anchor="w"
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="Copy", width=64,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=SURFACE2, hover_color=BORDER,
            text_color=TEXT_2, border_color=BORDER, border_width=1,
            corner_radius=6, height=28,
            command=self._copy_results
        ).pack(side="right")

        ctk.CTkFrame(panel, fg_color=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", pady=(8, 0)
        )

        self.result_box = ctk.CTkTextbox(
            panel, fg_color=SURFACE, border_width=0, corner_radius=0,
            font=ctk.CTkFont("Consolas", 12), text_color=TEXT_3,
            wrap="word", state="disabled"
        )
        self.result_box.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        self.result_box.configure(state="normal")
        self.result_box.insert("0.0", "Results will appear here after checking...")
        self.result_box.configure(state="disabled")

        import tkinter as tk

        char_card = tk.Frame(mid_row, bg="#000000", width=130)
        char_card.grid(row=0, column=1, sticky="ns")
        char_card.pack_propagate(False)
        char_card.grid_propagate(False)

        if CHAR_IMG.exists():
            try:
                from PIL import ImageTk
                raw = Image.open(CHAR_IMG).resize((118, 210), Image.LANCZOS)
                char_img = ImageTk.PhotoImage(raw)
                lbl = tk.Label(char_card, image=char_img, bg="#000000", bd=0)
                lbl.image = char_img
                lbl.pack(expand=True)
            except Exception as e:
                tk.Label(
                    char_card, text=f"Error:\n{e}",
                    bg="#000000", fg="#555555",
                    wraplength=120, justify="center"
                ).pack(expand=True)
        else:
            tk.Label(
                char_card,
                text="assets/\ncharacter\n.png",
                bg="#000000", fg="#555555",
                justify="center"
            ).pack(expand=True)

    def _section(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=TEXT, anchor="w"
        ).pack(fill="x", padx=4, pady=(14, 8))

    def _csv_card(self, parent, label, kind, var, cmd):
        card = ctk.CTkFrame(parent, fg_color=SURFACE2, corner_radius=8,
                             border_color=BORDER, border_width=1)
        card.pack(fill="x", padx=4, pady=(0, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(10, 4))

        icon = "📱" if kind == "mobile" else "🖥"
        ctk.CTkLabel(
            row, text=f"{icon}  {label}",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=TEXT, anchor="w"
        ).pack(side="left")

        ctk.CTkButton(
            row, text="Browse", width=72,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=ACCENT, hover_color=ACCENT_H,
            corner_radius=6, height=28, command=cmd
        ).pack(side="right")

        ctk.CTkLabel(
            card, textvariable=var,
            font=ctk.CTkFont("Consolas", 10),
            text_color=TEXT_3, anchor="w", wraplength=200
        ).pack(fill="x", padx=12, pady=(0, 8))

    def _stat(self, parent, col, label, color, bg):
        pad = (0, 8) if col < 4 else (0, 0)
        card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8,
                             border_color=BORDER, border_width=1)
        card.grid(row=0, column=col, sticky="ew", padx=pad)

        val = ctk.CTkLabel(card, text="—",
                            font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=color)
        val.pack(pady=(10, 2))
        ctk.CTkLabel(card, text=label,
                     font=ctk.CTkFont("Segoe UI", 10), text_color=TEXT_2).pack(pady=(0, 10))
        return val

    def _load_mobile(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self._mobile_full = path
            self.mobile_path.set(path.replace("\\", "/").split("/")[-1])
            self._try_merge()

    def _load_pc(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self._pc_full = path
            self.pc_path.set(path.replace("\\", "/").split("/")[-1])
            self._try_merge()

    def _try_merge(self):
        mp, pp = self._mobile_full, self._pc_full
        if mp and pp:
            try:
                df1 = pd.read_csv(mp)
                df2 = pd.read_csv(pp)
                df1.columns = df1.columns.str.strip()
                df2.columns = df2.columns.str.strip()
                df1 = df1[['Nama Lengkap']].copy()
                df2 = df2[['Nama Lengkap']].copy()
                for df, src in [(df1, 'Mobile'), (df2, 'PC')]:
                    df['Nama Asli']  = df['Nama Lengkap']
                    df['Nama Clean'] = df['Nama Lengkap'].apply(clean_text)
                    df['source']     = src
                self.df_all = pd.concat([df1, df2], ignore_index=True)
                self.status_lbl.configure(
                    text=f"●  {len(self.df_all)} participants loaded",
                    text_color=GREEN
                )
            except Exception as e:
                messagebox.showerror("Error", str(e))
        elif mp:
            self.status_lbl.configure(text="◑  Mobile loaded — add PC", text_color=ACCENT)
        elif pp:
            self.status_lbl.configure(text="◑  PC loaded — add Mobile", text_color=ACCENT)

    def _run_check(self):
        if self.df_all is None:
            messagebox.showwarning("No Data", "Load kedua file CSV dulu ya kak.")
            return
        raw = self.input_box.get("0.0", "end")
        data = parse_input(raw)
        if not data:
            messagebox.showwarning("Empty", "Paste nama peserta dulu ya kak.")
            return
        self.check_btn.configure(state="disabled", text="Checking...")
        threading.Thread(target=self._do_check, args=(data,), daemon=True).start()

    def _do_check(self, data):
        reg, noreg = [], []
        for item in data:
            match = self.df_all[self.df_all['Nama Clean'] == item["clean"]]
            if not match.empty:
                reg.append({
                    "input":   item["original"],
                    "db_name": match.iloc[0]['Nama Asli'],
                    "source":  ", ".join(match['source'].unique())
                })
            else:
                noreg.append(item["original"])
        self.after(0, self._show_results, reg, noreg, len(data))

    def _show_results(self, reg, noreg, total):
        n_mob = sum(1 for r in reg if "Mobile" in r["source"])
        n_pc  = sum(1 for r in reg if "PC"     in r["source"])

        self.stat_total.configure(text=str(total))
        self.stat_found.configure(text=str(len(reg)))
        self.stat_notfound.configure(text=str(len(noreg)))
        self.stat_mobile.configure(text=str(n_mob))
        self.stat_pc.configure(text=str(n_pc))

        lines = []
        if reg:
            lines += [f"✅  Registered  ({len(reg)})", "─" * 48]
            for r in reg:
                lines.append(f"  [{r['source']:<12}]  {r['input']}")
            lines += ["", "✅ Verified", "Mohon ditunggu team ID nya ya kak 🙌"]

        if noreg:
            if lines: lines.append("")
            lines += [f"❌  Not Registered  ({len(noreg)})", "─" * 48, "Atas nama:"]
            for n in noreg:
                lines.append(f"  • {n}")
            lines += [
                "",
                "Bisa melakukan pendaftaran melalui form ya kak",
                "untuk melanjutkan tahap verifikasi."
            ]

        self._result_text = "\n".join(lines)
        self.result_box.configure(state="normal", text_color=TEXT)
        self.result_box.delete("0.0", "end")
        self.result_box.insert("0.0", self._result_text)
        self.result_box.configure(state="disabled")
        self.check_btn.configure(state="normal", text="Check Participants")

    def _copy_results(self):
        if self._result_text:
            self.clipboard_clear()
            self.clipboard_append(self._result_text)

    def _clear(self):
        self.result_box.configure(state="normal", text_color=TEXT_3)
        self.result_box.delete("0.0", "end")
        self.result_box.insert("0.0", "Results will appear here after checking...")
        self.result_box.configure(state="disabled")
        for lbl in [self.stat_total, self.stat_found,
                    self.stat_notfound, self.stat_mobile, self.stat_pc]:
            lbl.configure(text="—")
        self._result_text = ""


if __name__ == "__main__":
    app = GameSeedApp()
    app.mainloop()