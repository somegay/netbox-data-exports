import tkinter as tk
from tkinter import ttk
from .constants import TAB_NAMES, COLUMN_MAP


# Controller
# ---------------------------

class GuiController(tk.Tk):
    """
    Owns the application window and acts as the controller of the widgets.
    Widgets propagate (call controller methods) and the controller calls back
    down to update other widgets.
    """

    def __init__(self, state_manager, config):
        super().__init__()
        self.state_manager = state_manager
        self.config = config

        self.title(self.config.title)
        self.geometry(self.config.geometry)

        # Layout
        self.header = Header(self, self.config)
        self.content = MainContent(self)
        self.sidebar = Sidebar(self.content, self.state_manager, on_snapshot_select=self.load_snapshot, on_refresh=self.refresh_snapshots)
        self.main_area = MainArea(self.content, self.state_manager, on_tab_change=self.on_tab_change)
        self.status_bar = ttk.Label(self, text="Ready", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

        self.refresh_snapshots()

    # Mediator methods
    # ---------------------------

    def set_status(self, status: str) -> None:
        self.status_bar.config(text=status)

    def refresh_snapshots(self) -> None:
        """Refresh the snapshot list and update the sidebar."""
        self.set_status("Refreshing list...")
        self.state_manager.refresh_snapshot_list()
        query = self.sidebar.get_search_query()
        filtered = self.state_manager.filter_list(query)
        self.sidebar.populate_list(filtered)
        self.set_status(f"{len(filtered)} snapshots shown")

    def load_snapshot(self, snapshot_name: str) -> None:
        """Load a snapshot for the currently active tab and refresh the table."""
        mode = self.main_area.get_active_mode()
        self.set_status("Loading snapshot...")
        try:
            dataset = self.state_manager.load_dataset(snapshot_name, mode)
        except FileNotFoundError:
            self.set_status(f"No {mode} export found for '{snapshot_name}'")
            return
        self.main_area.update_table(dataset)
        self.set_status(f"Loaded {len(dataset['dataset'])} records")

    def on_tab_change(self) -> None:
        """Re-load data when the user switches tabs, if a snapshot is selected."""
        snapshot = self.sidebar.get_selected_snapshot()
        if snapshot:
            self.load_snapshot(snapshot)


# Widgets
# ---------------------------

class Header(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Label(
            self,
            text="Snapshot Viewer",
            font=(config.font_family, config.header_font_size, config.header_font_style),
        ).pack(side="left")

class MainContent(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)
        self.grid_rowconfigure(0, weight=1)

class Sidebar(ttk.LabelFrame):
    """
    Displays the snapshot list and search/filter controls.
    """
    def __init__(self, parent, state_manager, *, on_snapshot_select, on_refresh):
        super().__init__(parent, text="Snapshots")
        self.state_manager = state_manager
        self._on_snapshot_select = on_snapshot_select
        self._on_refresh = on_refresh
        self.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Search row
        header_text = ttk.Frame(self)
        header_text.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(header_text, text="Search: ").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(header_text)
        self.search_entry.pack(fill="x", expand=True, ipadx=40)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # Action buttons
        header_actions = ttk.Frame(self)
        header_actions.pack(fill="x", padx=10)
        ttk.Button(header_actions, text="✕ Clear",   command=self._on_clear).pack(expand=True, fill="x", pady=(10, 0))
        ttk.Button(header_actions, text="⟲ Refresh", command=self._on_refresh).pack(expand=True, fill="x", pady=(10, 0))

        # Snapshot list
        self.snapshot_list = tk.Listbox(self, relief="solid")
        self.snapshot_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.snapshot_list.bind("<<ListboxSelect>>", self._on_listbox_select)

    # Public interface
    # ---------------------------

    def populate_list(self, snapshots: list[str]) -> None:
        self.snapshot_list.delete(0, tk.END)
        for snap in snapshots:
            self.snapshot_list.insert(tk.END, snap)

    def get_search_query(self) -> str:
        return self.search_entry.get()

    def get_selected_snapshot(self) -> str | None:
        selection = self.snapshot_list.curselection()
        if not selection:
            return None
        return self.snapshot_list.get(selection[0])

    # Private event handlers
    # ---------------------------

    def _on_search_change(self, event) -> None:
        query = self.search_entry.get()
        filtered = self.state_manager.filter_list(query)
        self.populate_list(filtered)

    def _on_clear(self) -> None:
        self.search_entry.delete(0, tk.END)
        self._on_search_change(None)

    def _on_listbox_select(self, event) -> None:
        snapshot = self.get_selected_snapshot()
        if snapshot:
            self._on_snapshot_select(snapshot)


class MainArea(ttk.LabelFrame):
    """
    Displays the record table with tab-per-type and record search.
    Knows nothing about Sidebar — notifies the controller via callbacks.
    """

    def __init__(self, parent, state_manager, *, on_tab_change):
        super().__init__(parent, text="Records")
        self.state_manager  = state_manager
        self._on_tab_change = on_tab_change
        self.grid(row=0, column=1, sticky="nsew")

        # Search bar
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(header, text="Search: ").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(header)
        self.search_entry.pack(side="left", ipadx=50)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        ttk.Button(header, text="✕ Clear", command=self._on_clear).pack(side="left", padx=(10, 0))

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_change)

        # One Treeview per tab
        self.trees: dict[str, ttk.Treeview] = {}
        for tab_name in TAB_NAMES:
            frame = tk.Frame(self.notebook)
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)
            self.notebook.add(frame, text=tab_name)

            columns = COLUMN_MAP[tab_name]
            tree = ttk.Treeview(frame, columns=columns, show="headings")
            tree.grid(row=0, column=0, sticky="nsew")
            for col in columns:
                tree.heading(col, text=col.replace("_", " ").replace(".", " ").title())
                tree.column(col, width=160, anchor="w")

            ysb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
            xsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscroll=ysb.set, xscroll=xsb.set)
            ysb.grid(row=0, column=1, sticky="ns")
            xsb.grid(row=1, column=0, sticky="ew")

            self.trees[tab_name] = tree

    # Public interface
    # ---------------------------

    def get_active_mode(self) -> str:
        return TAB_NAMES[self.notebook.index(self.notebook.select())]

    def update_table(self, dataset: dict) -> None:
        data_type = dataset["type"]
        df        = dataset["dataset"]
        columns   = COLUMN_MAP.get(data_type)

        if not columns:
            raise ValueError(f"Unknown dataset type: {data_type}")

        tree = self.trees[data_type]
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=[row.get(col, "") for col in columns])

    # Private event handlers
    # ---------------------------

    def _on_notebook_tab_change(self, event) -> None:
        self._on_tab_change()

    def _on_search_change(self, event) -> None:
        query    = self.search_entry.get()
        mode     = self.get_active_mode()
        filtered = self.state_manager.filter_data(query, mode)
        self.update_table(filtered)

    def _on_clear(self) -> None:
        self.search_entry.delete(0, tk.END)
        self._on_search_change(None)