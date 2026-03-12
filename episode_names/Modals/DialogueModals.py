from textual import on, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, MarkdownViewer, Checkbox
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

class ConfirmMessageBox(ModalScreen[bool]):
    """
    You got to inform the user about something, and maybe you actually need
    them to check a checkbox to make sure that the information was actually
    received. This is the handy modal for that
    """
    BINDINGS = [
        Binding("enter", "accept_accept_true", i18n['Yes']),
        Binding("escape", "accept_decline_false", i18n['No'])
    ]
    def __init__(self, message: str, aknowledge: bool = False, confirm_text: str = i18n['Confirm that this was read']):
        """

        :param message: Message to user, can be MarkDown as displayed in MD Viewer
        :param aknowledge: if True, additional checkbox for True return needed
        """
        self.messagebox = message
        self.display_checkbox = aknowledge
        self.confirm_text = confirm_text
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="adjust"):
                yield MarkdownViewer(self.messagebox, show_table_of_contents=False)
            if self.display_checkbox:
                yield Checkbox(self.confirm_text, id="check")
            with Horizontal(classes="adjust buttons"):
                yield Button(i18n['Yes'], id="btn_yes")
                yield Button(i18n['Cancel'], id="btn_no")

    def _on_mount(self) -> None:
        if self.display_checkbox:
            self.query_exactly_one("#btn_yes").disabled = True

    @on(Button.Pressed, "#btn_yes")
    def _btn_yes(self) -> None:
        self.action_accept_true()

    @on(Button.Pressed, "#btn_no")
    def _btn_no(self) -> None:
        self.action_decline_false()

    @on(Checkbox.Changed, "#check")
    def checkbox_changed(self):
        my_checkbox: Checkbox = self.query_exactly_one("#check")
        yes_button: Button = self.query_exactly_one('#btn_yes')
        if my_checkbox.value:
            yes_button.disabled = False
        else:
            yes_button.disabled = True

    def action_accept_true(self):
        my_checkbox: Checkbox = self.query_exactly_one("#check")
        if my_checkbox.value: # when not checked, enter does nothing
            self.dismiss(True)

    def action_decline_false(self):
        self.dismiss(False)