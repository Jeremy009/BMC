""" This script is used to quickly and easily label and annotate all received bills, invoices, and payment statements.
To use the labeler it suffices to run this script. No additional setup is required. """

import os
import shutil
import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTableWidgetItem, QFileDialog
import pandas as pd


class InvoiceProcessingMainWindow(QMainWindow):
    def __init__(self):
        super(InvoiceProcessingMainWindow, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'process_invoices.ui'), self)
        self.connect_signals_to_slots()
        self.set_msg_view("Go to File and open a directory to get started.")
        self.show()
        self.move(QApplication.desktop().screen().rect().center() - self.centralWidget().rect().center())

        self.supported_formats = [".pdf", ".jpg", ".png"]
        self.root_dir = None
        self.orig_dir = None
        self.labeled_dir = None
        self.processed_dir = None
        self.current_file = None
        self.table_data = None

    # Setup
    def connect_signals_to_slots(self):
        self.commit_button.clicked.connect(self.commit)
        self.refresh_button.clicked.connect(self.refresh_table_view)
        self.open_directory_action.triggered.connect(self.open_directory)
        self.export_action.triggered.connect(self.export_labels_frame)
        self.quit_action.triggered.connect(self.quit)

    # View
    def set_msg_view(self, msg):
        self.title_label.setText(msg)
        self.title_label.show()

        self.amount_input.hide()
        self.amount_label.hide()
        self.comment_input.hide()
        self.comment_label.hide()
        self.creditor_input.hide()
        self.creditor_label.hide()
        self.date_input.hide()
        self.date_label.hide()
        self.comment_input.hide()
        self.comment_label.hide()
        self.subtitle_label.hide()
        self.commit_button.hide()

    def refresh_table_view(self):
        doc_nr_col_data = []
        amount_col_data = []
        data_col_data = []
        creditor_col_data = []
        com_col_data = []
        doc_name_col_data = []

        if self.labeled_dir is not None and self.labeled_dir.is_dir:
            for file in self.labeled_dir.iterdir():
                if file.name.find(".ini") != -1:
                    continue
                doc_name = file.name
                doc_name_col_data.append(doc_name)
                doc_nr_col_data.append(doc_name.split("__")[0])
                amount_col_data.append(
                    doc_name.split("_")[3].lstrip("0").replace("EUR", self.decimal_point_input.text()))
                data_col_data.append(doc_name.split("_")[4])
                creditor_col_data.append(doc_name.split("_")[5].split(".")[0])
                try:
                    com_col_data.append(doc_name.split("_")[6].split(".")[0])
                except IndexError:
                    com_col_data.append(None)

            data = {
                'Nr': doc_nr_col_data,
                'Amount': amount_col_data,
                'Date': data_col_data,
                'Creditor': creditor_col_data,
                'Comment': com_col_data,
                'Document': doc_name_col_data,
                'Sort amount': [a.zfill(8) for a in amount_col_data],
                'Sort date': [c.split("-")[1] + "-" + c.split("-")[0] + "-" + c.split("-")[2] for c in data_col_data],
            }

            self.table_data = data
            self.set_table_data_data()

        else:
            msg = "Warning: could not load processed data/files because the directory has not yet been opened."
            QMessageBox.warning(self, "Warning", msg)

    def set_table_data_data(self):
        self.table_widget.setRowCount(len(self.table_data['Nr']))
        self.table_widget.setColumnCount(len(self.table_data.keys()))
        self.table_widget.setSortingEnabled(False)

        header = []
        for n, key in enumerate(self.table_data.keys()):
            header.append(key)
            for m, item in enumerate(self.table_data[key]):
                newitem = QTableWidgetItem(item)
                self.table_widget.setItem(m, n, newitem)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setHorizontalHeaderLabels(header)
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        self.table_widget.update()
        self.table_widget.setUpdatesEnabled(True)

    # Action triggers and slots
    def export_labels_frame(self):
        df = pd.DataFrame(list(zip(self.table_data['Nr'], self.table_data['Amount'], self.table_data['Date'],
                                   self.table_data['Comment'], self.table_data['Document'])),
                          columns=['Nr', 'Amount', 'Date', 'Comment', 'Document'])
        df.to_excel(str(self.root_dir.parent.joinpath("labeled documents.xlsx")) + "", index=False)

    def open_directory(self):
        self.root_dir = Path(QFileDialog.getExistingDirectory(self, "Select the 'Documents depenses' folder"))

        if self.root_dir is not None and self.root_dir.is_dir() and self.root_dir.name == "Documents depenses":
            self.orig_dir = self.root_dir.joinpath("Originaux")
            self.labeled_dir = self.root_dir.joinpath("Tries_NE_RIEN_CHANGER")
            self.processed_dir = self.root_dir.joinpath("Traites_NE_RIEN_CHANGER")
            self.analyse_directory()
        else:
            msg = "Warning: could not process the selected directory. Please make sure\n" \
                  "to select the correct 'Documents depenses' directory."
            QMessageBox.warning(self, "Warning", msg)

    def analyse_directory(self):
        assert self.orig_dir.is_dir()
        assert self.labeled_dir.is_dir()
        assert self.processed_dir.is_dir()

        for file in self.orig_dir.iterdir():
            if file.is_file():

                # Check if the file was already processed in the past
                if Path(str(file).replace("Originaux", "Traites_NE_RIEN_CHANGER")).is_file():
                    continue

                # Check if the filetype is supported
                if file.suffix.lower() not in self.supported_formats:
                    msg = "ERROR: {}\ncould not be processed because the filetype is not (yet) supported!\n\n" \
                          "Execution will continue but this file will be skipped.".format(file)
                    QMessageBox.critical(self, "Error", msg)
                    continue

                # The filetype is supported and was not yet processed so do process
                self.current_file = file
                self.process_file()
                return

        self.set_msg_view("{} out of {} files found in 'Originaux' have been labeled. Relax :)".format(
            len([f for f in self.processed_dir.iterdir() if f.stem[0] != -1]),
            len([f for f in self.orig_dir.iterdir() if f.stem[0] != -1])))

    def process_file(self):
        self.title_label.setText("PROCESSING FILE")
        self.subtitle_label.setText(self.current_file.name)
        self.amount_input.setValue(0.0)
        self.date_input.setDate(QDate(2020, 1, 1))
        self.creditor_input.setText("")
        self.comment_input.setPlainText("")

        self.title_label.show()
        self.amount_input.show()
        self.amount_label.show()
        self.comment_input.show()
        self.comment_label.show()
        self.creditor_input.show()
        self.creditor_label.show()
        self.date_input.show()
        self.date_label.show()
        self.comment_input.show()
        self.comment_label.show()
        self.subtitle_label.show()
        self.commit_button.show()
        self.open_with_chrome()

    def commit(self):
        if self.validate_commit():
            if self.accept_current_file():
                self.kill_chrome()
                self.current_file = None
                self.analyse_directory()

    def validate_commit(self):
        if self.current_file is None:
            msg = "WARNING: could not commit because the current file is None"
            QMessageBox.warning(self, "Warning", msg)
            return False
        if not isinstance(self.current_file, Path) or not self.current_file.is_file():
            msg = "WARNING: could not commit because the file does not exist.\n\nFile: {}".format(self.current_file)
            QMessageBox.warning(self, "Warning", msg)
            return False
        if self.amount_input.value() <= 0.0:
            msg = "WARNING: could not commit because amount should be > 0.0.\n\nFile: {}".format(self.current_file)
            QMessageBox.warning(self, "Warning", msg)
            return False
        if self.creditor_input.text() is None or len(self.creditor_input.text()) < 3:
            msg = "WARNING: could not commit because creditor should be at least 3 characters long.\n\nFile: {}".format(
                self.current_file)
            QMessageBox.warning(self, "Warning", msg)
            return False
        if self.date_input.date() <= QDate(2020, 1, 1):
            msg = "WARNING: could not commit because date should be after 2020.\n\nFile: {}".format(self.current_file)
            QMessageBox.warning(self, "Warning", msg)
            return False
        pass
        return True

    def accept_current_file(self):
        try:
            doc_nr = len([f for f in self.processed_dir.iterdir() if (f.stem[0] != -1 and f.suffix != ".ini")]) + 1
            am = int(self.amount_input.value())
            dec = round(self.amount_input.value() - am, 2)
            dd = self.date_input.date().day()
            mm = self.date_input.date().month()
            yyyy = self.date_input.date().year()
            cred = self.creditor_input.text().lower().capitalize()
            suf = self.current_file.suffix
            com = self.comment_input.toPlainText().lower().capitalize().replace(".", " ").replace("\n", " ")

            dec_str = str(dec).split(".")[1]
            if len(dec_str) == 1:
                dec_str = dec_str + "0"
            com_str = "" if len(com) == 0 else "_{}".format(com)

            labeled_file_name = "DEP2022_{:03}__{:04}EUR{}_{:02}-{:02}-{}_{}{}{}".format(doc_nr, am, dec_str, dd, mm, yyyy,
                                                                                         cred, com_str, suf)
            shutil.copy(str(self.current_file), str(self.labeled_dir.joinpath(labeled_file_name)))
            shutil.copy(str(self.current_file), str(self.current_file).replace("Originaux", "Traites_NE_RIEN_CHANGER"))
            self.amount_input.setFocus()
            return True
        except Exception as e:
            msg = "WARNING: could not commit due to an unexpected error.\n\nFile: {}\n\n{}".format(self.current_file, e)
            QMessageBox.warning(self, "Warning", msg)
            return False

    def quit(self):
        self.close()

    def open_with_chrome(self):
        if sys.platform == "darwin":
            os.system("open -a \"Google Chrome\" \"{}\"".format(self.current_file))
        elif sys.platform == "win32":
            os.system("start chrome \"{}\"".format(self.current_file))
        else:
            raise OSError("Only Windows and Mac are currently supported")

    @staticmethod
    def kill_chrome():
        # os.system("taskkill /IM chrome.exe /F")
        pass


if __name__ == "__main__":
    app = QApplication([])
    _ = InvoiceProcessingMainWindow()
    sys.exit(app.exec_())
