import re

CONTROL_PANEL_NAMES = (
    "CP-wang",
    "CP-RFR",
    "CP-Li",
    "CP-Luis",
)


def control_panel_name_for(power_box_name: str) -> str | None:
    tokens = re.split(r"[^a-z0-9]+", (power_box_name or "").casefold())
    tokens = [token for token in tokens if token]
    if "rfr" in tokens:
        return "CP-RFR"
    if "luis" in tokens:
        return "CP-Luis"
    if "li" in tokens:
        return "CP-Li"
    if "wang" in tokens or "pro5" in tokens:
        return "CP-wang"
    return None
