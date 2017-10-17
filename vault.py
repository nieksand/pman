"""
In-memory representation of credential vault.
"""
import datetime
import json
from typing import Any, Dict, List

def current_dt() -> str:
    """Current UTC date and time as 'yyyy-mm-dd hh:mm:ss'."""
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def parse_dt(dt: str) -> datetime.datetime:
    """Parse 'yyyy-mm-dd hh:mm:ss' to datetime."""
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


class Vault:
    def __init__(self) -> None:
        """Create empty vault."""
        self.entries = {}

    def list(self) -> List[str]:
        """List vault contents."""
        return sorted(self.entries.keys())

    def set(self, credname: str, **data) -> None:
        """Set vault entry."""
        # keeps old created if overwriting existing entry
        now = current_dt()
        data['created'] = self.entries.get(credname, {}).get('created', now)
        data['modified'] = now
        self.entries[credname] = data

    def get(self, credname: str) -> Dict[str, Any]:
        """Get vault entry."""
        return self.entries[credname]

    def search(self, credsubstr: str) -> List[str]:
        """Case-insensitive substring search of vault."""
        css_low = credsubstr.lower()
        return sorted([k for k in self.entries if css_low in k.lower()])

    def remove(self, credname: str) -> None:
        """Remove vault entry."""
        del self.entries[credname]

    def dumps(self) -> str:
        """Serialize vault using JSON."""
        return json.dumps(self.entries)

    def loads(self, s: str) -> None:
        """Deserialize vault from JSON."""
        self.entries = json.loads(s)
