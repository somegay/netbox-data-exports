# ── Dataset types ─────────────────────────────────────────────────────────────

TAB_NAMES         = ["IP Address", "Devices"]
IP_IDENTIFIER     = "ip_addresses_export_"
DEVICE_IDENTIFIER = "devices_export_"
FILE_FORMAT       = ".csv"

IP_COLUMNS = [
    "id",
    "status.label",
    "role",
    "address",
    "dns_name",
    "description",
    "assigned_object.device.name",
    "tenant.display",
    "last_updated",
]

DEVICE_COLUMNS = [
    "id",
    "name",
    "status.label",
    "role.display",
    "device_type.display",
    "site.display",
    "primary_ip4.display",
    "tenant.display",
    "last_updated"
]

COLUMN_MAP = {
    "IP Address": IP_COLUMNS,
    "Devices":    DEVICE_COLUMNS,
}

IDENTIFIER_MAP = {
    "IP Address": IP_IDENTIFIER,
    "Devices":    DEVICE_IDENTIFIER,
}