from src.controllers.gui_controller import GuiController

class Main:
    def __init__(self):
        # initialize configuration
        # initialize GUI
        self.gui_controller = GuiController(
            self.handle_list_refresh, 
            self.handle_list_search,
            self.handle_data_search,
            self.handle_snapshot_select)
        self.gui_controller.mainloop()
        self.handle_list_refresh()
    
    def refresh_snapshot_list(self):
        # FETCH LIST AGAIN
        pass

    def handle_list_refresh(self):
        # 1. REFRESH DATA
        # 2. UPDATE GUI WITH THE NEW LIST
        print("Refresh list")
        self.refresh_snapshot_list()
        self.gui_controller.update_status()
        self.gui_controller.update_snapshot_list()
    
    def handle_list_search(self):
        # 1. REFRESH DATA
        # 2. FILTER LIST
        # 3. UPDATE GUI WITH NEW LIST
        print("Search list")
        self.refresh_snapshot_list()
        self.gui_controller.update_status()
        self.gui_controller.update_snapshot_list()
    
    def handle_snapshot_select(self, event):
        # 1. GET SELECTED SNAPSHOT NAME FROM SIDEBAR
        # 2. OPEN FILE AND LOAD DATA
        # 3. UPDATE TREE VIEW WITH NEW DATA
        self.gui_controller.fetch_selected_snapshot()
        self.load_data()
        self.gui_controller.update_snapshot_data()
    
    def load_data(self):
        print("Load data for selected snapshot")

    def handle_data_search(self):
        # 1. TAKE CURRENT DATASET
        # 2. FILTER BASED ON SEARCH CRITERIA
        # 3. UPDATE TREE VIEW BASED ON FILTERED DATA
        self.gui_controller.fetch_snapshot_data_query()
        print("Search data")

if __name__ == "__main__":
    Main()