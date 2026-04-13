import tkinter as tk
from tkinter import ttk

# Window
TITLE = "Snapshot Viewer"
WINDOW_GEOMETRY = "1280x720"
# Type
FONT_FAMILY = "Segoe UI"
FONT_SIZE_HEADER = 14
FONT_STYLE_HEADER = "bold"
# Temps
SAMPLE_COLUMNS = ["col1", "col2", "col3", "col4", "col5"]

class GuiController(tk.Tk):
    def __init__(self, 
                 handle_list_refresh, 
                 handle_list_search, 
                 handle_data_search,
                 handle_snapshot_select):
        super().__init__()

        self.title(TITLE)
        self.geometry(WINDOW_GEOMETRY)

        # SETUP LAYOUT AND WIDGETS
        self.header = Header(self)
        self.content = MainContent(self)
        self.sidebar = Sidebar(self.content, "Snapshots", 
                               handle_list_refresh, 
                               handle_list_search, 
                               handle_snapshot_select)
        self.main_area = MainArea(self.content, "Records", SAMPLE_COLUMNS, handle_data_search)
        self.status_bar = ttk.Label(self, text="Status Bar", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))
    
    def fetch_snapshot_list_query(self):
        pass

    def fetch_snapshot_data_query(self):
        pass

    def fetch_selected_snapshot(self):
        pass

    def update_status(self):
        pass

    def update_snapshot_list(self):
        pass

    def update_snapshot_data(self):
        pass

# WIDGETS
# -----------------------------

class Header(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="x", padx=10, pady=(10, 5))
        self.title = ttk.Label(
            self,
            text="Snapshot Viewer",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, FONT_STYLE_HEADER)
        )
        self.title.pack(side="left")

class MainContent(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)
        self.grid_rowconfigure(0, weight=1)

class Sidebar(ttk.LabelFrame):
    def __init__(self, parent, text, refresh_method, search_method, snapshot_select_method):
        super().__init__(parent, text=text)
        self.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # Header
        self.header = tk.Frame(self)
        self.header.pack(fill="x", padx=10)
        header_text = ttk.Frame(self.header)
        header_text.pack(fill="x")
        ttk.Label(header_text, text="Search: ").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(header_text)
        self.search_entry.pack(fill="x", expand=True)
        header_actions = ttk.Frame(self.header)
        header_actions.pack(fill="x")
        self.combobox = ttk.Combobox(
            header_actions, 
            values=["IP Address", "Devices"], 
            state="readonly"
        )
        self.combobox.pack(side="top", pady=10, fill="x", expand=True)
        self.combobox.current(0)
        ttk.Button(header_actions, text="Refresh", command=refresh_method).pack(ipadx=2, side="left", padx= (0, 5))
        ttk.Button(header_actions, text="Search", command=search_method).pack(ipadx=5, fill="x", expand=True)  
        self.snapshot_list = tk.Listbox(self, relief="solid")
        self.snapshot_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.snapshot_list.bind("<<ListboxSelect>>", snapshot_select_method)
        """
        THIS IS A Sample DATA ONLY
        """
        self.snapshot_list.insert(tk.END, "Snapshot 1")
        self.snapshot_list.insert(tk.END, "Snapshot 2")
        self.snapshot_list.insert(tk.END, "Snapshot 3")

class MainArea(ttk.LabelFrame):
    def __init__(self, parent, text, columns, search_method):
        super().__init__(parent, text=text)
        self.grid(row=0, column=1, sticky="nsew")
        self.header = tk.Frame(self)
        self.header.pack(fill="x", padx=10)
        ttk.Label(self.header, text="Search: ").pack(side="left", padx=(0, 5))
        ttk.Entry(self.header).pack(side="left", ipadx=50)
        ttk.Button(self.header, text="Search", command=search_method).pack(side="left", padx=(10, 0))
        # table
        table = tk.Frame(self)
        table.pack(fill="both", expand=True, padx=10, pady=10)
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=columns, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")
        ysb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        """
        THIS IS SAMPLE DATA ONLY
        """
        for i in range(1, 21):
            self.tree.insert("", "end", values=(i, f"Item {i}", "OK"))