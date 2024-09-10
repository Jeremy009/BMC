import datetime
from abc import abstractmethod
from typing import Callable, List, Tuple

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate, QModelIndex, pyqtSlot
from PyQt5.QtGui import QKeyEvent, QCloseEvent
from PyQt5.QtWidgets import QGridLayout, QWidget, QSplitter, QHBoxLayout, QTextBrowser, QApplication, QCompleter, \
    QSizePolicy, QSpacerItem

from products import BMCProductsManager
from utils import get_button, get_fake_label


class BMCMainWidget(QWidget):
    """ This is the main widget which shows all buttons and views with which the user can do what you'd expect to do
    with a registry app. """

    def __init__(self, controller):
        super(BMCMainWidget, self).__init__()
        self.controller = controller

        # Buttons for locations and entries sales
        self.normal_button = get_button("Tarif normal", 200, 70)
        self.discount_button = get_button("Tarif réduit", 200, 70)
        self.member_button = get_button("Abonnement BMC", 200, 70)
        self.belt_button = get_button("Baudrier", 200, 70)
        self.belay_button = get_button("Gri-gri", 200, 70)
        self.shoe_button = get_button("Chaussons", 200, 70)
        self.kit_button = get_button("Kit", 200, 70)

        # Buttons for products sales
        self.product_bts = []
        for product in BMCProductsManager.products:
            button = get_button(product.name, 200, 50, product.color)
            self.product_bts.append(button)

        # Buttons for technical stuff
        self.operation_button = get_button("Operation caisse", 200, 40)
        self.history_button = get_button("Historique", 200, 40)
        self.reduction_button = get_button("Réduction {}%".format(int(100 - float(self.controller.config["reduction factor"])*100)), 200, 40)

        # Buttons for sale validations
        self.cash_button = get_button("Cash", 100, 75)
        self.card_button = get_button("Bancontact", 100, 75)
        self.cancel_button = get_button("Annuler", 100, 75)
        self.quit_button = get_button("Quitter", 100, 75)

        # Aggregate all buttons in one list
        self.buttons = [self.__dict__[key] for key in self.__dict__.keys() if key.find("button") != -1]
        self.buttons += self.product_bts
        for button in self.buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Text fields for sale validations
        self.details_textbrowser = QTextBrowser()
        self.recap_textbrowser = QTextBrowser()

        # Builder
        self.connect_signals_to_slots()
        self.build_ui()

    def connect_signals_to_slots(self) -> None:
        self.normal_button.clicked.connect(lambda: self.controller.update_transaction("entrée normale"))
        self.discount_button.clicked.connect(lambda: self.controller.update_transaction("entrée réduit"))
        self.member_button.clicked.connect(lambda: self.controller.update_transaction("abonnement BMC"))
        self.belt_button.clicked.connect(lambda: self.controller.update_transaction("location baudrier"))
        self.belay_button.clicked.connect(lambda: self.controller.update_transaction("location gri-gri"))
        self.shoe_button.clicked.connect(lambda: self.controller.update_transaction("location chaussons"))
        self.kit_button.clicked.connect(lambda: self.controller.update_transaction("location kit complet"))
        self.history_button.clicked.connect(lambda: self.controller.launch_history_view())
        self.operation_button.clicked.connect(lambda: self.controller.launch_custom_ops_view())
        self.cash_button.clicked.connect(lambda: self.controller.validate_transaction(modality="cash"))
        self.card_button.clicked.connect(lambda: self.controller.validate_transaction(modality="card"))
        self.reduction_button.clicked.connect(lambda: self.controller.apply_reduction(self.controller.config["reduction factor"]))
        self.cancel_button.clicked.connect(lambda: self.controller.cancel_transaction(self.product_bts))
        self.quit_button.clicked.connect(lambda: self.controller.launch_quit_view())

        for button in self.product_bts:
            button.clicked.connect(lambda _, b=button: self.controller.update_product(b))

    def build_ui(self) -> None:
        toplevel_h_layout = QHBoxLayout(self)
        toplevel_h_layout.setContentsMargins(3, 3, 3, 3)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.get_sales_input_grid())
        splitter.addWidget(self.get_sales_validation_view())
        toplevel_h_layout.addWidget(splitter)
        self.setLayout(toplevel_h_layout)

    def get_sales_input_grid(self) -> QWidget:
        sales_input_panel = QWidget()
        grid = QGridLayout()

        grid.addWidget(get_fake_label("Entrées"), 0, 0, 1, 4)
        grid.addWidget(self.normal_button, 1, 0)
        grid.addWidget(self.discount_button, 1, 1)
        grid.addWidget(self.member_button, 1, 2)
        separator = QWidget(minimumHeight=20)
        separator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid.addWidget(separator, 2, 0)

        grid.addWidget(get_fake_label("Locations"), 3, 0, 1, 4)
        grid.addWidget(self.belt_button, 4, 0)
        grid.addWidget(self.belay_button, 4, 1)
        grid.addWidget(self.shoe_button, 4, 2)
        grid.addWidget(self.kit_button, 4, 3)
        separator = QWidget(minimumHeight=20)
        separator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid.addWidget(separator, 5, 0)

        grid.addWidget(get_fake_label("Ventes"), 6, 0, 1, 4)
        i, j = 7, 0
        for button in self.product_bts:
            product = BMCProductsManager.get_with_name(button.objectName())
            if product.stock <= 0:
                button.setEnabled(False)
            button.setText(product.description)
            grid.addWidget(button, i, j)
            j += 1
            if j == 4:
                j = 0
                i += 1
        separator = QWidget(minimumHeight=20)
        separator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid.addWidget(separator, i + 1, 0)

        grid.addItem(QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding), i + 2, 0)

        grid.addWidget(self.history_button, i + 3, 0)
        grid.addWidget(self.operation_button, i + 3, 1)
        grid.addWidget(self.reduction_button, i + 3, 2)

        sales_input_panel.setLayout(grid)

        return sales_input_panel

    def get_sales_validation_view(self) -> QWidget:
        sales_validation_panel = QWidget()
        grid = QGridLayout()
        self.recap_textbrowser.setMinimumWidth(250)

        grid.addWidget(self.details_textbrowser, 0, 0, 1, 4)
        grid.addWidget(self.recap_textbrowser, 1, 0, 2, 2)
        grid.addWidget(self.cash_button, 1, 2)
        grid.addWidget(self.cancel_button, 1, 3)
        grid.addWidget(self.card_button, 2, 2)
        grid.addWidget(self.quit_button, 2, 3)

        sales_validation_panel.setLayout(grid)

        return sales_validation_panel


class BMCBaseChildWidget(QWidget):
    """ The BMCBaseWidget is an abstract class which implements some common behaviour between all widgets which can
    be spawned from a main widget and which need to connect to a controller. """

    def __init__(self, controller):
        super(BMCBaseChildWidget, self).__init__()
        self.setWindowTitle("")
        self.controller = controller
        self.controller.give_control_to_child()
        self.build_ui()
        self.connect_signals_to_slots()
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
        self.show()

    @abstractmethod
    def connect_signals_to_slots(self) -> None:
        pass

    @abstractmethod
    def build_ui(self) -> None:
        pass

    @abstractmethod
    def keyPressEvent(self, event: QKeyEvent) -> None:
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.controller.take_control_from_child()


class BMCLoginWidget(BMCBaseChildWidget):
    """ This widget requests some basic information needed to properly initialize the registry app such as the user, the
    date, and how much cash is (still) present in the registry. """

    def __init__(self, controller):
        super(BMCLoginWidget, self).__init__(controller)
        self.date_field.setDate(QDate.currentDate())
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.show()

    def connect_signals_to_slots(self) -> None:
        self.validate_button.clicked.connect(self.validate)

    def build_ui(self) -> None:
        uic.loadUi('resources/login.ui', self)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Return:
            self.validate()

    def closeEvent(self, event: QCloseEvent) -> None:
        if event.spontaneous():
            event.ignore()
        else:
            self.controller.take_control_from_child()

    def validate(self) -> None:
        try:
            # Try to validate the login data, may throw an error if supervisor invalid, which is to be handeled
            self.controller.validate_login(self.date_field.date(), self.get_cash_count(), self.supervisor_field.text())
            self.close()
        except ValueError:
            # ValueError is thrown when the supervisor's name is not in the list of approved supervisors
            pass

    def get_cash_count(self) -> float:
        cash_count = 0.
        cash_count += 200 * self.eur200_field.value()
        cash_count += 100 * self.eur100_field.value()
        cash_count += 50 * self.eur50_field.value()
        cash_count += 20 * self.eur20_field.value()
        cash_count += 10 * self.eur10_field.value()
        cash_count += 5 * self.eur5_field.value()
        cash_count += 2 * self.eur2_field.value()
        cash_count += 1 * self.eur1_field.value()
        cash_count += 0.5 * self.eur05_field.value()
        cash_count += 0.2 * self.eur02_field.value()
        cash_count += 0.1 * self.eur01_field.value()
        cash_count += 0.05 * self.eur005_field.value()

        return cash_count


class BMCHistoryWidget(BMCBaseChildWidget):
    """ This widget is very simple and just shows the history of this session's transactions, and a resume of the
    current session. It does nothing else. """

    def __init__(self, controller, transactions, resume):
        super(BMCHistoryWidget, self).__init__(controller)
        self.transactions_browser.setText(transactions)
        self.resume_browser.setText(resume)

    def connect_signals_to_slots(self) -> None:
        self.validate_button.clicked.connect(self.validate)

    def build_ui(self) -> None:
        uic.loadUi('resources/history.ui', self)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Escape:
            self.validate()

    def validate(self) -> None:
        self.close()


class BMCCustomOperationWidget(BMCBaseChildWidget):
    """ This widget makes it possible to register custom transactions which do not have a predifined title and value.
    Both positive (incoming) and negative (outgoing) transactions can be performed. """

    def __init__(self, controller):
        super(BMCCustomOperationWidget, self).__init__(controller)

    def connect_signals_to_slots(self) -> None:
        self.validate_button.clicked.connect(self.validate)
        self.cancel_button.clicked.connect(self.cancel)

    def build_ui(self) -> None:
        uic.loadUi('resources/operation.ui', self)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Return:
            self.validate()
        elif event.key() == Qt.Key_Escape:
            self.cancel()

    def validate(self) -> None:
        msg = self.msg_field.text()
        amount = float(self.amount_field.value())
        cash = self.cash_button.isChecked()
        card = self.card_button.isChecked()
        income = self.in_button.isChecked()
        expense = self.out_button.isChecked()

        if msg and amount > 0 and (cash ^ card) and (income ^ expense):
            amount = amount if income else -amount
            modality = "cash" if cash else "card"
            self.controller.custom_transaction(msg, amount, modality)
            self.close()

    def cancel(self) -> None:
        self.close()


class BMCAboWidget(BMCBaseChildWidget):
    """ This widget enables interactions with the clients and abonnements' database to query and set such data. It can
    spawn 2 different simple child widgets which allow showing suggestions when searching the database, or making a
    new abonnement. These are defined as inner classes as they can not really exist on their own. """

    class AutosearchWidget(QWidget):
        """ A simple QLineEdit which shows matching entries as you type. """

        def __init__(self, on_change: Callable, on_activate: Callable, on_close: Callable):
            super(BMCAboWidget.AutosearchWidget, self).__init__()
            self.setWindowTitle("")
            self.load_ui()
            self.connect_signals_to_slots()
            self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
            self.completer = QCompleter([])
            self.setup_autocompleter()
            self.on_change = on_change
            self.on_activate = on_activate
            self.on_close = on_close
            self.completer_triggered_change = False
            self.show()

        def closeEvent(self, event: QCloseEvent) -> None:
            self.on_close()

        def keyPressEvent(self, event: QKeyEvent) -> None:
            if event.key() == Qt.Key_Escape:
                self.close()

        def connect_signals_to_slots(self):
            self.close_button.clicked.connect(self.close)
            self.search_field.textChanged.connect(self.text_changed)

        def load_ui(self):
            uic.loadUi('resources/search_client.ui', self)

        def setup_autocompleter(self):
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.activated[QModelIndex].connect(self.completer_activated)
            self.completer.highlighted[QModelIndex].connect(self.completer_highlighted)
            self.search_field.setCompleter(self.completer)

        def set_completer_options(self, options: List[str]) -> None:
            model = self.completer.model()
            model.setStringList(options)

        @pyqtSlot(QModelIndex)
        def completer_activated(self, index: QModelIndex) -> None:
            self.completer_triggered_change = True
            self.on_activate(index.row())

        @pyqtSlot(QModelIndex)
        def completer_highlighted(self, _) -> None:
            self.completer_triggered_change = True

        @pyqtSlot()
        def text_changed(self) -> None:
            if not self.completer_triggered_change:
                self.on_change()
            self.completer_triggered_change = False

    class CreateAboWidget(QWidget):
        """ A simple widget to enter the additional data needed for making a new abonnement. """

        def __init__(self, on_validate: Callable, on_close: Callable):
            super(BMCAboWidget.CreateAboWidget, self).__init__()
            self.setWindowTitle("")
            self.load_ui()
            self.connect_signals_to_slots()
            self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
            self.on_validate = on_validate
            self.on_close = on_close
            self.show()

        def closeEvent(self, event: QCloseEvent) -> None:
            self.on_close()

        def keyPressEvent(self, event: QKeyEvent) -> None:
            if event.key() == Qt.Key_Escape:
                self.close()

        def connect_signals_to_slots(self):
            self.validate_button.clicked.connect(self.validate)

        def load_ui(self):
            uic.loadUi('resources/create_abo.ui', self)

        def validate(self):
            if self.abo_3m_button.isChecked():
                abo_type = "3M"
            elif self.abo_10s_button.isChecked():
                abo_type = "C10S"
            else:
                return

            self.on_validate(abo_type, self.reduced_price_button.isChecked(), self.gear_included_button.isChecked())
            self.close()

    def __init__(self, controller):
        super(BMCAboWidget, self).__init__(controller)
        self.search_widget = None
        self.create_abo_widget = None
        self.checkboxes = None
        self.search_client()

    def connect_signals_to_slots(self) -> None:
        self.search_button.clicked.connect(self.search_client)
        self.save_button.clicked.connect(self.save_client)
        self.create_button.clicked.connect(self.create_abo)
        self.delete_button.clicked.connect(self.delete_abonnement)
        self.validate_button.clicked.connect(self.validate_abonnement)
        self.reset_button.clicked.connect(self.reset_client)
        self.abo_end_date_field.editingFinished.connect(self.show_abonnement_end_date_button)
        self.abo_end_date_button.clicked.connect(self.update_abonnement_end_date)

    def build_ui(self) -> None:
        uic.loadUi('resources/abos.ui', self)
        self.set_size_policy()
        self.clear_client_view()
        self.clear_abonnement_view()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.controller.abo_manager.current_client = None
        self.controller.take_control_from_child()

    def set_size_policy(self) -> None:
        for item in [self.abo_end_date_field, self.validate_button, self.create_button,
                     self.entrance_1, self.entrance_2, self.entrance_3, self.entrance_4, self.entrance_5,
                     self.entrance_6, self.entrance_7, self.entrance_8, self.entrance_9, self.entrance_10]:
            size_policy = item.sizePolicy()
            size_policy.setRetainSizeWhenHidden(True)
            item.setSizePolicy(size_policy)

    # Handle the searching of clients
    def search_client(self) -> None:
        self.setEnabled(False)
        self.search_widget = BMCAboWidget.AutosearchWidget(
            self.on_search_change, self.on_search_activate, self.on_search_close)

    def on_search_change(self) -> None:
        search_string = self.search_widget.search_field.text()
        self.controller.search_clients(search_string)

    def on_search_activate(self, selected_index: int) -> None:
        self.controller.select_current_client(selected_index)
        self.on_search_close()

    def on_search_close(self) -> None:
        self.search_widget.close()
        self.setEnabled(True)

    # Handle the creation of a new abonnement
    def create_abo(self) -> None:
        self.setEnabled(False)
        self.create_abo_widget = BMCAboWidget.CreateAboWidget(self.on_creation_validated, self.on_creation_closed)

    def on_creation_validated(self, abo_type: str, reduced_price: bool, include_gear: bool) -> None:
        # Create and save the abonnement
        self.controller.create_abonnement(abo_type, reduced_price, include_gear)

        # Perform callback to also update transactions
        if abo_type == "3M" and not reduced_price:
            transaction_type = "achat 3M normale"
        elif abo_type == "3M" and reduced_price:
            transaction_type = "achat 3M réduit"
        elif abo_type == "C10S" and not reduced_price:
            transaction_type = "achat 10S normale"
        elif abo_type == "C10S" and reduced_price:
            transaction_type = "achat 10S réduit"
        else:
            raise RuntimeError("Unknown abo_type and/or reduced_price")
        if include_gear:
            self.controller.update_transaction("achat abo matériel")
        self.controller.update_transaction(transaction_type)

    def on_creation_closed(self) -> None:
        self.create_abo_widget.close()
        self.setEnabled(True)

    # Handle other things
    def save_client(self) -> None:
        self.controller.save_client()

    def reset_client(self) -> None:
        self.controller.reset_current_client()

    def delete_abonnement(self) -> None:
        self.controller.delete_abonnement()

    def validate_abonnement(self) -> None:
        abo_type = self.get_valid_abonnement_data()[0]
        if abo_type == "3M":
            self.controller.update_transaction("entrée 3M BMC")
        elif abo_type == "C10S":
            clicked_spots = self.get_c10s_spots_data()[1]
            for _ in range(clicked_spots):
                self.controller.update_transaction("entrée C10S BMC")
            self.controller.subtract_entries_from_abonnement(clicked_spots)
        else:
            raise RuntimeError("abo_type should be C10S or 3M")
        self.close()

    def show_abonnement_end_date_button(self) -> None:
        self.abo_end_date_button.show()

    def update_abonnement_end_date(self) -> None:
        self.controller.update_abonnement_end_date()

    # Handle the view
    def clear_client_view(self) -> None:
        self.client_title.setText("Client")
        self.first_name_field.setText(None)
        self.last_name_field.setText(None)
        self.phone_field.setText(None)
        self.email_field.setText(None)
        self.street_name_field.setText(None)
        self.city_name_field.setText(None)
        self.country_field.setText(None)
        self.street_nr_field.setText(None)
        self.city_zip_field.setText(None)
        self.reduced_price_checkbox.setChecked(False)
        self.buttonGroup.setExclusive(False)
        self.male_button.setChecked(False)
        self.female_button.setChecked(False)
        self.buttonGroup.setExclusive(True)
        self.birthdate_field.setDate(datetime.date(year=1900, month=1, day=1))
        self.save_button.setText("Créer")

    def clear_abonnement_view(self) -> None:
        self.create_button.hide()
        self.delete_button.hide()
        self.validate_button.hide()
        self.abo_end_date_button.hide()
        self.abo_end_date_field.hide()
        checkboxes = [self.entrance_1, self.entrance_2, self.entrance_3, self.entrance_4, self.entrance_5,
                      self.entrance_6, self.entrance_7, self.entrance_8, self.entrance_9, self.entrance_10]
        for cb in checkboxes:
            cb.hide()
            cb.setChecked(False)
            cb.setDisabled(False)

        self.abo_type_field.setText("-")
        self.abo_validity_field.setText("-")
        self.abo_gear_field.setText("-")
        self.abo_history_browser.setText("")

    # Handle the data
    def get_c10s_spots_data(self) -> Tuple[int, int, int]:
        checkboxes = [self.entrance_1, self.entrance_2, self.entrance_3, self.entrance_4, self.entrance_5,
                      self.entrance_6, self.entrance_7, self.entrance_8, self.entrance_9, self.entrance_10]
        free_spots, clicked_spots, taken_spots = 0, 0, 0
        for cb in checkboxes:
            if cb.isEnabled():
                if cb.isChecked():
                    clicked_spots += 1
                else:
                    free_spots += 1
            else:
                taken_spots += 1
        assert free_spots + clicked_spots + taken_spots == 10
        return free_spots, clicked_spots, taken_spots

    def get_client_data(self):
        first_name = self.first_name_field.text() if self.first_name_field.text() != "" else None
        last_name = self.last_name_field.text() if self.last_name_field.text() != "" else None
        phone = self.phone_field.text() if self.phone_field.text() != "" else None
        email = self.email_field.text() if self.email_field.text() != "" else None
        street_name = self.street_name_field.text() if self.street_name_field.text() != "" else None
        city_name = self.city_name_field.text() if self.city_name_field.text() != "" else None
        country = self.country_field.text() if self.country_field.text() != "" else None
        dob_str = self.birthdate_field.date().toString("yyyy-MM-dd")
        date_of_birth = None if dob_str == "01/01/1900" else datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()
        street_number = int(self.street_nr_field.text()) if self.street_nr_field.text() != "" else None
        city_zip = int(self.city_zip_field.text()) if self.city_zip_field.text() != "" else None
        reduced_price = self.reduced_price_checkbox.isChecked()
        sex = "M" if self.male_button.isChecked() else ("F" if self.female_button.isChecked() else None)

        return first_name, last_name, reduced_price, email, phone, date_of_birth, sex, street_name, street_number, \
            city_zip, city_name, country

    def get_valid_abonnement_data(self):
        # Abo type
        if self.abo_type_field.text() == "3M":
            abo_type = "3M"
        elif self.abo_type_field.text() == "C10S":
            abo_type = "C10S"
        else:
            abo_type = None

        # Gear included
        include_gear = True if self.abo_gear_field.text() == "Oui" else False

        # Buy date
        try:
            date_str = self.abo_validity_field.text().split(" ")[0]
            buy_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
        except Exception as e:
            print(e)
            buy_date = None

        # End date
        try:
            date_str = self.abo_end_date_field.date().toString("yyyy-MM-dd")
            end_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            print(e)
            end_date = None

        # Remaining entrances
        if abo_type == "C10S":
            checkboxes = [self.entrance_1, self.entrance_2, self.entrance_3, self.entrance_4, self.entrance_5,
                          self.entrance_6, self.entrance_7, self.entrance_8, self.entrance_9, self.entrance_10]
            entrances_remaining = [cb.isChecked() for cb in checkboxes].count(False)
        else:
            entrances_remaining = None

        # Reduced price
        reduced_price = self.reduced_price_checkbox.isChecked()

        return abo_type, include_gear, reduced_price, buy_date, end_date, entrances_remaining
