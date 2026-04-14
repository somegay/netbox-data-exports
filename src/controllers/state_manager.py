import pandas

COMBOBOX_VALS = ["IP Address", "Devices"]
IP_IDENTIFIER = "ip_addresses_export_"
DEVICE_IDENTIFIER = "devices_export_"
FILE_FORMAT = ".csv"

class StateManager:
    def __init__(self, export_path):
        self.snapshot_path = export_path
        self.ip_list = []
        self.filtered_ip_list = []
        self.device_list = []
        self.filtered_device_list = []
        self.dataset = {
            "dataset": [],
            "type": ""
        }

    def get_ip_list(self):
        return self.ip_list

    def get_device_list(self):
        return self.device_list

    def refresh_snapshot_list(self):
        snapshot_list = list(self.snapshot_path.glob("*.csv"))
        self.ip_list = [
            snapshot.name.replace(IP_IDENTIFIER, "").removesuffix(FILE_FORMAT)
            for snapshot in snapshot_list 
            if snapshot.name.startswith(IP_IDENTIFIER)]
        self.device_list = [
            snapshot.name.replace(DEVICE_IDENTIFIER, "").removesuffix(FILE_FORMAT) 
            for snapshot in snapshot_list 
            if snapshot.name.startswith(DEVICE_IDENTIFIER)]
    
    def filter_list(self, query, mode):
        query = query.lower().strip()
        if query == "":
            if mode == COMBOBOX_VALS[0]:
                return self.ip_list
            elif mode == COMBOBOX_VALS[1]:
                return self.device_list
        if mode == COMBOBOX_VALS[0]:  
            return [
                snap for snap in self.ip_list
                if query in snap.lower()
            ]
        elif mode == COMBOBOX_VALS[1]:
            return [
                snap for snap in self.device_list
                if query in snap.lower()
            ]
    
    def load_dataset(self, record_name, type):
        df = pandas.read_csv(self.snapshot_path / record_name)
        return {
            "type": type,
            "dataset": df,
        }

    def filter_data(self):
        # 1. TAKE CURRENT DATASET
        # 2. FILTER BASED ON SEARCH CRITERIA
        # 3. UPDATE TREE VIEW BASED ON FILTERED DATA
        print("Search data")