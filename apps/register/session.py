from __future__ import annotations

import os
import pickle
import time
from pathlib import Path
from typing import List
from typing import Tuple

from PyQt5.QtCore import QDate

from utils import get_most_recent_report_path, get_path_to_new_report_file, get_weekday_from_date, \
    get_expected_cash_from_report, write_report_file


class BMCSessionManager:
    """ The BMCSessionManager is responsible for managing one registry 'session'. It does things like managing and
    keeping track of transactions, keeping track of the registry's cash, keeping track of earnings, registering who's
    responsible for a given session, and making nice financial report files at the end of a session. """

    def __init__(self, config: dict = None):
        """ Constructor which initializes a session manager. Sets meaningless values for most fields, except for the
         expected cash count, which can be read from previous financial report files. As some fields are kinda
         required before properly starting a session, a separate, external login function can be ran. """
        self.config = config if config is not None else None
        self.supervisor = "None"
        self.date = QDate()
        self.expected_initial_cash_count, self.last_report_date = self.read_expected_cash_count_and_date_from_file()
        self.observed_initial_cash_count = 0.

        self._older_transactions = list()
        self._current_transaction = None

        self.recap = ""
        self.details = ""

        self.save_path, self.backup_path = None, None

    # Alternative constructor
    @classmethod
    def from_backup(cls, file_path: Path) -> BMCSessionManager:
        """ Alternative constructor which makes it possible to retrieve a session manager object from a pickeled
        backup file. """
        with (open(str(file_path), "rb")) as openfile:
            obj = pickle.load(openfile)

        return obj

    # Getters
    @property
    def supervisor(self) -> str:
        return self.__supervisor

    @supervisor.setter
    def supervisor(self, supervisor: str):
        if not isinstance(supervisor, str):
            raise TypeError("supervisor must be a string instance")
        if supervisor not in self.config["supervisors"] and supervisor != "None":
            raise ValueError("supervisor must be one of {}".format(self.config["supervisors"]))
        self.__supervisor = supervisor

    @property
    def date(self) -> QDate:
        return self.__date

    @date.setter
    def date(self, date: QDate):
        if not isinstance(date, QDate):
            raise TypeError("date must be a QDate isntance")
        self.__date = date

    @property
    def expected_initial_cash_count(self) -> float:
        return round(self.__expected_initial_cash_count, 2)

    @expected_initial_cash_count.setter
    def expected_initial_cash_count(self, expected_initial_cash_count: float):
        if not isinstance(expected_initial_cash_count, float):
            raise TypeError("expected_initial_cash_count must be a float instance")
        self.__expected_initial_cash_count = expected_initial_cash_count

    @property
    def observed_initial_cash_count(self) -> float:
        return round(self.__observed_initial_cash_count, 2)

    @observed_initial_cash_count.setter
    def observed_initial_cash_count(self, observed_initial_cash_count: float):
        if not isinstance(observed_initial_cash_count, float):
            raise TypeError("observed_initial_cash_count must be a float instance")
        self.__observed_initial_cash_count = observed_initial_cash_count

    @property
    def initial_cash_count_error(self) -> float:
        return round(self.observed_initial_cash_count - self.expected_initial_cash_count, 2)

    @property
    def cash_count(self) -> float:
        cash_count = self.observed_initial_cash_count
        for t in self._older_transactions:
            if t.modality == "cash":
                cash_count += t.value
        return round(cash_count, 2)

    @property
    def cash_earnings(self) -> float:
        return round(self.cash_count - self.observed_initial_cash_count, 2)

    @property
    def card_earnings(self) -> float:
        card_count = 0.0
        for t in self._older_transactions:
            if t.modality == "card":
                card_count += t.value
        return round(card_count, 2)

    @property
    def total_earnings(self) -> float:
        return round(self.cash_earnings + self.card_earnings, 2)

    @property
    def client_count(self) -> int:
        client_count = 0
        for t in self._older_transactions:
            client_count += t.client_count
        return client_count

    # Methods to initialize the manager
    def initialize_cash_count(self, initial_cash_count: float) -> None:
        """ Sets the initially observed cash count, which requires to manually check and count the cash. """
        self.observed_initial_cash_count = initial_cash_count
        self.set_recap_str(msg_type="initial", last_report_date=self.last_report_date,
                           expected_cash_count=self.expected_initial_cash_count,
                           observed_cash_count=self.observed_initial_cash_count)

    def initialize_paths(self, date: QDate) -> None:
        """ Sets up the folders and files where to save this session's state and final reports. """
        self.save_path = Path(get_path_to_new_report_file(self.config["logs root dir"], date))
        if self.save_path.is_file():
            renamed_extension = "-version-{}.csv".format(time.strftime("%Hh%Mm%Ss", time.localtime()))
            self.save_path.rename(str(self.save_path).replace(".csv", renamed_extension))
        self.backup_path = self.save_path.with_suffix(".bcp")

    # Methods that represent the session's state in one or another string form
    def __str__(self) -> str:
        """ Returns a sting representation of the internal state. """
        msg = str()
        msg += "Jour : {}\n".format(get_weekday_from_date(self.date))
        msg += "Date : {}\n".format(self.date.toString("dd/MM/yyyy"))
        msg += "Permanent : {}\n".format(self.supervisor)
        msg += "\n"
        msg += "Caisse début : €{}\n".format(self.observed_initial_cash_count)
        msg += "Erreur caisse : €{}\n".format(self.initial_cash_count_error)
        msg += "\n\n"
        msg += "Transactions\n"
        msg += "{}".format(str(BMCTransaction.from_transactions_list(self.config, self._older_transactions)))
        msg += "\n\n"
        msg += "Total rentrées : €{}".format(self.total_earnings)
        msg += "\n     - cash : €{}".format(self.cash_earnings)
        msg += "\n     - cartes : €{}".format(self.card_earnings)
        msg += "\n\n"
        msg += "Caisse fin : €{}".format(self.cash_count)

        return msg

    def get_recap_str(self) -> str:
        """ Short messages about the last or current operations or transactions being performed. """
        return self.recap

    def get_details_str(self) -> str:
        """ Get the detailled contents of the current transaction. """
        return self.details

    def get_session_summary_str(self) -> str:
        """ Summarize all of this session's parameters. """
        return str(self)

    def get_transactions_str(self) -> str:
        """ Get the list of all of this session's transactions. """
        if len(self._older_transactions) == 0:
            return "Aucune transaction enregistrée pour cette session."
        msg = str()
        for trans_nr, transaction in enumerate(self._older_transactions):
            msg += "-------- Transaction nr. {} --------\n".format(trans_nr)
            msg += str(transaction)
            msg += "Modalité: {}\n".format("carte" if transaction.modality == "card" else "cash")
            msg += "Total: €{}\n".format(transaction.value)
            msg += "\n"

        return msg

    def set_recap_str(self, msg_type: str, **kwargs) -> None:
        """ Constructs a recap string according to some predefined formats. """
        if msg_type == "initial":
            last_report_date = kwargs["last_report_date"]
            observed_cash_count = kwargs["observed_cash_count"]
            expected_cash_count = kwargs["expected_cash_count"]
            diff = observed_cash_count - expected_cash_count
            self.recap = "En caisse le {}:\t{}\n" \
                         "En caisse aujourd'hui:\t{}\n\n" \
                         "Difference caisse:\t{}".format(last_report_date.toString("dd/MM/yyyy"), expected_cash_count,
                                                         observed_cash_count, diff)

        elif msg_type == "current value":
            self.recap = "Total: €{}".format(round(self._current_transaction.value, 2))

        elif msg_type == "cancel":
            self.recap = "Vente annulée"

        elif msg_type == "validate" and kwargs["modality"] == "cash":
            self.recap = "Vente de €{} enregistrée en cash".format(kwargs["transaction_value"])

        elif msg_type == "validate" and kwargs["modality"] == "card":
            self.recap = "Vente de €{} enregistrée par carte".format(kwargs["transaction_value"])

        elif msg_type == "operation":
            self.recap = "Operation caisse de €{} effectuée".format(kwargs["transaction_value"])

        elif msg_type == "clear":
            self.recap = ""

        else:
            raise ValueError("unexpected value encountered for recap message type")

    def set_details_str(self, msg_type: str) -> None:
        """ Constructs an overview string of the current transaction according to some predefined formats. """
        if msg_type == "current transaction":
            self.details = str(self._current_transaction)

        elif msg_type == "clear":
            self.details = ""

        elif msg_type == "recover":
            self.details = "Les données suivantes ont été récuperées:\n" \
                           "Transactions:\n" \
                           "{}" \
                           "\n" \
                           "Rentrées cash:\t€{}\n" \
                           "Rentrées cartes:\t€{}\n" \
                           "# clients:\t\t{}".format(str(self._older_transactions[0]), self.cash_earnings,
                                                     self.card_earnings, self.client_count)
        else:
            raise ValueError("unexpected value encountered for recap message type")

    # Methods that handle transactional data
    def update_current_transaction(self, transaction_type: str) -> None:
        """ Creates a new transaction if there currently is no transaction being processed, or updates the current
        transaction with a predefined transaction type which must match one of the transaction types in the
        configuration. """
        if self._current_transaction is None:
            self._current_transaction = BMCTransaction(self.config)
        self._current_transaction.update(transaction_type)
        self.set_recap_str(msg_type="current value")
        self.set_details_str(msg_type="current transaction")

    def apply_reduction_on_current_transaction(self, reduction: float) -> None:
        """ If there is a current transaction and if a reduction has not yet been applied to this transaction, then
        a reduction will be applied. """
        if self._current_transaction is not None and self._current_transaction.reduction_applied is False:
            self._current_transaction.value = round(self._current_transaction.value * reduction * 10) / 10
            self._current_transaction.reduction_applied = True
            self.set_recap_str(msg_type="current value")
            self.set_details_str(msg_type="current transaction")

    def validate_current_transaction(self, modality: str) -> None:
        """ Validates the current transaction which amounts to checking the payment modality, and writing off the
        transaction to the list of previous transactions. Also makes a backup of the manager's internal state so that
        in the case of a crash the manager can recover its previous state. """
        if self._current_transaction is not None:
            self._current_transaction.modality = modality
            assert self._current_transaction.modality == "cash" or self._current_transaction.modality == "card"
            assert isinstance(self._current_transaction.client_count, int)
            assert self._current_transaction.client_count >= 0
            assert isinstance(self._current_transaction.value, float)
            self._older_transactions.append(self._current_transaction)
            self.set_recap_str(msg_type="validate", modality=modality,
                               transaction_value=self._current_transaction.value)
            self.set_details_str(msg_type="clear")
            self._current_transaction = None
            self.save_to_backup()

    def add_custom_transaction(self, msg: str, value: float, modality: str, client_count: int = 0) -> None:
        """ Creates and immediately validates a custom transaction: a transaction which does not adhere to the
        predefined formats in the config, and which can also be negative. """
        custom_transaction = BMCTransaction.from_manual_params(
            self.config, str(msg).lower() + " (op. caisse {})".format(len(self._older_transactions)),
            value,
            client_count,
            modality)
        assert custom_transaction.modality == "cash" or custom_transaction.modality == "card"
        assert isinstance(custom_transaction.client_count, int)
        assert custom_transaction.client_count >= 0
        assert isinstance(custom_transaction.value, float)
        self._older_transactions.append(custom_transaction)
        self.set_recap_str(msg_type="operation", transaction_value=value)
        self.set_details_str(msg_type="clear")
        self._current_transaction = None
        self.save_to_backup()

    def cancel_current_transaction(self) -> None:
        """ Obviously cancels the current transaction. """
        self._current_transaction = None
        self.set_recap_str(msg_type="cancel")
        self.set_details_str(msg_type="clear")

    # Methods that handle IO stuff
    def read_expected_cash_count_and_date_from_file(self) -> Tuple[float, QDate or None]:
        """ Looks in the reports folder for the most recently created financial report file and reads the cash count
        to be expected from that file. As all chartal transactions with the registry should be logged this should
        return the actual cash count in the register. """
        root_dir = self.config["logs root dir"]
        most_recent_report = get_most_recent_report_path(root_dir)
        ps = Path(most_recent_report).stem.split("-")
        most_recent_report_date = QDate()
        most_recent_report_date.setDate(int(ps[0]), int(ps[1]), int(ps[2]))
        expected_cash_count = get_expected_cash_from_report(most_recent_report)

        return expected_cash_count, most_recent_report_date

    def backup_file_exist(self) -> bool:
        """ Simply checks if there is already a backupfile for this session. """
        return Path(self.backup_path).is_file()

    def save_to_backup(self) -> None:
        """ Backs up the session manager's internal state and nothing else to a pickle file, which makes it possible to
        recover the manager's internal state after a crash."""
        backup_file = open(str(self.backup_path), "wb")
        pickle.dump(self, backup_file, protocol=pickle.HIGHEST_PROTOCOL)
        backup_file.close()
        os.chmod(str(self.backup_path), 0o777)

    def remove_backup_file(self) -> None:
        """ Deletes older backups of this session to avoid cluttering the file system. """
        if self.backup_path.is_file():
            self.backup_path.unlink()

    def save_to_file(self) -> None:
        """ Saves (what should be the final state of) the session manager's important data in a nice csv file, which
        is nicely classified and dated. """
        transactions = BMCTransaction.from_transactions_list(self.config, self._older_transactions)
        session_dict = {
            "Jour": get_weekday_from_date(self.date),
            "Date": self.date.toString("dd/MM/yyyy"),
            "Permanent": self.supervisor,
            "Caisse début": self.observed_initial_cash_count,
            "Erreur caisse": self.expected_initial_cash_count - self.observed_initial_cash_count,
            "Total cash": self.cash_earnings,
            "Total cartes": self.card_earnings,
            "Total rentrées": self.total_earnings,
            "# de clients": self.client_count,
            "Caisse fin": self.cash_count,
        }
        write_report_file(transactions, session_dict, self.save_path)


class BMCTransaction:
    """ The BMCTransaction class generates objects which represent a single transaction. It is used to hold and
    prganise transactional data. It is also possible to merge a list of transactions in one big transaction, although
    some information gets lost such as the different modalities of payment employed for each of the constituent
    transactions. """

    def __init__(self, config: dict = None):
        """ Initialize a transaction. By default a transaction is empty, and must be filled by calling its update
        method with a transaction type which matches the transaction types defined in the config dict. """
        self.config = config
        self.value = 0.
        self.client_count = 0
        self.sales_dict = dict()
        self.modality = None
        self.reduction_applied = False

        if config is not None:
            self.prices = dict()
            self.prices.update(self.config["prices of entries"])
            self.prices.update(self.config["prices of rentals"])
            self.prices.update(self.config["prices of sales"])

            for key in self.prices:
                self.sales_dict[key] = [0, self.prices[key]]

    # Alternative constructors
    @classmethod
    def from_transactions_list(cls, config: dict, transactions_list: List) -> BMCTransaction:
        """ Merge a list of transactions into one single transaction. """
        merged_transaction = BMCTransaction(config=config)
        for t in transactions_list:
            merged_transaction = merged_transaction + t

        return merged_transaction

    @classmethod
    def from_manual_params(cls, config: dict, msg: str, value: float, client_count: int,
                           modality: str) -> BMCTransaction:
        """ Create a transaction manually which does not adhere to a predefined format (description and value). """
        manual_transaction = BMCTransaction(config=config)
        manual_transaction.value = value
        manual_transaction.client_count = client_count
        manual_transaction.modality = modality
        manual_transaction.sales_dict[msg] = [1, value]

        return manual_transaction

    def update(self, transaction_type: str) -> None:
        """ Update a transaction by adding a predefined type of transactions to it. The allowed transaction typed
        are defined in the config dict. """
        if transaction_type not in self.config["prices of entries"] and \
                transaction_type not in self.config["prices of rentals"] and \
                transaction_type not in self.config["prices of sales"]:
            raise RuntimeError("A sale has been initialised that is not in the known config.")
        if transaction_type in self.config["prices of entries"]:
            self.client_count += 1
        self.sales_dict[transaction_type][0] += 1
        self.value += self.prices[transaction_type]

    def __str__(self) -> str:
        """ Represent a single transaction as a string. """
        msg = ""
        for key in self.sales_dict:
            if float(self.sales_dict[key][0]) > 0.:
                msg += "{} x {}\n".format(self.sales_dict[key][0], key)

        return msg

    def __add__(self, other: BMCTransaction) -> BMCTransaction:
        """ Define the addition operator on BMCTransactions. """
        # Make a new transaction
        comb_trans = BMCTransaction(config=self.config)

        # Set it's main fields
        comb_trans.value = self.value + other.value
        comb_trans.client_count = self.client_count + other.client_count
        comb_trans.modality = "multiple"

        # Set the exact sales dict by merging both together
        self_keys = self.sales_dict.keys()
        other_keys = other.sales_dict.keys()
        common_keys = [key for key in self_keys if key in other_keys]
        unique_self_keys = [key for key in self_keys if key not in other_keys]
        unique_other_keys = [key for key in other_keys if key not in self_keys]

        comb_trans.sales_dict = {}
        for key in common_keys:
            comb_trans.sales_dict[key] = [self.sales_dict[key][0] + other.sales_dict[key][0], other.sales_dict[key][1]]
        for key in unique_self_keys:
            comb_trans.sales_dict[key] = [self.sales_dict[key][0], self.sales_dict[key][1]]
        for key in unique_other_keys:
            comb_trans.sales_dict[key] = [other.sales_dict[key][0], other.sales_dict[key][1]]

        return comb_trans
