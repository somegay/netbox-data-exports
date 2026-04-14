import pandas
from .constants import IP_IDENTIFIER, DEVICE_IDENTIFIER, FILE_FORMAT, IDENTIFIER_MAP


class StateManager:
    """
    State Manager for netbox objects.
    """
    def __init__(self, export_path):
        self.snapshot_path = export_path
        self.ip_list = []
        self.device_list = []
        self.dataset = {"dataset": [], "type": ""}

    # Snapshot list
    # ---------------------------

    def refresh_snapshot_list(self) -> None:
        """
        Fetches list of snapshots from the exports folder and updates the local list of copy with the new one.
        """
        snapshot_list = list(self.snapshot_path.glob("*.csv"))
        # Filter fetched snapshots to IP Address only
        self.ip_list = [
            s.name.replace(IP_IDENTIFIER, "").removesuffix(FILE_FORMAT)
            for s in snapshot_list if s.name.startswith(IP_IDENTIFIER)
        ]
        # Filter fetched snapshots to devices only
        self.device_list = [
            s.name.replace(DEVICE_IDENTIFIER, "").removesuffix(FILE_FORMAT)
            for s in snapshot_list if s.name.startswith(DEVICE_IDENTIFIER)
        ]

    def filter_list(self, query: str) -> list[str]:
        """
        Return the sorted union of snapshot dates for both types,
        optionally filtered by a search query.

        Args:
            query (str): Search query to filter for.
        
        Returns:

        """
        query = query.lower().strip()
        # Stores list of snapshots for both ip and devices in a set
        combined = sorted(set(self.ip_list) | set(self.device_list))
        if not query:
            return combined
        return [snap for snap in combined if query in snap.lower()]

    # Dataset
    # --------------------------- 

    def build_filename(self, snapshot_name: str, mode: str) -> str:
        """Construct the CSV filename from a snapshot date string and mode."""
        identifier = IDENTIFIER_MAP.get(mode)
        if not identifier:
            raise ValueError(f"Unknown mode: {mode}")
        return identifier + snapshot_name + FILE_FORMAT

    def load_dataset(self, snapshot_name: str, mode: str) -> dict:
        """Load a CSV by snapshot name + mode and cache it as the active dataset."""
        filename = self.build_filename(snapshot_name, mode)
        df = pandas.read_csv(self.snapshot_path / filename)
        self.dataset = {"type": mode, "dataset": df}
        return self.dataset

    def filter_data(self, query: str, data_type: str) -> dict:
        """
        Filter the currently loaded dataset by a search query.
        Searches across all columns (case-insensitive substring match).
        """
        df = self.dataset["dataset"]

        if not isinstance(df, pandas.DataFrame) or df.empty:
            return {"type": data_type, "dataset": pandas.DataFrame()}

        if query.strip():
            mask = df.apply(
                lambda col: col.astype(str).str.contains(query, case=False, na=False)
            ).any(axis=1)
            df = df[mask]

        return {"type": data_type, "dataset": df}