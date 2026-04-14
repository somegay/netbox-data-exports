import pandas
from pathlib import Path

class StateManager:
    def __init__(self, export_path):
        self.snapshot_path = self.set_snapshot_path(export_path)
        self.snapshot_list = self.refresh_snapshot_list()
        self.dataset = []

    def set_snapshot_path(self, exports_path):
        base_path = Path(__file__).resolve().parent
        return base_path / exports_path

    def get_snapshot_list(self):
        return self.snapshot_list

    def refresh_snapshot_list(self):
        # FETCH LIST AGAIN
        pass

    def list_refresh(self):
        # 1. REFRESH DATA
        # 2. UPDATE GUI WITH THE NEW LIST
        print("Refresh list")
        self.refresh_snapshot_list()
    
    def filter_list(self):
        # 1. REFRESH DATA
        # 2. FILTER LIST
        # 3. UPDATE GUI WITH NEW LIST
        print("Search list")
        self.refresh_snapshot_list()
    
    def load_data(self):
        print("Load data for selected snapshot")

    def filter_data(self):
        # 1. TAKE CURRENT DATASET
        # 2. FILTER BASED ON SEARCH CRITERIA
        # 3. UPDATE TREE VIEW BASED ON FILTERED DATA
        print("Search data")