from omnivore.framework.panes import FrameworkPane

# Local imports.
from omnivore.tasks.hex_edit.segments import SegmentList
from omnivore.tasks.hex_edit.grid_control import HexEditControl
from omnivore.tasks.hex_edit.panes import CommentsPanel
from omnivore.framework.undo_panel import UndoHistoryPanel
from omnivore.utils.wx.springtabs import SpringTabs

import logging
log = logging.getLogger(__name__)


class SegmentsPane(FrameworkPane):
    #### TaskPane interface ###################################################

    id = 'jumpman.segments'
    name = 'Segments'
    
    def create_contents(self, parent):
        control = SegmentList(parent, self.task, size=(64,150))
        return control


class UndoPane(FrameworkPane):
    #### TaskPane interface ###################################################

    id = 'jumpman.undo'
    name = 'Undo History'
    
    def create_contents(self, parent):
        control = UndoHistoryPanel(parent, self.task, size=(64,150))
        return control


class HexPane(FrameworkPane):
    #### TaskPane interface ###################################################

    id = 'jumpman.hex'
    name = 'Raw Level Data'
    
    def create_contents(self, parent):
        control = HexEditControl(parent, self.task, size=(300, 150))
        return control


class SidebarPane(FrameworkPane):
    #### TaskPane interface ###################################################

    id = 'jumpman.sidebar'
    name = 'Sidebar'
    
    movable = False
    caption_visible = False
    dock_layer = 9
    
    def comments_cb(self, parent, task, **kwargs):
        control = CommentsPanel(parent, task)
        
    def create_contents(self, parent):
        control = SpringTabs(parent, self.task, popup_direction="left")
        control.addTab("Comments", self.comments_cb)
        return control
    
    def refresh_active(self):
        active = self.control._radio
        if active is not None and active.is_shown:
            active.managed_window.refresh_view()