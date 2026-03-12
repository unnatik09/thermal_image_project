import json
import os
from dataclasses import dataclass, asdict

SETTINGS_FILE = "tc001_settings.json"


@dataclass
class Settings:
    camera_index:    int   = 0
    mad_threshold:   float = 2.0
    min_fruit_area:  int   = 3000
    max_fruit_area:  int   = 200000
    snapshot_dir:    str   = "snapshots"
    recordings_dir:  str   = "."

    def save(self, path: str = SETTINGS_FILE):
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
        print(f"[Settings] Saved → {path}")

    @classmethod
    def load(cls, path: str = SETTINGS_FILE) -> 'Settings':
        if not os.path.exists(path):
            print("[Settings] No settings file found, using defaults.")
            return cls()
        with open(path) as f:
            data = json.load(f)
        print(f"[Settings] Loaded from {path}")
        return cls(**data)

    def apply_to_detector(self):
        """Push area thresholds into detector module live."""
        import detector
        detector.MIN_FRUIT_AREA = self.min_fruit_area
        detector.MAX_FRUIT_AREA = self.max_fruit_area

    def apply_to_classifier(self):
        """Push MAD threshold into classifier module live."""
        import classifier
        classifier.MAD_THRESHOLD = self.mad_threshold