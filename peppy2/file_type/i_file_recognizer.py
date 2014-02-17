# Enthought library imports.
from traits.api import Interface, Str, List, Instance

class IFileRecognizer(Interface):
    """File recognizers must implement this AND be added to the list of known
    recognizers via a plugin that contributes to 'peppy2.file_recognizer'.
    
    """
    # The ID used in ordering recognizers.  This should correspond to a MIME
    # type that can be detected with this recognizer (if more than one MIME
    # type can be recognized, the most common MIME type can be used or a MIME-
    # like string containing the top-level media type and a descriptive subtype
    # may be used.  E.g.  "image/common" is used by the ImageRecognizer
    # plugin).
    id = Str

    # The recognizer will be processed after the item with this ID.
    after = Str

    # The recognizer will be processed before the item with this ID.
    before = Str

    def identify_bytes(self, byte_stream):
        """Return a MIME type if byte stream can be identified.
        
        If byte stream is not known, returns None
        """

class IFileRecognizerDriver(Interface):
    """ File type identifier service.
    
    """
    recognizers = List(Instance(IFileRecognizer))

    def recognize(self, guess):
        """Attempt to set the mime type of a FileGuess.
        """
