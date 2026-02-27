from aqt import gui_hooks, mw
from aqt.utils import qconnect
from aqt.qt import QDialog
from .ui.game_selector import GameSelector
from .games.memory_flip import MemoryFlipGame
from .games.line_match import LineMatchGame


def launch_game(deck_id):
    deck      = mw.col.decks.get(deck_id)
    deck_name = deck["name"]

    selector = GameSelector(deck_name)
    result   = selector.exec()

    if result == QDialog.DialogCode.Accepted:
        if selector.chosen_mode == "memory_flip":
            game = MemoryFlipGame(deck_name)
            game.exec()
        elif selector.chosen_mode == "line_match":
            game = LineMatchGame(deck_name)
            game.exec()


def add_game_option(menu, deck_id):
    action = menu.addAction("🎮 Play as Game")
    qconnect(action.triggered, lambda: launch_game(deck_id))


gui_hooks.deck_browser_will_show_options_menu.append(add_game_option)