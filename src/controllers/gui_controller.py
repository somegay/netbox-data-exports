import tkinter as tk
from tkinter import ttk

COMBOBOX_VALS = ["IP Address", "Devices"]
IP_IDENTIFIER = "ip_addresses_export_"
DEVICE_IDENTIFIER = "devices_export_"
FILE_FORMAT = ".csv"

IP_COLUMNS = [
    "address",
    "dns_name",
    "status",
    "assigned_object_type",
    "assigned_object_name",
    "vrf",
]

DEVICE_COLUMNS = [
    "name",
    "device_role",
    "status",
    "site",
    "primary_ip4",
]

COLUMN_MAP = {
    "IP Address": IP_COLUMNS,
    "Devices": DEVICE_COLUMNS,
}
# Temps
SAMPLE_COLUMNS = ["col1", "col2", "col3", "col4", "col5"]

class GuiController(tk.Tk):
    def __init__(self, 
                 state_manager,
                 config):
        super().__init__()

        # Initialize configuration
        self.state_manager = state_manager
        self.config = config
        self.title(self.config.title)
        self.geometry(self.config.geometry)

        # SETUP LAYOUT AND WIDGETS
        self.header = Header(self, self.config)
        self.content = MainContent(self)
        self.sidebar = Sidebar(self, self.content, "Snapshots", self.state_manager)
        self.main_area = MainArea(self.content, "Records", SAMPLE_COLUMNS, self.state_manager)
        self.status_bar = ttk.Label(self, text="Status Bar", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

        # Initialize view
        self.sidebar.on_refresh()
    
    def set_status(self, status):
        self.status_bar.config(text=status)

# WIDGETS
# -----------------------------

class Header(tk.Frame):
    def __init__(self, parent, config):
        # Initialize
        super().__init__(parent)
        self.config = config
        self.pack(fill="x", padx=10, pady=(10, 5))
        # Widgets
        self.title = ttk.Label(
            self,
            text="Snapshot Viewer",
            font=(self.config.font_family, self.config.header_font_size, self.config.header_font_style)
        )
        self.title.pack(side="left")

class MainContent(tk.Frame):
    def __init__(self, parent):
        # Initialize
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)
        self.grid_rowconfigure(0, weight=1)

class Sidebar(ttk.LabelFrame):
    def __init__(self, controller, parent, text, state_manager):
        # Initialize
        super().__init__(parent, text=text)
        self.state_manager = state_manager
        self.gui_controller = controller
        self.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # Header
        self.header = tk.Frame(self)
        self.header.pack(fill="x", padx=10)
        header_text = ttk.Frame(self.header)
        header_text.pack(fill="x")
        ttk.Label(header_text, text="Search: ").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(header_text)
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        header_actions = ttk.Frame(self.header)
        header_actions.pack(fill="x")
        ttk.Button(header_actions, text="Clear", command=self.on_clear).pack(expand=True, fill="x", pady=(10, 0))
        self.combobox = ttk.Combobox(
            header_actions, 
            values=COMBOBOX_VALS, 
            state="readonly",
        )
        self.combobox.bind("<<ComboboxSelected>>", self.on_mode_change)
        self.combobox.pack(side="top", pady=10, ipadx=10, fill="x", expand=True)
        self.combobox.current(0)
        ttk.Button(header_actions, text="Refresh", command=self.on_refresh).pack(expand=True, fill="x")  
        self.snapshot_list = tk.Listbox(self, relief="solid")
        self.snapshot_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.snapshot_list.bind("<<ListboxSelect>>", self.on_snapshot_select)

    def on_search_change(self, event):
        self.run_search()

    def on_clear(self):
        self.search_entry.delete(0, tk.END)

    def on_mode_change(self, event):
        self.run_search()
    
    def on_refresh(self):
        print("Refresh Clicked!")
        self.gui_controller.set_status("Refreshing list...")
        self.state_manager.refresh_snapshot_list()
        self.run_search()

    def on_snapshot_select(self, event):
        selection = self.snapshot_list.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.snapshot_list.get(index)
        mode = self.combobox.get()
        if mode == COMBOBOX_VALS[0]:
            filename = IP_IDENTIFIER + name + FILE_FORMAT
        elif mode == COMBOBOX_VALS[1]:
            filename = DEVICE_IDENTIFIER + name + FILE_FORMAT
        else:
            return
        self.gui_controller.set_status("Loading snapshot...")
        dataset = self.state_manager.load_dataset(filename, mode)
        self.gui_controller.main_area.update_table(dataset)
        self.gui_controller.set_status(
            f"Loaded {len(dataset['dataset'])} records"
        )

    # Utilities

    def run_search(self):
        query = self.search_entry.get()
        mode = self.combobox.get()

        filtered = self.state_manager.filter_list(query, mode)
        self.insert_snapshots(filtered)

        self.gui_controller.set_status(
            f"{len(filtered)} snapshots shown"
        )
    
    def insert_snapshots(self, snapshots):
        self.snapshot_list.delete(0, tk.END)
        for snapshot in snapshots:
            self.snapshot_list.insert(tk.END, snapshot)

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
    
    def update_table(self, dataset):
        df = dataset["dataset"]
        data_type = dataset["type"]

        columns = COLUMN_MAP.get(data_type)
        if not columns:
            raise ValueError(f"Unknown dataset type: {data_type}")

        self.tree.delete(*self.tree.get_children())

        # Configure columns
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, anchor="w", width=160)

        # Insert rows
        for _, row in df.iterrows():
            values = [row.get(col, "") for col in columns]
            self.tree.insert("", "end", values=values)