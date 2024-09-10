import datetime
import sqlite3
import sys
from pathlib import Path

import yaml
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QStatusBar, QMainWindow, QPushButton

from abonnements import BMCAboManager
from exception import UnhandeledExceptionObserver
from popups import ask_to_recover_from_backup_popup, ask_to_confirm_quit_popup, simple_dialog, \
    ask_to_confirm_abo_delete, confirm_abo_creation_sponsor_popup, confirm_reduction_popup
from products import BMCProductsManager
from session import BMCSessionManager
from widgets import BMCMainWidget, BMCLoginWidget, BMCHistoryWidget, BMCCustomOperationWidget, \
    BMCAboWidget

# Name and version the app
APP_NAME, APP_VERSION = "Caisse BMC", "2.2"

# Make sure to be able to report all unhandled exceptions before crashing
qt_exception_hook = UnhandeledExceptionObserver()


def main():
    """ Start the main window and event loop. """
    app = QApplication([])
    controller = BMCMainController()
    view = BMCMainWindow(controller=controller)
    controller.initialize_view(view)
    controller.launch_login_view()
    sys.exit(app.exec_())


class BMCMainController:
    """ This class implements the main controller of the application. The user uses the controller which interacts with
     the data classes, and then updates the views which are mostly implemented as widgets. """

    def __init__(self):
        """ Initialize the controller.

        config: a dict with the 'configuration' variables such as prices, allowed users, paths, ...
        session_manager: an instance of the class which manages a session which mostly boils down to managing all
            the current session's monetary transactions.
        abo_manager: an instance of the class that manages clients and abonnements. This class mostly wraps around
            the client, and abonnement classes, as well as the interface which connects to the database.
        main_widget: The main view. Must be a QMainWindow.
        child_widget: A placeholder which can be used to spawn child widgets to delegate specific taskt such as
            asking for login information, showing a history log, ...

        """
        # Initialize data
        self.config = self.get_config()
        self.products_manager = BMCProductsManager
        self.update_config_with_products()
        self.session_manager = BMCSessionManager(self.config)
        self.abo_manager = BMCAboManager(self.config["abo db path"])

        # Initialize views
        self.main_widget = None
        self.child_widget = None

    def initialize_view(self, view: QMainWindow) -> None:
        """ Set the main view. """
        self.main_widget = view

    @staticmethod
    def get_config() -> dict:
        """ Get the config dict from imported constants. """
        # Import static constants from config
        with open('resources/config.yaml', 'rt', encoding='utf8') as file:
            parsed_config = yaml.safe_load(file)

        config = dict()
        config["supervisors"] = parsed_config["PREMANENTS"]
        config["prices of entries"] = parsed_config["PRIX_ENTREES"]
        config["prices of rentals"] = parsed_config["PRIX_LOCATIONS"]
        config["logs root dir"] = parsed_config["DOSSIER_COMPTABILITE"]
        config["abo db path"] = parsed_config["DATABASE"]
        config["products db path"] = parsed_config["DATABASE"]
        config["reduction factor"] = parsed_config["REDUCTION_PERMANENTS"]

        config_file_path = Path(__file__).parent.joinpath("resources", "config.yaml")
        if not Path(config["logs root dir"]).is_dir():
            raise IOError("logs root dir: {} not found. Try editing the config file located at {}".format(
                config["logs root dir"], config_file_path))
        if not Path(config["abo db path"]).is_file():
            raise IOError("abo db path: {} not found Try editing the config file located at {}".format(
                config["abo db path"], config_file_path))
        if not Path(config["products db path"]).is_file():
            raise IOError("products db path: {} not found Try editing the config file located at {}".format(
                config["products db path"], config_file_path))

        return config

    def update_config_with_products(self):
        """ Products are dynamically loaded from database at application start. The products manager must be
        initialised first so this function updates the existing config with sale products. """
        self.products_manager.fetch_products(self.config["products db path"])
        self.config["prices of sales"] = {}
        for product in self.products_manager.products:
            self.config["prices of sales"]["achat " + product.name] = product.price

    # Methods to delegate views
    def give_control_to_child(self) -> None:
        """ Child widgets can be spawned. This method gives control to the child widget. """
        self.main_widget.setEnabled(False)

    def take_control_from_child(self) -> None:
        """ This method takes control back to the main view when child widgets are deleted. """
        self.main_widget.setEnabled(True)
        self.update_main_view()

    def launch_login_view(self) -> None:
        """ Before launching and enabeling the main view some initial information is requested. Not a 'true' login, more
        an initialization."""
        self.child_widget = BMCLoginWidget(self)

    def launch_abo_view(self) -> None:
        """ Launches the separate and complex abo view which is responsible for handeling client data as well as
        abonnements data. """
        self.child_widget = BMCAboWidget(self)

    def launch_history_view(self) -> None:
        """ Shows an overview of this session's transaction as well as a resume with the most important information. """
        transactions_str = self.session_manager.get_transactions_str()
        summary_str = self.session_manager.get_session_summary_str()
        self.child_widget = BMCHistoryWidget(self, transactions_str, summary_str)

    def launch_custom_ops_view(self) -> None:
        """ Allows to create a transaction which does not fit the 'standard' transaction format in terms of description
        and pricing. Also allows subtracting money from the register. """
        self.child_widget = BMCCustomOperationWidget(self)

    def launch_quit_view(self) -> None:
        """ Asks to confirm the intention to quit the app, and closes everything down cleanly if confirmed. """
        if ask_to_confirm_quit_popup(self.session_manager.cash_count):
            self.session_manager.save_to_file()
            self.session_manager.remove_backup_file()
            self.main_widget.close()

    # All things related to a session
    # Methods to interact with the session manager
    def validate_login(self, date: QDate, cash_count: float, supervisor: str) -> None:
        """ Validate the login data. First sets all data to the session manager, and then checks if a previous session
        backup exists, which should exist after an app crash. """
        self.session_manager.initialize_paths(date)
        self.session_manager.date = date
        self.session_manager.initialize_cash_count(cash_count)
        self.session_manager.supervisor = supervisor

        # Check if a previous backup file_path resulting from a prior crash is present and if so give option to restore
        if self.session_manager.backup_file_exist() is True:
            backup = BMCSessionManager.from_backup(self.session_manager.backup_path)
            recover = ask_to_recover_from_backup_popup(backup, date, cash_count)
            if recover:
                self.session_manager = backup
            self.session_manager.save_to_backup()

    def update_product(self, button: QPushButton):
        """ Updates the current transaction with a product sale. """
        self.products_manager.adjust_local_stocks(button.objectName())
        product = self.products_manager.get_with_name(button.objectName())
        button.setText(product.description)
        if product.stock <= 0:
            button.setEnabled(False)
        self.update_transaction("achat " + button.objectName())

    def cancel_update_product(self, buttons: list):
        """ Cancels an update to the products stock. """
        for button in buttons:
            product = self.products_manager.get_with_name(button.objectName())
            if product.changed_stock:
                product.restore()
                button.setText(product.description)
                if product.stock > 0:
                    button.setEnabled(True)

    def update_transaction(self, transaction_type: str) -> None:
        """ Creates a new transaction, or updates the current transaction in the session manager in the case of
        'normal' operations, or delegates to the abo and clients views and managers to handle abonnements. """
        if transaction_type == "abonnement BMC":
            self.launch_abo_view()
        else:
            self.session_manager.update_current_transaction(transaction_type)
        self.update_main_view()

    def apply_reduction(self, reduction: float) -> None:
        """ Applies a one time reduction on the total of the current transaction in the session manager. """
        if confirm_reduction_popup(reduction):
            self.session_manager.apply_reduction_on_current_transaction(reduction)
            self.update_main_view()

    def validate_transaction(self, modality: str) -> None:
        """ Validates the current transaction in the session manager. """
        self.session_manager.validate_current_transaction(modality)
        self.products_manager.update_db(self.config["products db path"])
        self.products_manager.confirm_stock()
        self.update_main_view()

    def custom_transaction(self, description: str, amount: float, modality: str) -> None:
        """ Creates and immediately validates a custom transaction which can have any description, and value (also
        negative values allowed). """
        self.session_manager.add_custom_transaction(description, amount, modality)
        self.update_main_view()

    def cancel_transaction(self, buttons) -> None:
        """ Cancels the current transaction. """
        self.cancel_update_product(buttons)
        self.session_manager.cancel_current_transaction()
        self.update_main_view()

    # Methods to update the main view
    def update_main_view(self) -> None:
        """ Delegate to separate methods for separate parts of the view. """
        self.update_statusbar_view()
        self.update_details_view()
        self.update_recap_view()

    def update_statusbar_view(self) -> None:
        """ Updates the status bar. """
        msg = "{}         |         {}         |         En caisse: €{}         Rentrées: €{}         # clients: {}" \
            .format(self.session_manager.date.toString("dd/MM/yyyy"),
                    self.session_manager.supervisor,
                    self.session_manager.cash_count,
                    self.session_manager.cash_earnings + self.session_manager.card_earnings,
                    self.session_manager.client_count)
        self.main_widget.statusBar.showMessage(msg)

    def update_details_view(self) -> None:
        """ Updates the details view which has a complete breakdown of what's included in the current transaction. """
        self.main_widget.centralWidget().details_textbrowser.setText(self.session_manager.get_details_str())

    def update_recap_view(self) -> None:
        """ Updates the recap view which shows the value value of the current trancation, or other short messages.  """
        self.main_widget.centralWidget().recap_textbrowser.setText(self.session_manager.get_recap_str())

    # All things related to clients and abonnements
    # Methods to interact with the abo manager
    def search_clients(self, name_part: str) -> None:
        """ This asks the abo manager to perform a search in the database and to filter all clients whose name
        partially match the provided name part. The list of matching clients is stored in the manager. """
        self.abo_manager.search_clients(name_part)
        self.update_autocompleter_view(name_part)

    def select_current_client(self, selected_index: int) -> None:
        """ Sets the current client in the abo manager based on the index of the current client in the matching
        clients' list. """
        self.abo_manager.current_client = self.abo_manager.matching_clients[selected_index]
        self.update_client_and_abonnements_view()

    def reset_current_client(self) -> None:
        """ Resets the current client. """
        self.abo_manager.current_client = None
        self.update_client_and_abonnements_view()

    def save_client(self) -> None:
        """ Checks whether there is a currently set client. If so it attempts to update it with the current data, if
        not it attempts to create a new client. In any case a message is displayed to confirm the action. """
        # Check that reading the data does not raise an exception
        try:
            _, _, _, _, _, date_of_birth, _, _, _, _, _, _ = self.child_widget.get_client_data()
            if date_of_birth >= datetime.date.today():
                raise ValueError()
        except ValueError:
            msg = "Il y a une ou des erreur dans les données. Veuillez verifier que tout les champs contiennent des " \
                  "valeurs valables (ex. chiffres plutot que letters etc., date de naissance réaliste, ...)."
            simple_dialog("Warning", "Erreur", msg)
            return

        # Try to create or update a client
        try:
            if self.abo_manager.current_client is None:
                self.abo_manager.create_new_client(*self.child_widget.get_client_data())
            else:
                self.abo_manager.update_current_client(*self.child_widget.get_client_data())
            new_first_name = self.abo_manager.current_client.first_name
            new_last_name = self.abo_manager.current_client.last_name
            msg = "Le client {} {} a été enregistré dans la base de données.".format(new_first_name, new_last_name)
            simple_dialog("Information", "Réussi", msg)
            self.update_client_and_abonnements_view()
        except (ValueError, sqlite3.Error):
            msg = "Une erreur est survenue lors de la sauvegarde du client. Assurez-vous que le nom et prénom ne " \
                  "soient pas vides et que le client n'éxiste pas déjà dans la base de données."
            simple_dialog("Warning", "Erreur", msg)
            self.abo_manager.current_client = None
            return

    def create_abonnement(self, abo_type: str, reduced_price: bool, include_gear: bool) -> None:
        """ Asks the abo manager to create a new abonnement with the provided data and pops up a reminder to make
        a Lecomte fidelity card. """
        self.abo_manager.create_new_abonnement(abo_type, reduced_price, include_gear)
        first_name, last_name = self.abo_manager.current_client.first_name, self.abo_manager.current_client.last_name
        confirm_abo_creation_sponsor_popup(first_name + " " + last_name)
        self.update_client_and_abonnements_view()

    def update_abonnement_end_date(self) -> None:
        """ Asks the abo manager to update the current abonnement's end date. """
        _, _, _, _, new_end_date, _ = self.child_widget.get_valid_abonnement_data()
        self.abo_manager.update_valid_abonnement_end_date(new_end_date)
        msg = "La date de fin de l'abonnement a été mis à jour. L'abonnement est maintenant valable jusqu'au {}" \
            .format(self.abo_manager.valid_client_abonnement.end_date.strftime("%d/%m/%Y"))
        simple_dialog(severity="Information", title="Abonnement mis à jour", text=msg)
        self.update_client_and_abonnements_view()

    def subtract_entries_from_abonnement(self, num_entries: int) -> None:
        """ Subtracts a given number of entries from a 10 entrances card. """
        self.abo_manager.update_valid_abonnement_entrances(num_entries)
        self.update_client_and_abonnements_view()

    def delete_abonnement(self) -> None:
        """ Pops up a confirmation dialog and proceeds to delete the current abonnement if the user is certain that
        that is what he wants to do. """
        if ask_to_confirm_abo_delete(insist=False):
            if ask_to_confirm_abo_delete(insist=True):
                self.abo_manager.delete_valid_abonnement()
        self.update_client_and_abonnements_view()

    # Methods to update the clients and abos views
    def update_autocompleter_view(self, name_part: str) -> None:
        """ Updates the autocompleter's view by setting the dropdown's options. """
        name_part = name_part.lower()
        vals = []
        for client in self.abo_manager.matching_clients:
            fl_name = client.first_name + ", " + client.last_name
            lf_name = client.last_name + ", " + client.first_name

            if fl_name.lower().find(name_part) == 0:
                vals.append(fl_name)
            elif lf_name.lower().find(name_part) == 0:
                vals.append(lf_name)
            else:
                raise RuntimeError("The filtered clients' list contains invalid entries")

        self.child_widget.search_widget.set_completer_options(vals)

    def update_client_and_abonnements_view(self) -> None:
        """ Triggers an update on the whole widget by dispatching to specific methods related to some parts of view. """
        self.child_widget.clear_abonnement_view()
        self.child_widget.clear_client_view()
        self.update_client_view()
        self.update_abonnements_current_view()
        self.update_abonnements_history_view()

    def update_client_view(self) -> None:
        """ Checks if the manager has a currently active client and if so sets all fields etc. in the view which are
        related to client data. """
        if self.abo_manager.current_client is not None:
            # Set simple string fields (None is handeled automatically)
            self.child_widget.client_title.setText("Client {}".format(self.abo_manager.current_client.db_id))
            self.child_widget.first_name_field.setText(self.abo_manager.current_client.first_name)
            self.child_widget.last_name_field.setText(self.abo_manager.current_client.last_name)
            self.child_widget.phone_field.setText(self.abo_manager.current_client.phone)
            self.child_widget.email_field.setText(self.abo_manager.current_client.email)
            self.child_widget.street_name_field.setText(self.abo_manager.current_client.street_name)
            self.child_widget.city_name_field.setText(self.abo_manager.current_client.city_name)
            self.child_widget.country_field.setText(self.abo_manager.current_client.country)

            # Set integer fields where None needs to be handeled separately
            if self.abo_manager.current_client.street_number is not None:
                self.child_widget.street_nr_field.setText(str(self.abo_manager.current_client.street_number))
            if self.abo_manager.current_client.city_zip is not None:
                self.child_widget.city_zip_field.setText(str(self.abo_manager.current_client.city_zip))

            # Set boxes
            self.child_widget.reduced_price_checkbox.setChecked(self.abo_manager.current_client.reduced_price)
            if self.abo_manager.current_client.sex == "M":
                self.child_widget.male_button.setChecked(True)
            elif self.abo_manager.current_client.sex == "F":
                self.child_widget.female_button.setChecked(True)
            else:
                self.child_widget.buttonGroup.setExclusive(False)
                self.child_widget.male_button.setChecked(False)
                self.child_widget.female_button.setChecked(False)
                self.child_widget.buttonGroup.setExclusive(True)

            # Set date of birth
            if self.abo_manager.current_client.date_of_birth:
                self.child_widget.birthdate_field.setDate(self.abo_manager.current_client.date_of_birth)
            else:
                self.child_widget.birthdate_field.setDate(datetime.date(year=1900, month=1, day=1))
            self.child_widget.save_button.setText("Update")

    def update_abonnements_current_view(self) -> None:
        """ Checks if the manager has a currently active abonnement and if so sets all fields etc. in the view which
        are related to abo data. """
        if self.abo_manager.valid_client_abonnement is not None:
            valid_abo = self.abo_manager.valid_client_abonnement
            self.child_widget.abo_type_field.setText(valid_abo.abo_type)
            self.child_widget.abo_gear_field.setText("Oui" if valid_abo.include_gear else "Non")
            if valid_abo.abo_type == "C10S":
                self.child_widget.abo_validity_field.setText(valid_abo.buy_date.strftime("%d/%m/%Y"))
            elif valid_abo.end_date is not None:
                self.child_widget.abo_validity_field.setText(valid_abo.buy_date.strftime("%d/%m/%Y") +
                                                             "       →      Date de fin:")
                self.child_widget.abo_end_date_field.setDate(self.abo_manager.valid_client_abonnement.end_date)
                self.child_widget.abo_end_date_field.show()
            self.child_widget.validate_button.show()
            self.child_widget.delete_button.show()
            if valid_abo.abo_type == "C10S":
                checkboxes = [self.child_widget.entrance_1, self.child_widget.entrance_2, self.child_widget.entrance_3,
                              self.child_widget.entrance_4, self.child_widget.entrance_5, self.child_widget.entrance_6,
                              self.child_widget.entrance_7, self.child_widget.entrance_8, self.child_widget.entrance_9,
                              self.child_widget.entrance_10]
                for i, cb in enumerate(checkboxes):
                    cb.show()
                    if i < 10 - valid_abo.entrances_remaining:
                        cb.setChecked(True)
                        cb.setDisabled(True)
        else:
            if self.abo_manager.current_client is not None:
                self.child_widget.create_button.show()
            else:
                self.child_widget.clear_abonnement_view()

    def update_abonnements_history_view(self) -> None:
        """ Checks if the manager has (had) any abonnement and shows a small overview of all (previous) abonnements.
        This allows to inform clients of their previous abo when one were to expire. """
        if self.abo_manager.current_client_abonnements is not None:
            abonnements = self.abo_manager.current_client_abonnements
            abonnements.sort(key=lambda x: x.buy_date, reverse=True)
            history = ""
            for abo in abonnements:
                history += str(abo)
                history += "\n"
            self.child_widget.abo_history_browser.setText(history)


class BMCMainWindow(QMainWindow):
    """ This class implements the main view (window) of the application. The controller gets orders from the view,
    interacts with the data, and updates the view. QT needs a main window, which can embed a (main) widget. """

    def __init__(self, controller):
        """ Initialize the main window, and link it to the controller. The main window consists of a main widget,
        a title bar, and a status bar. """
        super(BMCMainWindow, self).__init__()
        self.controller = controller
        self.setCentralWidget(BMCMainWidget(self.controller))
        self.setWindowTitle("{} V{}".format(APP_NAME, APP_VERSION))
        self.statusBar = QStatusBar()
        self.statusBar.showMessage("Caisse BMC")
        self.setStatusBar(self.statusBar)
        self.show()
        x = int((QApplication.desktop().screen().rect().center() - self.centralWidget().rect().center()).x())
        self.move(x, 0)

    def closeEvent(self, event) -> None:
        """ The closeEvent function is extended to be able to handle (well ignore actually) closing events originating
        from outside the application, such as cmd + q, or clicking the 'x' window button. """
        if event.spontaneous():
            event.ignore()


if __name__ == "__main__":
    main()

# TODO
#  check where data is being checked, validated, and processed
#  read ID cards
#  the whole config shit doesn't make sense to be copied and included in every single transaction instance...
#  use properties in bmcclient and bmcabonnement
#  check input and set
