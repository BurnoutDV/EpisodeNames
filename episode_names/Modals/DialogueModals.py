from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from episode_names.Utility import i18n


class YesNoBox(ModalScreen[bool | None]):
    """
    Simple general purpose question thingy for the occasion that you actually
    need to answer a simple yes/no question. This feels like something I could
    find elsewhere as boiler plate
    """
    BINDINGS = [
        Binding("enter", "accept_accept_true", i18n['Yes']),
        Binding("escape", "accept_decline_false", i18n['No'])
    ]

    def __init__(self, message: str = ""):
        self.internal_message = message
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="adjust"):
                yield Label(self.internal_message)
            with Horizontal(classes="adjust"):
                yield Button(i18n['Yes'], id="btn_yes")
                yield Button(i18n['No'], id="btn_no")

    @on(Button.Pressed, "#btn_yes")
    def _btn_yes(self) -> None:
        self.action_accept_true()

    @on(Button.Pressed, "#btn_no")
    def _btn_no(self) -> None:
        self.action_decline_false()

    def action_accept_true(self):
        self.dismiss(True)

    def action_decline_false(self):
        self.dismiss(False)