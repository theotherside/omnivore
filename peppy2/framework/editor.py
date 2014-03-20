from os.path import basename

# Enthought library imports.
from traits.api import Bool, Unicode, Property
from pyface.tasks.api import Editor

class FrameworkEditor(Editor):
    """The pyface editor template for the peppy2 framework
    
    The abstract methods 
    """

    #### 'IProjectEditor' interface ############################################

    path = Unicode

    dirty = Bool(False)

    name = Property(Unicode, depends_on='path')

    tooltip = Property(Unicode, depends_on='path')

    #### property getters

    def _get_tooltip(self):
        return self.path

    def _get_name(self):
        return basename(self.path) or 'Untitled'

    ###########################################################################
    # 'FrameworkEditor' interface.
    ###########################################################################

    def create(self, parent):
        """ Creates the toolkit-specific control for the widget.
        """
        raise NotImplementedError

    def load(self, guess=None, **kwargs):
        """ Loads the contents of the editor.
        """
        raise NotImplementedError

    def view_of(self, editor, **kwargs):
        """ Copy the view of the supplied editor.
        """
        raise NotImplementedError

    def save(self, path=None):
        """ Saves the contents of the editor.
        """
        raise NotImplementedError
