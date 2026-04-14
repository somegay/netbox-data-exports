import tkinter as tk
from tkinter import ttk

# Temps
SAMPLE_COLUMNS = ["col1", "col2", "col3", "col4", "col5"]

class GuiController(tk.Tk):
    def __init__(self, 
                 state_manager,
                 config):
        super().__init__()
        self.state_manager = state_manager
        self.config = config

        self.title(self.config.title)
        self.geometry(self.config.geometry)

        # SETUP LAYOUT AND WIDGETS
        self.header = Header(self, self.config)
        self.content = MainContent(self)
        self.sidebar = Sidebar(self.content, "Snapshots", self.state_manager)
        self.main_area = MainArea(self.content, "Records", SAMPLE_COLUMNS, self.state_manager)
        self.status_bar = ttk.Label(self, text="Status Bar", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

# WIDGETS
# -----------------------------

class Header(tk.Frame):
    def __init__(self, parent, config):
        self.config = config
        super().__init__(parent)
        self.pack(fill="x", padx=10, pady=(10, 5))
        self.title = ttk.Label(
            self,
            text="Snapshot Viewer",
            font=(self.config.font_family, self.config.header_font_size, self.config.header_font_style)
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
    def __init__(self, parent, text, state_manager):
        super().__init__(parent, text=text)
        self.state_manager = state_manager
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
        ttk.Button(header_actions, text="Refresh", command=self.handle_refresh).pack(ipadx=2, side="left", padx= (0, 5))
        ttk.Button(header_actions, text="Search", command=self.handle_search).pack(ipadx=5, fill="x", expand=True)  
        self.snapshot_list = tk.Listbox(self, relief="solid")
        self.snapshot_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.snapshot_list.bind("<<ListboxSelect>>", self.handle_select)
        """
        THIS IS A Sample DATA ONLY
        """
        self.snapshot_list.insert(tk.END, "Snapshot 1")
        self.snapshot_list.insert(tk.END, "Snapshot 2")
        self.snapshot_list.insert(tk.END, "Snapshot 3")
    
    def handle_refresh(self):
        print("Refresh Clicked!")
        self.state_manager.list_refresh()

    def handle_search(self):
        print("List Search Clicked!")
        self.state_manager.filter_list()

    def handle_select(self, event):
        print("=Snapshot Selected!")
        self.state_manager.get_snapshot_list()

class MainArea(ttk.LabelFrame):
    def __init__(self, parent, text, columns, state_manager):
        self.state_manager = state_manager
        super().__init__(parent, text=text)
        self.grid(row=0, column=1, sticky="nsew")
        self.header = tk.Frame(self)
        self.header.pack(fill="x", padx=10)
        ttk.Label(self.header, text="Search: ").pack(side="left", padx=(0, 5))
        ttk.Entry(self.header).pack(side="left", ipadx=50)
        ttk.Button(self.header, text="Search", command=self.handle_data_search).pack(side="left", padx=(10, 0))
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
    
    def handle_data_search(self):
        self.state_manager.filter_data()