from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox

from session import BMCSessionManager


def ask_to_recover_from_backup_popup(previous_state: BMCSessionManager, date: QDate, counted_cash_count: float) -> bool:
    """ Pops up a message box asking whether to restore from the previous state found in a backup file_path, or to
    continue in a new session, de-facto discarding the backup file_path. """
    supervisor = previous_state.supervisor
    client_count = previous_state.client_count
    cash_count_on_file = "€" + str(previous_state.cash_count)
    info = "Il existe un fichier incomplet pour le {}\n\n".format(date.toString("dd/MM/yyyy"))
    info += "    Permanent selon backup : \t{}\n" \
            "    # clients selon backup: \t{}\n" \
            "    Caisse selon backup : \t{}\n" \
            "    \n" \
            "    Caisse actuelle  : \t€{}\n\n".format(supervisor, client_count, cash_count_on_file, counted_cash_count)
    info += "Voulez-vous récupérer la session trouvée ou démarrer une nouvelle session?\n"
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText("Attention : fichier existant")
    msg.setInformativeText(info)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.button(QMessageBox.Yes).setText('Récupérer session')
    msg.button(QMessageBox.No).setText('Nouvelle session')
    msg.setDefaultButton(QMessageBox.Yes)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

    retval = msg.exec_()
    if retval == 16384:
        return True
    elif retval == 65536:
        return False
    else:
        raise RuntimeError("unexpected error when recovering previous state")


def ask_to_confirm_quit_popup(cash_count: float) -> bool:
    """ Pops up a message box asking to confirm to quit the application and also displays how much cash should be
    in the register. """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Etes-vous sûr de vouloir quitter l'appli caisse?")
    msg.setInformativeText("Il devrait y avoir €{} en caisse.".format(cash_count))
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.button(QMessageBox.Yes).setText('Quitter')
    msg.button(QMessageBox.No).setText('Annuler')
    msg.setDefaultButton(QMessageBox.No)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

    retval = msg.exec_()
    if retval == 16384:
        return True
    elif retval == 65536:
        return False
    else:
        raise RuntimeError("unexpected error when confirming quit")


def ask_to_confirm_abo_delete(insist: bool) -> bool:
    """ Pops up a message box warning that this is a valid abonnement and asks to confirm whether the user really
     wants to delete a valid abonnement. """

    msg = QMessageBox()
    if not insist:
        msg.setIcon(QMessageBox.Question)
        msg.setText("Attention")
        msg.setInformativeText("Vous etes sur le point d'effacer un abonnement encore valide. Voulez-vous continuer?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Oui')
        msg.button(QMessageBox.No).setText('Annuler')
    else:
        msg.setIcon(QMessageBox.Warning)
        msg.setText("ATTENTION!")
        msg.setInformativeText("Etes-vous absolument sur de vouloir effacer un abonnement encore valide?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Effacer')
        msg.button(QMessageBox.No).setText('Annuler')
    msg.setDefaultButton(QMessageBox.No)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

    retval = msg.exec_()
    if retval == 16384:
        return True
    elif retval == 65536:
        return False
    else:
        raise RuntimeError("unexpected error")


def confirm_abo_creation_sponsor_popup(client_name: str) -> None:
    """ Pops up a message box confirming that the abonnement was successfully created and reminds the user to create
    an Lecomte fidelity card as they're our main sponsor. """
    msg = QMessageBox()
    pm = QPixmap("resources/lecomte.png")
    pm = pm.scaledToWidth(90)
    msg.setIconPixmap(pm)
    msg.setText("Abonnement crée")
    txt = "L'abonnement de {} a été crée. N'oubliez pas de faire une carte de fidelite Lecomte!".format(client_name)
    msg.setInformativeText(txt)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
    msg.exec_()


def simple_dialog(severity: str, title: str, text: str) -> None:
    """ Pops up a simple dialog window which only prints some information and closes down without doing anything. """
    if severity == "NoIcon":
        icon = QMessageBox.NoIcon
    elif severity == "Question":
        icon = QMessageBox.Question
    elif severity == "Information":
        icon = QMessageBox.Information
    elif severity == "Warning":
        icon = QMessageBox.Warning
    elif severity == "Critical":
        icon = QMessageBox.Critical
    else:
        raise ValueError("Severity must be one of NoIcon, Question, Information, Warning, Critical")

    msg = QMessageBox()
    msg.setIcon(icon)
    msg.setText(title)
    msg.setInformativeText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
    msg.exec_()


def confirm_reduction_popup(reduction: float) -> None:
    """ Pops up a message box asking to confirm the reduction to be applied. """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Voulez-vous appliquer une réduction pour le personnel?")
    msg.setInformativeText("Il est uniquement autorisé d'appliquer une réduction de {}% pour les achats des membres du "
                           "personnel. Voulez-vous appliquer la réduction?\n\nAttention: la réduction n'est appliquée "
                           "que pour les achats déjà dans la transaction et pas sur les achats que vous ajoutéz après"
                           " avoir appliqué la réduction.".format(int(100 - reduction*100)))
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.button(QMessageBox.Yes).setText('Oui')
    msg.button(QMessageBox.No).setText('Annuler')
    msg.setDefaultButton(QMessageBox.No)
    msg.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

    retval = msg.exec_()
    if retval == 16384:
        return True
    elif retval == 65536:
        return False
    else:
        raise RuntimeError("unexpected error when confirming quit")
