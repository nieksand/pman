import json
import datetime

def current_dt() -> str:
    """Current UTC date and time as 'yyyy-mm-dd hh:mm:ss'."""
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def parse_dt(dt: str) -> datetime.datetime:
    """Parse 'yyyy-mm-dd hh:mm:ss' to datetime."""
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


class Vault:
    def __init__(self) -> None:
        self.entries = {}

    def list(self):
        return sorted(self.entries.keys())

    def set(self, credname: str, **data) -> None:
        # keeps old created if overwriting existing entry
        now = current_dt()
        data['created'] = self.entries.get(credname, {}).get('created', now) 
        data['modified'] = now
        self.entries[credname] = data

    def get(self, credname: str):
        return self.entries[credname]

    def search(self, credsubstr: str):
        css_low = credsubstr.lower()
        return sorted([(k,v) for k, v in self.entries.items() if css_low in k.lower()])

    def remove(self, credname: str) -> None:
        del self.entries[credname]

    def dumps(self) -> str:
        return json.dumps(self.entries)

    def loads(self, s: str) -> None:
        self.entries = json.loads(s)
