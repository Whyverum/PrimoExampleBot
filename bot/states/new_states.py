# bot/states/new_states.py
from aiogram.fsm.state import State, StatesGroup

class NewStates(StatesGroup):
    role: State = State()
    sorol: State = State()
    code_phrase: State = State()
    rules: State = State()
