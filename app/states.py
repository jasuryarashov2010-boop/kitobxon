from aiogram.fsm.state import State, StatesGroup


class RecommendationForm(StatesGroup):
    waiting_title = State()
    waiting_author = State()
    waiting_reason = State()
    waiting_photo = State()
