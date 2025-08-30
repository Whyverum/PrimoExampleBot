# bot/states/form.py
from aiogram.fsm.state import State, StatesGroup

class StartForm(StatesGroup):
    waiting_for_application: State = State()
