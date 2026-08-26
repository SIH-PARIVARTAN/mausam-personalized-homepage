import json
from abc import ABC, abstractmethod
import datetime
from engine.models import SignalValue
import logging

logger = logging.getLogger(__name__)

class Adapter(ABC):
    @abstractmethod
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> any:
        pass

    def make_unavailable_signal(self) -> SignalValue:
        return SignalValue(value=None, source="unavailable", freshness_min=None, confidence=0.0)

    def load_fixture(self, filepath: str) -> dict:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fixture {filepath}: {e}")
            return None
