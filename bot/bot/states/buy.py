"""FSM states for the purchase flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BuyStates(StatesGroup):
    """States for the buy-subscription FSM."""

    choosing_plan = State()
    choosing_provider = State()
