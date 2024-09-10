import copy
import datetime

import numpy as np
import pandas as pd


def main(input_path: str, account_balance_begin: float, account_balance_end: float) -> None:
    # Read in data
    transactions_frame = pd.read_csv(input_path, delimiter=";")

    # Split in incomes and expenses, and merge classifications
    expenses_frame = copy.deepcopy(transactions_frame[transactions_frame["Montant"] < 0.])
    incomes_frame = copy.deepcopy(transactions_frame[transactions_frame["Montant"] > 0.])
    incomes_frame["Categorie"] = incomes_frame["Categorie"].apply(lambda s: "Cours" if s.find("Cours") != -1 else s)
    incomes_frame["Categorie"] = incomes_frame["Categorie"].apply(
        lambda s: "Perm" if s.find("Bancontact") != -1 or s.find("Cash") != -1 else s)

    # Compute some check metrics
    turnover = transactions_frame[transactions_frame["Montant"] > 0.]["Montant"].sum()
    expenses = transactions_frame[transactions_frame["Montant"] < 0.]["Montant"].sum()

    # Process data
    print("--- RESUME ---")
    analyse_high_level(transactions_frame, account_balance_begin, account_balance_end)
    print("\n\n\n")

    print("--- RENTREES ---")
    analyse_incomes(incomes_frame, turnover)
    print("\n\n\n")

    print("--- DEPENSES ---")
    analyse_expenses(expenses_frame, expenses)
    print("\n")
    analyse_payroll(expenses_frame)
    print("\n")
    analyse_services(expenses_frame)
    print("\n")
    analyse_goods(expenses_frame)
    print("\n\n")


def analyse_high_level(df: pd.DataFrame, account_balance_begin: float, account_balance_end: float):
    """ Does a high-level analysis of the transactions. """
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    date_begin = df["Date"].min()
    date_end = df["Date"].max()
    turnover = df[df["Montant"] > 0.]["Montant"].sum()
    expenses = df[df["Montant"] < 0.]["Montant"].sum()
    profit = turnover + expenses

    print("Date début, {}".format(datetime.datetime.strptime(str(date_begin.date()), "%Y-%m-%d").strftime("%d/%m/%Y")))
    print("Date fin, {}".format(datetime.datetime.strptime(str(date_end.date()), "%Y-%m-%d").strftime("%d/%m/%Y")))
    print("Effectifs début, €{}".format(str(account_balance_begin)))
    print("Effectifs fin, €{}".format(str(account_balance_end)))
    print("Chiffre d'affaire, €{}".format(str(np.round(turnover, 2))))
    print("Dépenses, €-{}".format(str(np.round(abs(expenses), 2))))
    print("Benefice net, €{}".format(str(np.round(profit, 2))))

    assert np.round(account_balance_begin + turnover - abs(expenses), 2) == np.round(account_balance_end, 2), \
        "Error is {}€".format(np.round(account_balance_begin + turnover - abs(expenses) - account_balance_end, 2))


def analyse_incomes(df, total_incomes: float):
    """ Analyse the incomes. Breakdown per category and per trimester. """
    # Breakdown per period per category
    sf = df.sort_values(by=["Periode", "Categorie"])
    categories = sf["Categorie"].unique()
    periods = sf["Periode"].unique()

    data = np.zeros(shape=(len(categories), len(periods)))
    summed_vals = 0.0

    header = ""
    for prd in periods:
        header += ", " + str(prd)
    print(header)

    for i, cat in enumerate(categories):
        for j, per in enumerate(periods):
            val = np.round(sf[(sf["Categorie"] == cat) & (sf["Periode"] == per)]["Montant"].sum(), 2)
            data[i, j] = val
            summed_vals += val

    assert np.round(summed_vals, 2) == np.round(total_incomes, 2)

    for i, cat in enumerate(categories):
        line = cat
        for j, per in enumerate(periods):
            line += ", €" + str(np.round(data[i, j], 2))
        print(line)


def analyse_expenses(df, total_expenses: float):
    """ Analyse the expenses. Breakdown per category and per trimester. """
    # Breakdown per period per category
    sf = df.sort_values(by=["Periode", "Categorie"])
    global_frame = copy.deepcopy(sf)
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: "Salaires" if s.find("Salaires") != -1 else s)
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: "Services" if s.find("Services") != -1 else s)
    global_frame["Categorie"] = global_frame["Categorie"].apply(
        lambda s: "Marchandises" if s.find("Marchandises") != -1 else s)
    categories = global_frame["Categorie"].unique()
    periods = global_frame["Periode"].unique()

    data = np.zeros(shape=(len(categories), len(periods)))
    summed_vals = 0.0

    header = ""
    for prd in periods:
        header += ", " + str(prd)
    print(header)

    for i, cat in enumerate(categories):
        for j, per in enumerate(periods):
            val = -np.round(
                global_frame[(global_frame["Categorie"] == cat) & (global_frame["Periode"] == per)]["Montant"].sum(), 2)
            data[i, j] = val
            summed_vals += val

    assert np.round(-summed_vals, 2) == np.round(total_expenses, 2)

    for i, cat in enumerate(categories):
        line = cat
        for j, per in enumerate(periods):
            line += ", €" + str(np.round(data[i, j], 2))
        print(line)


def analyse_payroll(df):
    """ Analyse the expenses. Breakdown per category and per trimester. """
    # Breakdown per period per category
    sf = df.sort_values(by=["Periode", "Categorie"])
    global_frame = copy.deepcopy(sf)
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: "discard" if s.find("Salaires") == -1 else s)
    global_frame = global_frame[global_frame["Categorie"] != "discard"]
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: str(s).split(",")[1])
    categories = global_frame["Categorie"].unique()

    for cat in categories:
        val = -np.round(global_frame[(global_frame["Categorie"] == cat)]["Montant"].sum(), 2)
        print("{}, €{}".format(cat.replace(" ", ""), np.round(val, 2)))


def analyse_services(df):
    """ Analyse the expenses. Breakdown per category and per trimester. """
    # Breakdown per period per category
    sf = df.sort_values(by=["Periode", "Categorie"])
    global_frame = copy.deepcopy(sf)
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: "discard" if s.find("Services") == -1 else s)
    global_frame = global_frame[global_frame["Categorie"] != "discard"]
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: str(s).split(",")[1])
    categories = global_frame["Categorie"].unique()

    for cat in categories:
        val = -np.round(global_frame[(global_frame["Categorie"] == cat)]["Montant"].sum(), 2)
        print("{}, €{}".format(cat.replace(" ", ""), np.round(val, 2)))


def analyse_goods(df):
    """ Analyse the expenses. Breakdown per category and per trimester. """
    # Breakdown per period per category
    sf = df.sort_values(by=["Periode", "Categorie"])
    global_frame = copy.deepcopy(sf)
    global_frame["Categorie"] = global_frame["Categorie"].apply(
        lambda s: "discard" if s.find("Marchandises") == -1 else s)
    global_frame = global_frame[global_frame["Categorie"] != "discard"]
    global_frame["Categorie"] = global_frame["Categorie"].apply(lambda s: str(s).split(",")[1])
    categories = global_frame["Categorie"].unique()

    for cat in categories:
        val = -np.round(global_frame[(global_frame["Categorie"] == cat)]["Montant"].sum(), 2)
        print("{}, €{}".format(cat.replace(" ", ""), np.round(val, 2)))


if __name__ == "__main__":
    input_csv = r"/Users/jeremy/Library/Mobile Documents/com~apple~CloudDocs/BMC/Comptabilité/Extraits de compte/2020/363-0989738-87 CA (EUR) 20200101 - 20201231_classified.csv"
    begin_balance = 43580.99
    end_balance = 43580.99 + 3434.85
    main(input_csv, begin_balance, end_balance)
