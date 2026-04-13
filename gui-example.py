import tkinter as tk
from tkinter import ttk

class TkinterPlayground(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Tkinter Layout Playground")
        self.geometry("1000x700")

        # ---- TOP LEVEL LAYOUT (pack) ----
        # Header (pack is perfect here)
        self.header = ttk.Frame(self)
        self.header.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(
            self.header,
            text="Tkinter Layout Playground",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")

        ttk.Button(
            self.header,
            text="Quit",
            command=self.destroy
        ).pack(side="right")

        # Main content area
        self.content = ttk.Frame(self)
        self.content.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- CONTENT LAYOUT (grid) ----
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=2)
        self.content.grid_rowconfigure(0, weight=1)

        self.create_left_panel()
        self.create_right_panel()

        # ---- STATUS BAR (pack) ----
        self.status = ttk.Label(self, text="Ready", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(0, 5))

    # -----------------------------
    # LEFT PANEL (grid, form-style)
    # -----------------------------
    def create_left_panel(self):
        frame = ttk.LabelFrame(self.content, text="Controls (grid layout)")
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frame).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Email:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frame).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Role:").grid(row=2, column=0, sticky="ne", padx=5, pady=5)

        role_box = ttk.Combobox(frame, values=["Admin", "User", "Viewer"])
        role_box.current(0)
        role_box.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Checkbutton(frame, text="Active").grid(
            row=3, column=1, sticky="w", padx=5, pady=5
        )

        ttk.Button(frame, text="Submit").grid(
            row=4, column=0, columnspan=2, pady=(10, 5)
        )

    # -----------------------------
    # RIGHT PANEL (table + pack)
    # -----------------------------
    def create_right_panel(self):
        frame = ttk.LabelFrame(self.content, text="Data View (nested layout)")
        frame.grid(row=0, column=1, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # ---- Toolbar (pack) ----
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="Add Row").pack(side="left", padx=2)
        ttk.Button(toolbar, text="Remove Row").pack(side="left", padx=2)
 
        ttk.Entry(toolbar).pack(side="right")
        ttk.Label(toolbar, text="Search:").pack(side="right", padx=2)

        # ---- Table area (grid) ----
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Name", "Status"),
            show="headings"
        )

        for col in ("ID", "Name", "Status"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        ysb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)

        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        # Sample data
        for i in range(1, 21):
            self.tree.insert("", "end", values=(i, f"Item {i}", "OK"))


if __name__ == "__main__":
    TkinterPlayground().mainloop()