"""
In-memory representation of credential vault.
"""
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple
import json

def current_dt() -> str:
    """Current UTC date and time as 'yyyy-mm-dd hh:mm:ss'."""
    return datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

def parse_dt(dt: str) -> datetime:
    """Parse 'yyyy-mm-dd hh:mm:ss' to datetime."""
    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)


class Vault:
    """
    Credential vault.
    """

    def __init__(self) -> None:
        """Create empty vault."""
        self.entries: Dict[str, Dict[str, Any]] = {}

    def list(self) -> List[str]:
        """List vault contents."""
        return sorted(self.entries.keys())

    def set(self, credname: str, **data: Any) -> None:
        """Set vault entry."""
        # keeps old created if overwriting existing entry
        now = current_dt()
        data['created'] = self.entries.get(credname, {}).get('created', now)
        data['modified'] = now
        self.entries[credname] = data

    def get(self, credname: str) -> Dict[str, Any]:
        """Get vault entry."""
        return self.entries[credname]

    def contains(self, credname: str) -> bool:
        """Check if key in vault."""
        return credname in self.entries

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

    def merge(self, other: 'Vault') -> List[Tuple[str, str, Optional[str], Optional[str]]]:
        """Merge another vault into this one, keeping newest for conflicts.

        Returns list of (action, key, self_modified, other_modified) tuples where
        action is 'add', 'update', or 'skip'.
        """
        actions: List[Tuple[str, str, Optional[str], Optional[str]]] = []

        for key in other.list():
            if not self.contains(key):
                actions.append(('add', key, None, None))
                self.set(key, **other.get(key))
                continue

            self_cred = self.get(key)
            other_cred = other.get(key)
            if self_cred == other_cred:
                continue

            if self_cred['modified'] < other_cred['modified']:
                actions.append(('update', key, self_cred['modified'], other_cred['modified']))
                self.set(key, **other_cred)
            else:
                actions.append(('skip', key, self_cred['modified'], other_cred['modified']))

        return actions
