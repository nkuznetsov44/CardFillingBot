from enum import Enum
from typing import Optional
import json
from aiogram.types import Message

class BudgetEditState(Enum):
    WAITING_FOR_AMOUNT = "waiting_for_amount"
    WAITING_FOR_PERIOD = "waiting_for_period"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"

class StateService:
    def __init__(self, cache_service):
        self.cache_service = cache_service

    def set_budget_edit_state(self, chat_id: int, state: BudgetEditState, data: dict = None) -> None:
        self.cache_service.rdb.set(
            f"budget_edit:{chat_id}",
            json.dumps({"state": state.value, "data": data or {}})
        )
    
    def get_budget_edit_state(self, chat_id: int) -> Optional[tuple[BudgetEditState, dict]]:
        data = self.cache_service.rdb.get(f"budget_edit:{chat_id}")
        if not data:
            return None
        parsed = json.loads(data)
        return BudgetEditState(parsed["state"]), parsed.get("data", {})
    
    def clear_budget_edit_state(self, chat_id: int) -> None:
        self.cache_service.rdb.delete(f"budget_edit:{chat_id}")
