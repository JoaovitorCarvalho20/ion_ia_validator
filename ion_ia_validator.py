import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os

# ── Paleta de cores ION ──────────────────────────────────────────────────────
BG         = "#1e1e2e"
SURFACE    = "#2a2a3d"
CARD       = "#313149"
ACCENT     = "#4f8ef7"
ACCENT_DIM = "#2d5ab0"
SUCCESS    = "#3ecf6e"
WARNING    = "#f5a623"
DANGER     = "#e74c3c"
TEXT       = "#e8e8f0"
TEXT_MUTED = "#8888aa"
BORDER     = "#3d3d58"

FONT_TITLE  = ("Segoe UI", 15, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 9)
FONT_BADGE  = ("Segoe UI", 9, "bold")


class IONIAValidator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ION IA — Validador de Regras")
        self.geometry("980x680")
        self.minsize(820, 560)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.db_path = None
        self._build_ui()

    # ── Layout principal ─────────────────────────────────────────────────────
    def _build_ui(self):
        # Cabeçalho
        header = tk.Frame(self, bg=SURFACE, pady=14)
        header.pack(fill="x")

        tk.Label(header, text="ION IA", font=("Segoe UI", 18, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=20)
        tk.Label(header, text="Validador de Regras de Recomendação",
                 font=("Segoe UI", 11), bg=SURFACE, fg=TEXT_MUTED).pack(side="left")

        # Barra de ação
        action = tk.Frame(self, bg=BG, pady=14, padx=20)
        action.pack(fill="x")

        self.btn_upload = tk.Button(
            action, text="⬆  Carregar base (.db / .s3db)",
            font=FONT_HEADER, bg=ACCENT, fg="white",
            activebackground=ACCENT_DIM, activeforeground="white",
            relief="flat", padx=16, pady=8, cursor="hand2",
            command=self._load_db
        )
        self.btn_upload.pack(side="left")

        self.lbl_file = tk.Label(action, text="Nenhuma base carregada",
                                 font=FONT_BODY, bg=BG, fg=TEXT_MUTED)
        self.lbl_file.pack(side="left", padx=16)

        # Cards de métricas
        self.metrics_frame = tk.Frame(self, bg=BG, padx=20, pady=0)
        self.metrics_frame.pack(fill="x")

        self.card_total   = self._metric_card(self.metrics_frame, "Total de regras", "—", ACCENT)
        self.card_ic      = self._metric_card(self.metrics_frame, "Com inteligência comercial", "—", SUCCESS)
        self.card_sem_ic  = self._metric_card(self.metrics_frame, "Sem inteligência comercial", "—", WARNING)
        self.card_status  = self._metric_card(self.metrics_frame, "Status das tabelas", "—", TEXT_MUTED)

        for c in (self.card_total, self.card_ic, self.card_sem_ic, self.card_status):
            c.pack(side="left", padx=(0, 12), pady=(0, 14))

        # Separador
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=20)

        # Filtro de busca
        filter_row = tk.Frame(self, bg=BG, padx=20, pady=10)
        filter_row.pack(fill="x")

        tk.Label(filter_row, text="Filtrar:", font=FONT_BODY,
                 bg=BG, fg=TEXT_MUTED).pack(side="left")

        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._apply_filter)
        entry = tk.Entry(filter_row, textvariable=self.filter_var,
                         font=FONT_BODY, bg=CARD, fg=TEXT,
                         insertbackground=TEXT, relief="flat",
                         highlightthickness=1, highlightcolor=ACCENT,
                         highlightbackground=BORDER, width=34)
        entry.pack(side="left", padx=(8, 0), ipady=5)

        # Filtro IC
        self.ic_filter = tk.StringVar(value="Todos")
        for label in ("Todos", "Com IC", "Sem IC"):
            rb = tk.Radiobutton(
                filter_row, text=label, variable=self.ic_filter, value=label,
                font=FONT_BODY, bg=BG, fg=TEXT, selectcolor=CARD,
                activebackground=BG, activeforeground=ACCENT,
                command=self._apply_filter
            )
            rb.pack(side="left", padx=(16, 0))

        # Tabela
        table_frame = tk.Frame(self, bg=BG, padx=20, pady=0)
        table_frame.pack(fill="both", expand=True, pady=(0, 16))
        self.table_frame = table_frame

        cols = ("rule_id", "antecedentes", "consequente", "qtd_ant", "ic")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                 selectmode="browse")

        col_cfg = [
            ("rule_id",     "Rule ID",                     220, "w"),
            ("antecedentes","Antecedentes",                 280, "w"),
            ("consequente", "Consequente",                  180, "w"),
            ("qtd_ant",     "Qtd. antecedentes",             90, "center"),
            ("ic",          "Inteligência comercial",        90, "center"),
        ]
        for cid, head, width, anchor in col_cfg:
            self.tree.heading(cid, text=head,
                              command=lambda c=cid: self._sort_col(c))
            self.tree.column(cid, width=width, minwidth=60, anchor=anchor)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD, foreground=TEXT,
                        fieldbackground=CARD, font=FONT_MONO,
                        rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading",
                        background=SURFACE, foreground=TEXT,
                        font=FONT_BODY, relief="flat")
        style.map("Treeview", background=[("selected", ACCENT_DIM)])

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("ic_sim", foreground=SUCCESS)
        self.tree.tag_configure("ic_nao", foreground=TEXT_MUTED)

        # Linhas divisórias entre colunas
        self._col_separators = []
        self._sep_after_cols = ("antecedentes", "consequente", "qtd_ant")
        self.tree.bind("<Configure>", lambda _e: self._draw_column_separators())

        # Rodapé
        footer = tk.Frame(self, bg=SURFACE, pady=8)
        footer.pack(fill="x", side="bottom")
        self.lbl_rows = tk.Label(footer, text="", font=FONT_BODY,
                                 bg=SURFACE, fg=TEXT_MUTED)
        self.lbl_rows.pack(side="right", padx=20)

        self._rows_cache = []

    # ── Card de métrica ──────────────────────────────────────────────────────
    def _metric_card(self, parent, label, value, color):
        frame = tk.Frame(parent, bg=CARD, padx=18, pady=12,
                         highlightthickness=1, highlightbackground=BORDER)
        tk.Label(frame, text=label, font=FONT_BODY,
                 bg=CARD, fg=TEXT_MUTED).pack(anchor="w")
        lbl = tk.Label(frame, text=value, font=("Segoe UI", 20, "bold"),
                       bg=CARD, fg=color)
        lbl.pack(anchor="w", pady=(2, 0))
        frame._value_lbl = lbl
        frame._color = color
        return frame

    def _update_card(self, card, value, color=None):
        card._value_lbl.config(text=str(value),
                               fg=color if color else card._color)

    # ── Linhas divisórias entre colunas da tabela ───────────────────────────
    def _draw_column_separators(self):
        for line in self._col_separators:
            line.destroy()
        self._col_separators = []

        x = 0
        for cid in self.tree["columns"]:
            x += self.tree.column(cid, "width")
            if cid in self._sep_after_cols:
                sep = tk.Frame(self.table_frame, bg=BORDER, width=1)
                sep.place(in_=self.tree, x=x, y=0, relheight=1)
                self._col_separators.append(sep)

    # ── Carregar base ────────────────────────────────────────────────────────
    def _load_db(self):
        path = filedialog.askopenfilename(
            title="Selecionar base do cliente",
            filetypes=[("SQLite", "*.db *.s3db *.sqlite *.sqlite3"),
                       ("Todos", "*.*")]
        )
        if not path:
            return
        self.db_path = path
        self.lbl_file.config(text=os.path.basename(path), fg=TEXT)
        self._run_query()

    # ── Consulta principal ───────────────────────────────────────────────────
    def _run_query(self):
        if not self.db_path:
            return

        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()

            # Verificar existência das tabelas
            cur.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name IN ('ionv_rules_antecedents','ionv_rules_consequents')
            """)
            found = {r[0] for r in cur.fetchall()}

            tem_ant = "ionv_rules_antecedents" in found
            tem_con = "ionv_rules_consequents" in found

            if not tem_ant or not tem_con:
                missing = []
                if not tem_ant: missing.append("ionv_rules_antecedents")
                if not tem_con: missing.append("ionv_rules_consequents")
                self._update_card(self.card_status,
                                  "❌ Ausente", DANGER)
                self._update_card(self.card_total, "—", ACCENT)
                self._update_card(self.card_ic,    "—", SUCCESS)
                self._update_card(self.card_sem_ic,"—", WARNING)
                messagebox.showwarning(
                    "Tabelas não encontradas",
                    f"As seguintes tabelas estão ausentes na base:\n\n"
                    + "\n".join(f"  • {m}" for m in missing)
                    + "\n\nO módulo de IA pode não ter sido executado ainda."
                )
                con.close()
                return

            self._update_card(self.card_status, "✔ OK", SUCCESS)

            # Regras com antecedentes agrupados
            cur.execute("""
                SELECT
                    ira.rule_id,
                    GROUP_CONCAT(ira.antecedent, ' | ') AS antecedentes,
                    irc.consequent,
                    COUNT(ira.antecedent)               AS qtd_ant,
                    irc.inteligencia_comercial           AS ic,
                    (SELECT COUNT(DISTINCT rule_id)
                     FROM ionv_rules_consequents)        AS total_regras
                FROM ionv_rules_antecedents ira
                JOIN ionv_rules_consequents irc
                    ON ira.rule_id = irc.rule_id
                GROUP BY ira.rule_id, irc.consequent
                ORDER BY ira.rule_id
            """)
            rows = cur.fetchall()
            con.close()

            if not rows:
                messagebox.showinfo("Sem dados",
                    "As tabelas existem, mas não há regras geradas ainda.")
                return

            total_regras = rows[0][5] if rows else 0
            com_ic  = sum(1 for r in rows if r[4] and int(r[4]) != 0)
            sem_ic  = total_regras - com_ic

            self._update_card(self.card_total,  total_regras, ACCENT)
            self._update_card(self.card_ic,     com_ic,       SUCCESS)
            self._update_card(self.card_sem_ic, sem_ic,       WARNING)

            self._rows_cache = rows
            self.filter_var.set("")
            self.ic_filter.set("Todos")
            self._populate_table(rows)

        except Exception as e:
            messagebox.showerror("Erro ao consultar base",
                                 f"{type(e).__name__}: {e}")

    # ── Preencher tabela ─────────────────────────────────────────────────────
    def _populate_table(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            rule_id, ants, consequente, qtd_ant, ic, *_ = r
            ic_val  = int(ic) if ic is not None else 0
            ic_txt  = "Sim" if ic_val != 0 else "Não"
            tag     = "ic_sim" if ic_val != 0 else "ic_nao"
            self.tree.insert("", "end",
                             values=(rule_id, ants, consequente, qtd_ant, ic_txt),
                             tags=(tag,))

        total = len(rows)
        self.lbl_rows.config(text=f"{total} regra(s) exibida(s)")

    # ── Filtro de texto + IC ─────────────────────────────────────────────────
    def _apply_filter(self, *_):
        term  = self.filter_var.get().lower()
        ic_f  = self.ic_filter.get()

        filtered = []
        for r in self._rows_cache:
            rule_id, ants, consequente, qtd_ant, ic, *_ = r
            ic_val = int(ic) if ic is not None else 0

            if ic_f == "Com IC" and ic_val == 0:
                continue
            if ic_f == "Sem IC" and ic_val != 0:
                continue

            if term and term not in str(r).lower():
                continue

            filtered.append(r)

        self._populate_table(filtered)

    # ── Ordenação por coluna ─────────────────────────────────────────────────
    def _sort_col(self, col):
        col_map = {"rule_id": 0, "antecedentes": 1,
                   "consequente": 2, "qtd_ant": 3, "ic": 4}
        idx = col_map.get(col, 0)
        rev = getattr(self, "_sort_rev", {})
        asc = not rev.get(col, False)
        rev[col] = asc
        self._sort_rev = rev

        sorted_rows = sorted(
            self._rows_cache,
            key=lambda r: (r[idx] if r[idx] is not None else ""),
            reverse=asc
        )
        self._rows_cache = sorted_rows
        self._apply_filter()


if __name__ == "__main__":
    app = IONIAValidator()
    app.mainloop()
