from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, RichLog, Select, TextArea, Collapsible
from textual.screen import ModalScreen, Screen

from episode_names.Utility.i18n import i18n


class YesNoBox(ModalScreen[bool | None]):
    """
    Simple general purpose question thingy for the occasion that you actually
    need to answer a simple yes/no question. This feels like something I could
    find elsewhere as boiler plate
    """
    BINDINGS = [
        Binding("enter", "accept_true", i18n['Yes'])
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
    def _btn_save(self) -> None:
        self._action_accept_true()

    @on(Button.Pressed, "#btn_no")
    def _btn_save(self) -> None:
        self._action_decline_false()

    def _action_accept_true(self):
        self.dismiss(True)

    def _action_decline_false(self):
        self.dismiss(False)