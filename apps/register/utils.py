import csv
import os
from pathlib import Path

from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QPushButton, QSizePolicy


def get_button(name: str, min_width: int, min_height: int, color: str = "#ededed", gradient: int = 10) -> QPushButton:
    """ Wrapper to get a QPushButton easily. """
    button = QPushButton(name)
    button.setMinimumWidth(min_width)
    button.setMinimumHeight(min_height)
    button.setObjectName(name)

    # Normal color gradient
    rgb = tuple(int(color.strip("#")[i:i + 2], 16) for i in (0, 2, 4))
    rgb_lower = (rgb[0] - gradient, rgb[1] - gradient, rgb[2] - gradient)
    rgb_higher = (rgb[0] + gradient, rgb[1] + gradient, rgb[2] + gradient)
    rgb_lower = tuple([0 if c < 0 else (c if c <= 255 else 255) for c in rgb_lower])
    rgb_higher = tuple([0 if c < 0 else (c if c <= 255 else 255) for c in rgb_higher])
    bgr = ("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {}, stop:0 {}, stop: 1.0 "
           "{});").format(QColor(*rgb_higher).name(), QColor(*rgb_lower).name(), QColor(*rgb_higher).name())

    # Pressed darker color gradient
    rgb_lower = (rgb[0] - gradient - 30, rgb[1] - gradient - 30, rgb[2] - gradient - 30)
    rgb_higher = (rgb[0] + gradient - 30, rgb[1] + gradient - 30, rgb[2] + gradient - 30)
    rgb_lower = tuple([0 if c < 0 else (c if c <= 255 else 255) for c in rgb_lower])
    rgb_higher = tuple([0 if c < 0 else (c if c <= 255 else 255) for c in rgb_higher])
    bgr_pressed = (
        "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {}, stop:0 {}, stop: 1.0 "
        "{});").format(QColor(*rgb_higher).name(), QColor(*rgb_lower).name(), QColor(*rgb_higher).name())

    # Set the stylesheet to the button
    button.setStyleSheet(
        "QPushButton{" +
            "font-weight: normal;" +
            "color: rgb(0, 0, 0);" +
            "border: 1px;" +
            "border-style: solid;" +
            "border-radius: 3px;" +
            "border-color: rgb(175, 175, 175);" +
            str(bgr) +
        "}" +
        "QPushButton:disabled{" +
            "color: rgb(130, 130, 130);"
        "}"
        "QPushButton:pressed{" +
            "color: rgb(255, 255, 255Z);" +
            str(bgr_pressed) +
        "}"
    )

    return button


def get_fake_label(name: str) -> QPushButton:
    """ Gets a sort of boxed label by abusing the QPushbutton class. """
    label = get_button(name, 10, 30)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    label.setStyleSheet("font-size: 14pt; border: 1px; border-style: solid; border-radius: 0px; border-color: rgb(175, 175, 175); background-color: rgb(237, 237, 237)")

    return label


def get_weekday_from_date(date: QDate) -> str:
    """ Get the day of the week as a french string. """
    day_of_week = date.dayOfWeek()
    if day_of_week == 1:
        return "Lundi"
    elif day_of_week == 2:
        return "Mardi"
    elif day_of_week == 3:
        return "Mercredi"
    elif day_of_week == 4:
        return "Jeudi"
    elif day_of_week == 5:
        return "Vendredi"
    elif day_of_week == 6:
        return "Samedi"
    elif day_of_week == 7:
        return "Dimanche"
    raise RuntimeError("Expected day_of_week to be an int from 1 to 7 but got {} instead".format(day_of_week))


def get_month_name_from_int(month: int) -> str:
    """ Convert an int to a string for the corresponding month"""
    if not 0 < month < 13:
        raise ValueError("Month must be an int in the range [1 - 12]")

    mois = {
        "1": "janvier",
        "2": "fevrier",
        "3": "mars",
        "4": "avril",
        "5": "mai",
        "6": "juin",
        "7": "juillet",
        "8": "aout",
        "9": "septembre",
        "10": "octobre",
        "11": "novembre",
        "12": "decembre"
    }

    return mois[str(month)]


def get_path_to_new_report_file(root_dir: Path or str, date: QDate) -> str:
    """ Sets up the file_path structure for saving financial daily report files which are organised by year - month - day.
    Checks that there is a folder for the corresponding year, and month, and if not creates a new folder. """
    # Input processing
    root_dir = Path(root_dir)
    if not root_dir.is_dir():
        raise FileNotFoundError("could not find the root dir")
    day = date.day()
    month_as_int = date.month()
    month_as_str = get_month_name_from_int(month_as_int)
    year = date.year()

    # Make the parent directories if neccesary
    if not root_dir.joinpath(str(year)).is_dir():
        root_dir.joinpath(str(year)).mkdir()
        os.chmod(str(root_dir.joinpath(str(year))), 0o777)

    if not root_dir.joinpath(str(year), str(month_as_str)).is_dir():
        root_dir.joinpath(str(year), str(month_as_str)).mkdir()
        os.chmod(str(root_dir.joinpath(str(year), str(month_as_str))), 0o777)

    # Construct the path to this date's report file_path
    new_file_path = root_dir.joinpath(str(year), str(month_as_str),
                                      str(year) + "-" + str(month_as_int) + "-" + str(day) + ".csv")

    # Check that the parent directories were successfully created
    if not Path(new_file_path.parent).is_dir():
        raise IOError("The save path for today's financial report was not successfully created")

    return new_file_path


def get_most_recent_report_path(root_dir: str or Path) -> str:
    """ Goes through all files in the folder containing all the registry's reports, filters for csv's and returns the
     path to the most recent report. """
    root_dir = Path(root_dir)
    most_recent_file, most_recent_mod = None, 0.0
    for file in root_dir.glob("*/*/*.csv"):
        if file.is_file() and file.stat().st_mtime > most_recent_mod:
            most_recent_file = file
            most_recent_mod = file.stat().st_mtime

    # Check that the most recent financial report was found
    if most_recent_file is None:
        print("Most recent file is none")
        raise IOError("The most recent financial report file_path was not found in root dir {}".format(root_dir))

    return str(most_recent_file)


def get_expected_cash_from_report(file_path: Path or str) -> float or int:
    """ Given the path to a registry report file_path parses the file_path and returns the expected cash count. """
    with open(file_path, encoding='utf-8') as report:
        csv_reader = csv.reader(report, delimiter=";")
        for row in csv_reader:
            if len(row) == 2 and row[0] == "Caisse fin":
                return float(row[1].replace("€", ""))
    raise IOError("Could not get the expected cash count from file_path: {}".format(str(file_path)))


def write_report_file(transactions, session_dict: dict, file_path: Path or str):
    """ Given a BMCTransaction instance combining all the current session's transactions into one, and given a
    session_dict containing all of this session's data writes a registry report csv file_path to store all this date. """
    with open(file_path, mode="w", encoding='utf-8') as report:
        for key in session_dict:
            report.write(key + ";" + str(session_dict[key]) + "\n")
            if key == "Erreur caisse":
                for sales_key in transactions.sales_dict:
                    if transactions.sales_dict[sales_key][0] > 0:
                        line = ""
                        line += str(round(transactions.sales_dict[sales_key][0], 2))
                        line += ";"
                        line += sales_key
                        line += ";"
                        line += str(round(transactions.sales_dict[sales_key][1], 2))
                        line += ";"
                        line += str(
                            round(transactions.sales_dict[sales_key][0] * transactions.sales_dict[sales_key][1], 2))
                        line += "\n"
                        report.write(line)
    os.chmod(str(file_path), 0o777)
