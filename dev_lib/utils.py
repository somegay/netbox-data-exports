from pathlib import Path
import json, re, csv

CSV_PATTERN = re.compile(
    r'^(devices|ip_addresses)_export_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.csv$'
)

def load_json(path: Path) -> dict:
    try:
        with path.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}") from e

def initialize_file(file: str):
    formatted_path = format_path(file)
    try:
        formatted_path.mkdir(parents=True, exist_ok=True)
        return formatted_path.open()
    except Exception as e:
        print (f"Error: {e}")

def format_path(path: str) -> Path:
    try:
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return Path().cwd() / path_obj
    except Exception as e:
        print(f"Error: {e}")

def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0

    with path.open(newline='', encoding='utf-8') as f:
        # subtract 1 for header
        return max(sum(1 for _ in f) - 1, 0)

def first_value(row, *keys, default="—"):
    for key in keys:
        val = row.get(key)
        if val:
            return str(val).strip()
    return default

def normalize_status(value):
    if not value:
        return "Unknown"

    v = value.strip().lower()

    if v in ("active", "online", "enabled"):
        return "Active"
    if v in ("standby", "offline"):
        return "Standby"
    if "maint" in v:
        return "Maintenance"
    if "reserv" in v:
        return "Reserved"
    if "dhcp" in v:
        return "DHCP"

    return value.capitalize()

def list_snapshots(csv_dir: Path):
    snapshots = {}

    for file in csv_dir.glob("*.csv"):
        match = CSV_PATTERN.match(file.name)
        if not match:
            continue

        kind, ts = match.groups()
        snap = snapshots.setdefault(ts, {
            "id": ts,
            "count": {"devices": 0, "ips": 0}
        })

        if kind == "devices":
            snap["devices_file"] = file.name
            snap["count"]["devices"] = count_csv_rows(csv_dir / file.name)

        if kind == "ip_addresses":
            snap["ips_file"] = file.name
            snap["count"]["ips"] = count_csv_rows(csv_dir / file.name)

    return list(snapshots.values())

def load_devices_csv(path: Path) -> list:
    devices = []

    if not path.exists():
        return devices

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            devices.append({
                "name": row.get("name", "Unnamed device"),

                # Role name (human readable)
                "type": (
                    row.get("role.name")
                    or row.get("role.display")
                    or "Device"
                ),

                # Proper status label
                "status": (
                    row.get("status.label")
                    or row.get("status.value")
                    or "Unknown"
                ),

                # Site name
                "site": (
                    row.get("site.name")
                    or "—"
                ),

                # Manufacturer + model
                "manufacturer": (
                    row.get("device_type.manufacturer.name")
                    or "—"
                ),
                "model": (
                    row.get("device_type.model")
                    or "—"
                ),

                # Primary IP (prefer IPv4)
                "ip_address": (
                    row.get("primary_ip4.address")
                    or row.get("primary_ip.address")
                    or "—"
                ),

                "description": row.get("description", ""),
            })

    return devices

def load_ips_csv(path: Path) -> list:
    ips = []

    if not path.exists():
        return ips

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ips.append({
                "address": row.get("address", "—"),

                "status": (
                    row.get("status.label")
                    or row.get("status.value")
                    or "Unknown"
                ),

                "assigned_to": (
                    row.get("assigned_object.display")
                    or row.get("assigned_object.name")
                    or "Unassigned"
                ),

                "vrf": (
                    row.get("vrf.name")
                    or "Global"
                ),

                "tenant": (
                    row.get("tenant.name")
                    or "—"
                ),

                "description": row.get("description", ""),
            })

    return ips
