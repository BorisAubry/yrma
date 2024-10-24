from textual import on
from textual.app import App
from textual.containers import Horizontal, Vertical, Center
from textual.widgets.selection_list import Selection
from textual.widgets.option_list import Option
from textual.widgets import (
    Footer,
    Header,
    SelectionList,
    Static,
    OptionList,
    Input,
    Label,
)
from data import DataHandler


class VideoMngt(Static):

    BINDINGS = [
        ("u", "update", "Update list"),
        ("s", "sort_by_length", "Sort by duration"),
        ("ctrl+d", "download_all", "Download all"),
        ("d", "download_selected", "Download selected"),
        ("ctrl+k", "discard_all", "Discard all"),
        ("k", "discard_selected", "Discard selected"),
    ]

    def __init__(
        self,
        renderable="",
        *,
        expand=False,
        shrink=False,
        markup=True,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        handler: DataHandler,
    ):
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.handler = handler

    def compose(self):
        with Center():
            yield SelectionList[str]()

    def on_mount(self) -> None:
        sl = self.query_one(SelectionList)
        sl.border_title = "Available for download video list"
        self.create_video_list()

    def activation(self):
        self.remove_class("inactive")
        self.add_class("active")
        self.create_video_list()
        self.query_one(SelectionList).focus()

    def desactivation(self):
        sl = self.query_one(SelectionList)
        sl.clear_options()
        self.remove_class("active")
        self.add_class("inactive")

    def create_video_list(self, sort_by_len: bool = False):
        sl = self.query_one(SelectionList)
        sl.clear_options()
        v_list = self.handler.get_video_from_pool(sort_by_len)
        for v in v_list:
            sl.add_option(
                Selection(
                    prompt=v["prompt"],
                    value=v["id"],
                    id=v["id"],
                )
            )

    def get_selection_list(self, all: bool) -> list:
        sl = self.query_one(SelectionList)
        if all:
            sl.select_all()
        return sl.selected

    def action_update(self):
        self.handler.get_new_videos_to_pool()
        self.create_video_list()

    def action_sort_by_length(self):
        self.create_video_list(sort_by_len=True)

    def action_download_all(self):
        self.handler.download_video_from_list(self.get_selection_list(all=True))
        self.handler.set_videos_pool(self.get_selection_list(all=True), in_pool=False)
        self.create_video_list()
        self.notify("All videos downloaded !", timeout=5)

    def action_download_selected(self):
        self.handler.download_video_from_list(self.get_selection_list(all=False))
        self.handler.set_videos_pool(self.get_selection_list(all=False), in_pool=False)
        self.create_video_list()
        self.notify("Selected videos downloaded ! ", timeout=5)

    def action_discard_all(self):
        self.handler.set_videos_pool(self.get_selection_list(all=True), in_pool=False)
        self.create_video_list()
        self.notify("All videos discarded !", timeout=5)

    def action_discard_selected(self):
        self.handler.set_videos_pool(self.get_selection_list(all=False), in_pool=False)
        self.create_video_list()
        self.notify("Selected videos discarded !", timeout=5)


class ChannelMngt(Static):
    BINDINGS = [
        ("a", "goto_add_channel", "Add Channel"),
        ("d", "delete_channel", "Delete channel"),
        ("p", "promote_selected", "Promote selected to available"),
        ("m", "modify_path", "Modify downloading path"),
    ]

    def __init__(
        self,
        renderable="",
        *,
        expand=False,
        shrink=False,
        markup=True,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        handler: DataHandler,
    ):
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.handler = handler

    def compose(self):
        with Vertical():
            yield Label("Actual download path is : ")
            yield Input(
                placeholder="Enter an id of a new channel here",
                id="url",
            )
            with Horizontal():
                yield OptionList(id="channels")
                yield SelectionList[str](id="chan_videos")

    def on_mount(self) -> None:
        ol = self.query_one(OptionList)
        ol.border_title = "Channels"
        sl = self.query_one(SelectionList)
        sl.border_title = "Selected channel video list"
        lb = self.query_one(Label)
        lb.update("Actual download path is : " + self.handler.get_dl_path())

    def activation(self):
        self.remove_class("inactive")
        self.add_class("active")
        self.create_channel_list()
        self.query_one(OptionList).focus()

    def desactivation(self):
        sl = self.query_one(SelectionList)
        sl.clear_options()
        ol = self.query_one(OptionList)
        ol.clear_options()
        self.remove_class("active")
        self.add_class("inactive")

    def get_selection_list(self, all: bool) -> list:
        sl = self.query_one(SelectionList)
        if all:
            sl.select_all()
        return sl.selected

    @on(Input.Submitted)
    def add_channel(self):
        u_input = self.query_one(Input)
        if "path" not in u_input.classes:
            if self.handler.is_channel_input_known(u_input.value):
                self.notify("Channel is already known !", timeout=5)
            else:
                if self.handler.is_channel_input_valid(u_input.value):
                    self.handler.add_channel(u_input.value)
                    self.notify("Channel added", timeout=5)
                else:
                    self.notify(
                        "Channel id submitted is incorrect !",
                        timeout=2,
                        severity="error",
                    )
            u_input.clear()
            self.create_channel_list()
            self.query_one(OptionList).focus()
        else:
            if self.handler.is_new_path_valid(u_input.value):
                self.handler.set_new_path_for_dl(u_input.value)
                lb = self.query_one(Label)
                lb.update("Actual download path is : " + self.handler.get_dl_path())
                self.notify("Path modified !", timeout=5)
            else:
                self.notify("Path incorrect !", timeout=5, severity="error")

            u_input.remove_class("path")
            u_input.clear()
            u_input.placeholder = "Enter an id of a new channel here"
            self.query_one(OptionList).focus()

    def action_modify_path(self):
        u_input = self.query_one(Input)
        u_input.placeholder = "Paste your new path"
        u_input.add_class("path")
        u_input.focus()

    def action_goto_add_channel(self):
        self.query_one(Input).focus()

    def action_delete_channel(self):
        ol = self.query_one(OptionList)
        if ol.highlighted != None:
            id = ol.get_option_at_index(ol.highlighted).id
            self.handler.delete_channel(id)
            self.query_one(SelectionList).clear_options()
            self.create_channel_list()
            ol.focus()
            self.notify("Selected channel deleted", timeout=5)

    def action_promote_selected(self):
        self.handler.set_videos_pool(self.get_selection_list(all=False), in_pool=True)
        self.update_video_list()
        self.notify("Selected videos promoted to available for dowload", timeout=5)

    def create_channel_list(self):
        ol = self.query_one(OptionList)
        ol.clear_options()
        c_list = self.handler.get_channel_list()
        for c in c_list:
            ol.add_option(
                Option(
                    prompt=c["prompt"],
                    id=c["id"],
                )
            )

    @on(OptionList.OptionSelected)
    @on(OptionList.OptionHighlighted)
    def update_video_list(self):
        ol = self.query_one(OptionList)
        if ol.highlighted != None:
            id = ol.get_option_at_index(ol.highlighted).id
            sl = self.query_one(SelectionList)
            sl.clear_options()
            v_list = self.handler.get_video_from_channel_id(id)
            for v in v_list:
                sl.add_option(
                    Selection(
                        prompt=v["prompt"],
                        value=v["id"],
                        id=v["id"],
                    )
                )


class MainApp(App):

    BINDINGS = [
        ("c", "switch_to_channel", "Channels Menu"),
        ("v", "switch_to_video", "Videos Menu"),
        ("e", "exit_app", "Exit"),
    ]

    CSS_PATH = "view.tcss"

    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=False
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.handler = DataHandler()

    def compose(self):
        yield Header(show_clock=True)
        yield VideoMngt(
            id="V",
            classes="active",
            handler=self.handler,
        )
        yield ChannelMngt(
            id="C",
            classes="inactive",
            handler=self.handler,
        )
        yield Footer()

    def action_exit_app(self):
        self.app.exit()

    def action_switch_to_channel(self):
        self.notify("Switch to [b]CHANNEL MODE[/b]", timeout=5)
        self.query_one(VideoMngt).desactivation()
        self.query_one(ChannelMngt).activation()

    def action_switch_to_video(self):
        self.notify("Switch to [b]VIDEO MODE[/b]", timeout=5)
        self.query_one(ChannelMngt).desactivation()
        self.query_one(VideoMngt).activation()
