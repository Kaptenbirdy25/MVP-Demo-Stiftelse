from __future__ import annotations

import json
from typing import List

from config import STIFTELSER_PATH
from models import Foundation


def load_foundations() -> List[Foundation]:
    with STIFTELSER_PATH.open("r", encoding="utf-8") as file:
        raw = json.load(file)
    return [Foundation.model_validate(item) for item in raw]
