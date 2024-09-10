import sys
import traceback

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox


class UnhandeledExceptionObserver(QtCore.QObject):
    """ Observer class used to wrap the error report in a QMessageBox which can be shown to the user, before letting
    the app crash. """
    _exception_caught = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        """ Allows to catch all exceptions and report them to the user before letting the app crash. """
        super(UnhandeledExceptionObserver, self).__init__(*args, **kwargs)

        sys.excepthook = self.exception_hook
        self._exception_caught.connect(UnhandeledExceptionObserver.show_exception)

    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """ Function handling uncaught exceptions. It is triggered each time an uncaught exception occurs. """
        title = "{0} : {1}".format(exc_type.__name__, exc_value)
        tb = '\n'.join(["".join(traceback.format_tb(exc_traceback)), "{0}: {1}".format(exc_type.__name__, exc_value)])
        self._exception_caught.emit((title, tb))
        sys.exit()

    @staticmethod
    def show_exception(exception_data):
        """ Actually print the error report."""
        title, tb = exception_data[0], exception_data[1]
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Crash report : {}\t\t\t".format(title))
        msg.setInformativeText("Une erreur critique est survenue et l'application a crashée. Le stack trace ci-dessous "
                               "peut contenir des informations supplementaires.\n\nUn back-up devrait avoir été "
                               "sauvegardé permettante de récupérer les donnees en redémarrant l'application.\n")
        msg.setDetailedText(tb)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)
        msg.exec_()
