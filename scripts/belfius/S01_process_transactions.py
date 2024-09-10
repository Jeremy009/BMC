""" This script is used to prepare a .csv file with expense transactions downloaded (manually) from Belfius Direct Net.
 The expenses will be classified into predefined categories, and the tabular data will be preprocessed to be
 imported in the 'official' accountant Excel file.

 The user will have to manually set the environemental constants hereunder:
 INPUT_CSV: Must be the path to the actual .csv file
 DECIMAL_POINT_IN_OUTPUT: Easily switch between . and , for decimal point representation
 REFINE_MANUALLY: Whether to manually correct dubious classifications
 """

import re
import unicodedata
import pandas as pd
from typing import List
from pathlib import Path

INPUT_CSVS = [str(csv_path) for csv_path in Path(r"/Users/jlb5pbf/Library/CloudStorage/GoogleDrive-jeremy@brusselsmonkeysclimbing.com/My Drive/BMC/BMC-Protected/Comptabilité/2023/Comptabilite/extraits").glob("*.csv")]


DECIMAL_POINT_IN_OUTPUT = ","
REFINE_MANUALLY = False

HEADER = 12

EXPENSE_CLASSES = [
    ["Loyer"],
    ["Remunerations", "Volontaires"],
    ["Remunerations", "CDI", "ONSS"],
    ["Remunerations", "CDI", "Precompte prof."],
    ["Remunerations", "CDI", "Cheques repas"],
    ["Remunerations", "CDI"],
    ["Remunerations", "TA"],
    ["Remunerations", "Etudiants"],
    ["Remunerations", "Independants"],
    ["Services", "Secretariat sociale"],
    ["Services", "Comptabilité"],
    ["Services", "Bancontact"],
    ["Services", "Belfius"],
    ["Services", "Assurances"],
    ["Services", "Club Alpin"],
    ["Services", "BFIC"],
    ["Services", "Stib"],
    ["Services", "SNCB"],
    ["Services", "Peage"],
    ["Marchandises", "Lecomte"],
    ["Marchandises", "Bricolage"],
    ["Marchandises", "Sport"],
    ["Marchandises", "Multimedia"],
    ["Marchandises", "Mobilier"],
    ["Marchandises", "Carburants"],
    ["Marchandises", "Consumables"],
    ["Marchandises", "Autres"],
    ["Remboursements"],
    ["Investissements", "Prises"],
    ["Investissements", "Van"],
    ["Visa"],
    ["Entrées salles"],
    ["Autre dépenses"],
    ["-1"]
]

INCOME_CLASSES = [
    ["Cours", "Ok"],
    ["Cours", "Check"],
    ["Bancontact"],
    ["Cash"],
    ["Consumations"],
    ["Factures"],
    ["Stages"],
    ["Subsides et sponsoring"],
    ["Autre rentrées"],
    ["Location van"],
    ["Remboursements"],
    ["-1"]
]


def reduce_whitespace(s: str) -> str:
    """ Reduces multiple successive whitespaces to a singel whitespace. """
    return " ".join(str(s).split())


def prune_frame(df: pd.DataFrame, keep: str) -> pd.DataFrame:
    """ Gets rid of rows which have €0,00 monetary value, and removes uninterresting columns. """
    df = df.drop(df[df["Montant"] == 0.0].index)
    df = df.drop(df[df["Montant"] >= 0.0].index) if keep == "expenses" else df.drop(df[df["Montant"] <= 0.0].index)
    df = df.drop(["Compte", "Numéro d'extrait", "Rue et numéro", "Code postal et localité", "Date valeur", "BIC",
                  "Code pays"], axis=1)

    return df


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """ Typechecking and removal of excessive whitespace. """
    df["Montant"] = df["Montant"].apply(lambda s: float(str(s).replace(",", ".").replace("nan", "0.00")))
    df["Numéro de transaction"] = pd.to_numeric(df["Numéro de transaction"], downcast="unsigned")
    df["Transaction"] = df["Transaction"].apply(reduce_whitespace)
    df["Communications"] = df["Communications"].apply(reduce_whitespace)
    df["Nom contrepartie contient"] = df["Nom contrepartie contient"].apply(lambda s: str(s).replace("nan", ""))
    df["Description"] = df["Nom contrepartie contient"] + " " + df["Transaction"] + " " + df["Communications"]
    df["Description"] = df["Description"].apply(lambda s: str(s).lower())
    df["Description"] = df["Description"].apply(lambda s: reduce_whitespace(s))

    return df


def postprocess_frame(df: pd.DataFrame) -> pd.DataFrame:
    """ Makes the description more readable. """

    def _clean_up_description(data_row: pd.Series) -> str:
        if data_row["Categorie"] == "Loyer" and -data_row["Montant"] > 500:
            return "Loyer salle escalade"
        if data_row["Categorie"] == "Loyer" and -data_row["Montant"] < 500:
            return "Loyer location bureau"

        if data_row["Categorie"] == "Entrées salles":
            return "Entrée(s) autre salle {}".format(data_row["Nom contrepartie contient"].title().split("  ")[0])

        if data_row["Categorie"] == "Remunerations, Volontaires":
            return "Rémuneration volontariat {}".format(data_row["Nom contrepartie contient"].title())
        if data_row["Categorie"] == "Remunerations, TA":
            return "Travail associatif {}".format(data_row["Nom contrepartie contient"].title())
        if data_row["Categorie"] == "Remunerations, CDI, ONSS":
            return "Charges sociale ONSS"
        if data_row["Categorie"] == "Remunerations, CDI, Precompte prof.":
            return "Précompte professionel"
        if data_row["Categorie"] == "Remunerations, CDI, Cheques repas":
            return "Cheques repas"

        if data_row["Categorie"].find("Services") != -1:
            return data_row["Categorie"].replace(",", ":")
        if data_row["Categorie"].find("Marchandises") != -1:
            return data_row["Categorie"].replace(",", ":")

        if data_row["Categorie"].find("Bancontact") != -1:
            return "Rentrées permanence par Bancontact"
        if data_row["Categorie"].find("Cours, Ok") != -1:
            return "Cotisation cours"

        return data_row["Description"]

    df["Description"] = df.apply(_clean_up_description, axis=1)

    return df


def export_frame(df: pd.DataFrame, save_path: str) -> None:
    """ Makes the frame more readable and then exports it. """
    ef = df.loc[:, ["Date de comptabilisation", "Description", "Numéro de transaction", "Montant", "Categorie",
                    "Periode"]]
    ef.columns = ["Date registration", "Description", "Nr", "Montant", "Categorie", "Periode"]

    ef["Date registration"] = pd.to_datetime(ef["Date registration"], format="%d/%m/%Y").dt.date
    ef = ef.sort_values(by=["Date registration", "Nr"])
    ef.to_excel(str(save_path).replace(".csv", ".xlsx"), index=False)

    return


def strip_accents(s: str) -> str:
    """ Accepts a string and returns the string without accents. """
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def determine_period(data_row: pd.Series) -> str:
    """ Determines the quarterly period based on the transaction date. """
    date = data_row["Date de comptabilisation"]
    matches = re.findall(r"\d\d/\d\d/\d\d\d\d", date)
    if not len(matches) == 1:
        raise ValueError("date should be in dd/mm/yyyy format but is {}".format(date))
    period = date[6:]
    month = int(date[3:5])
    if 1 <= month < 4:
        period += "Q1"
    elif 4 <= month < 7:
        period += "Q2"
    elif 7 <= month < 10:
        period += "Q3"
    elif 10 <= month < 13:
        period += "Q4"
    else:
        raise ValueError("invalid month")

    return period


def classify_manually(amount: str, features: str, transaction_type: str):
    """ If needed gives the option to manually specify the classification of a certain expense in the terminal. """
    if REFINE_MANUALLY:
        if transaction_type == "expense":
            classes = EXPENSE_CLASSES
        elif transaction_type == "income":
            classes = INCOME_CLASSES
        else:
            raise ValueError("transaction_type must be expense or income")
        print("A transaction with an ambiguous classification was found. Please classify manually")
        print(amount, features)
        for i, class_name in enumerate(classes):
            print("{}: {}".format(i, class_name))
        class_idx = input("Classification nr.: ")
        classification = classes[int(class_idx)]
        print("Classified as {}\n\n".format(classification))

        return classification
    else:
        return ["-1"]


def classify(data_row: pd.Series) -> str:
    """ Classifies all rows. """
    amount = str(data_row["Montant"])
    if float(amount) < 0.0:
        return classify_expense(data_row)
    elif float(amount) > 0.0:
        return classify_income(data_row)
    else:
        raise RuntimeError("0-value rows should have been pruned")


def classify_expense(data_row: pd.Series) -> str:
    """ Classifies all expenses. """
    # Define some variables which can be used to determine the classification of the current row
    features = data_row["Description"].lower()
    iban = str(data_row["Compte contrepartie"])
    amount = str(data_row["Montant"])
    classification = list()
    num_classifications = 0
    assert float(amount) < 0.0

    # Loyers
    if iban == "BE66 0682 2865 0043":
        classification.extend(["Loyer"])
        num_classifications += 1
    if features.find("sous-location") != -1:
        classification.extend(["Loyer"])
        num_classifications += 1

    # Remunerations (volontariat et travail associatif)
    if features.find("volontariat") != -1 or features.find("volontairiat") != -1:
        classification.extend(["Remunerations", "Volontaires"])
        num_classifications += 1
    if features.find("travail associatif") != -1:
        classification.extend(["Remunerations", "TA"])
        num_classifications += 1
    if features.find("facturation heures") != -1 or features.find("belgiquescalade") != -1 or features.find("bel escalade") != -1:
        classification.extend(["Remunerations", "Independants"])
        num_classifications += 1

    # ONSS, PP, etc.
    if iban == "BE39 6791 6925 7219" or iban == "BE63 6790 2618 1108":
        classification.extend(["Remunerations", "CDI", "ONSS"])
        num_classifications += 1
    if iban == "BE32 6792 0022 7602":
        classification.extend(["Remunerations", "CDI", "Precompte prof."])
        num_classifications += 1
    if features.find("edenred") != -1:
        classification.extend(["Remunerations", "CDI", "Cheques repas"])
        num_classifications += 1

    # Services
    if iban == "BE55 3100 2694 2444" or features.find("worldline sa") != -1:
        classification.extend(["Services", "Bancontact"])
        num_classifications += 1
    if features.find("axa") != -1 or features.find("ethias") != -1 or features.find("ag insurance") != -1:
        classification.extend(["Services", "Assurances"])
        num_classifications += 1
    if features.find("bfic") != -1:
        classification.extend(["Services", "BFIC"])
        num_classifications += 1
    if iban == "BE34 0882 1660 0890" or features.find("club alpin belge") != -1:
        classification.extend(["Services", "Club Alpin"])
        num_classifications += 1
    if features.find("cout gestion carte de debit") != -1 or features.find(
            "tenue de votre belfius business pack") != -1:
        classification.extend(["Services", "Belfius"])
        num_classifications += 1
    if features.find("associatif financier") != -1:
        classification.extend(["Services", "Secretariat sociale"])
        num_classifications += 1
    if features.find("nmbs") != -1 or features.find("sncb") != -1:
        classification.extend(["Services", "SNCB"])
        num_classifications += 1
    if features.find("stib") != -1 or features.find("mivb") != -1:
        classification.extend(["Services", "Stib"])
        num_classifications += 1
    if features.find("sanef") != -1 or \
            features.find("aprr") != -1 or \
            features.find("autoroute") != -1:
        classification.extend(["Services", "Peage"])
        num_classifications += 1

    # Marchandises
    if iban == "310-0601340-26" or features.find("alpinisme et rando") != -1 or features.find("lecomte") != -1:
        classification.extend(["Marchandises", "Lecomte"])
        num_classifications += 1
    if features.find("brand of rebels") != -1 or \
            features.find("decathlon") != -1 or \
            features.find("as adventure") != -1:
        classification.extend(["Marchandises", "Sport"])
        num_classifications += 1
    if features.find("brico") != -1 or \
            features.find("clabots") != -1 or \
            features.find("plan-it") != -1 or \
            features.find("noya eleven tools") != -1:
        classification.extend(["Marchandises", "Bricolage"])
        num_classifications += 1
    if features.find("media markt") != -1 or \
            (features.find("apple") != -1 and features.find("apple pay") == -1) or \
            features.find("vanden borre") != -1 or \
            features.find("coolblue") != -1 or \
            features.find("bol.com") != -1 or \
            features.find("krefel") != -1:
        classification.extend(["Marchandises", "Multimedia"])
        num_classifications += 1
    if features.find("colruyt") != -1 or \
            features.find("oscar drink") != -1 or \
            features.find("delhaize") != -1 or \
            features.find("leclerc") != -1 or \
            features.find("intermarche") != -1 or \
            features.find("chalk rebels") != -1 or \
            features.find("batteria") != -1 or \
            features.find("coop") != -1:
        classification.extend(["Marchandises", "Autres"])
        num_classifications += 1
    if features.find("ikea") != -1:
        classification.extend(["Marchandises", "Mobilier"])
        num_classifications += 1
    if (features.find("carburant") != -1 or
            features.find("esso") != -1 or
            features.find("bp ") != -1 or
            features.find("texaco") != -1 or
            features.find("q8") != -1 or
            features.find("shell") != -1 or
            features.find("lukoil") != -1 or
            features.find("total") != -1 or
            features.find("relais") != -1 or
            features.find("octa") != -1):
        classification.extend(["Marchandises", "Carburants"])
        num_classifications += 1

    # Investissements
    if features.find("gorgon") != -1:
        classification.extend(["Investissements", "Van"])
        num_classifications += 1
    if features.find("agripp") != -1 or \
            features.find("bavaria holds") != -1 or \
            features.find("entre prises") != -1 or \
            features.find("entre-prises") != -1 or \
            features.find("entreprises") != -1 or \
            features.find("lapiz") != -1 or \
            features.find("xcult") != -1 or \
            features.find("x-cult") != -1 or \
            features.find("x cult") != -1 or \
            features.find("cheeta") != -1 or \
            features.find("kitka") != -1 or \
            features.find("ibex") != -1 or \
            features.find("rokodromo") != -1:
        classification.extend(["Investissements", "Prises"])
        num_classifications += 1

    # Remboursements
    if features.find("remboursement") != -1:
        classification.extend(["Remboursements"])
        num_classifications += 1

    # Mastercard
    if features.find("visa releve") != -1:
        classification.extend(["Visa"])
        num_classifications += 1

    # Autres salles
    if (features.find("agb puurs vrijha") != -1 or
            features.find("complexe sportif - louvain-la") != -1 or
            features.find("petite ile") != -1 or
            features.find("centre sportif d") != -1 or
            features.find("klimkaffee bvba") != -1 or
            features.find("boulder bvba") != -1 or
            features.find("maniak") != -1 or
            features.find("kergen raphael") != -1 or
            features.find("entre ciel et terre") != -1 or
            features.find("new rock") != -1 or
            features.find("rlc climbers") != -1 or
            features.find("block out") != -1 or
            features.find("kletterzentrum") != -1 or
            features.find("escalade charler") != -1 or
            features.find("stuntwerk") != -1 or
            features.find("kraftwerk") != -1 or
            features.find("bleau bvba") != -1 or
            features.find("crux boulder") != -1 or
            features.find("a bloc") != -1 or
            features.find("camp de base") != -1 or
            features.find("terres verticale") != -1 or
            features.find("arkose") != -1 or
            features.find("gemeente puurs") != -1 or
            features.find("blackbox") != -1 or
            features.find("centre sportif de la w") != -1 or
            features.find("pink peaks") != -1 or
            features.find("bebloc") != -1 or
            features.find("klim en boulderzaal th ant") != -1 or
            features.find("rhino") != -1 or
            features.find("boulderhal breda") != -1 or
            features.find("face nord") != -1 or
            features.find("boulder bvba") != -1 or
            features.find("ecole d'escalade") != -1):
        classification.extend(["Entrées salles"])
        num_classifications += 1

    # Remboursement van
    if (features.find("van breda car finance") != -1):
        classification.extend(["Investissements", "Van"])
        num_classifications += 1

    # Check that the classification is correct
    assert num_classifications >= 0
    if num_classifications == 0:
        classification.extend(["Autre dépenses"])
    elif num_classifications > 1:
        classification = classify_manually(amount, features, transaction_type="expense")

    # Validate the classification and return
    assert classification in EXPENSE_CLASSES, "{}".format(classification)
    return ", ".join(classification)


def classify_income(data_row: pd.Series) -> str:
    """ Classifies all incomes. """
    # Define some variables which can be used to determine the classification of the current row
    features = data_row["Description"].lower()
    amount = str(data_row["Montant"])
    classification = list()
    num_classifications = 0
    assert float(amount) > 0.0

    # Bancontact
    if (features.find("gr ") != -1 and features.find("bancontact") != -1) or features.find("worldline") != -1:
        classification.extend(["Bancontact"])
        num_classifications += 1

    # Especes
    if strip_accents(features).find("rentrees especes") != -1:
        classification.extend(["Cash"])
        num_classifications += 1

    # Bancontact
    if features.find("boissons") != -1 or features.find("distributeur") != -1:
        classification.extend(["Consumations"])
        num_classifications += 1

    # Cours
    crs_rexes = re.findall(r"t2017\d+", features) + re.findall(r"t2018\d+", features) + \
                re.findall(r"t2019\d+", features) + re.findall(r"t2020\d+", features) + \
                re.findall(r"t2021\d+", features) + re.findall(r"t2022\d+", features) + \
                re.findall(r"t2023\d+", features) + \
                re.findall(r"communication : t\d+\s", features)
    if len(crs_rexes) > 0 or \
            features.find("2017t3") != -1 or \
            features.find("2018t1") != -1 or \
            features.find("2018t2") != -1 or \
            features.find("2018t3") != -1 or \
            features.find("t2021-") != -1 or \
            features.find("t2022-") != -1 or \
            features.find("t2023-") != -1:
        classification.extend(["Cours", "Ok"])
        num_classifications += 1
    if (features.find("inscription") != -1 or
            features.find("affiliation") != -1 or
            features.find("trimestre") != -1 or
            features.find("lidmaatschap") != -1 or
            features.find("cotisation") != -1 or
            features.find("cours") != -1):
        if len(crs_rexes) > 0:
            pass
        else:
            classification.extend(["Cours", "Check"])
            num_classifications += 1

    # Factures
    fac_rexes = re.findall(r"2017f\d+", features) + \
                re.findall(r"2018f\d+", features) + \
                re.findall(r"2019f\d+", features) + \
                re.findall(r"2020f\d+", features) + \
                re.findall(r"2021f\d+", features) + \
                re.findall(r"2022f\d+", features)
    if len(fac_rexes) > 0:
        classification.extend(["Factures"])
        num_classifications += 1

    # Stages
    if features.find("stage") != -1 or \
            features.find("fontainebleau") != -1 or \
            features.find("bleau") != -1 or \
            features.find("margalef") != -1 or \
            features.find("leonidio") != -1 or \
            features.find("tarn") != -1 or \
            features.find("freyr") != -1 or \
            features.find("berdorf") != -1:
        classification.extend(["Stages"])
        num_classifications += 1

    # Check that the classification is correct
    assert num_classifications >= 0
    if num_classifications == 0:
        classification.extend(["Autre rentrées"])
    elif num_classifications > 1:
        classification = classify_manually(amount, features, transaction_type="income")

    # Validate the classification and return
    assert classification in INCOME_CLASSES
    return ", ".join(classification)


def main(input_path: str or List) -> None:
    # Read and prepare the data
    if isinstance(input_path, List):
        expenses_frame = None
        for fp in input_path:
            ef = pd.read_csv(fp, delimiter=";", encoding='LATIN', header=HEADER)
            if expenses_frame is None:
                expenses_frame = ef
            else:
                expenses_frame = pd.concat([expenses_frame, ef], ignore_index=True)
        input_path = input_path[0]
    else:
        expenses_frame = pd.read_csv(input_path, delimiter=";", encoding='LATIN', header=HEADER)
    expenses_frame = prepare_frame(expenses_frame)

    # Handle in and out transactions
    for keep in ["expenses", "incomes"]:
        pruned_frame = prune_frame(expenses_frame, keep)

        # Classify transaction
        pruned_frame["Categorie"] = pruned_frame.apply(classify, axis=1)

        # Add a period field
        pruned_frame["Periode"] = pruned_frame.apply(determine_period, axis=1)

        # Export processed frames
        save_path = str(Path(input_path).with_name("classified {}.csv".format(keep)))
        pruned_frame = postprocess_frame(pruned_frame)
        export_frame(pruned_frame, save_path)
        print(f"Saved {keep} to {save_path}")

        # Some stats
        num_transactions = pruned_frame.shape[0]
        num_expenses = pruned_frame.shape[0]
        num_classified_expenses = len(pruned_frame[pruned_frame["Categorie"] != "Autre dépenses"].index)
        num_unclassified_expenses = len(pruned_frame[pruned_frame["Categorie"] == "Autre dépenses"].index)

        print(keep)
        print("Number of transactions: {}".format(num_transactions))

        print("Number of expenses: {}".format(num_expenses))
        print("- classified: {}".format(num_classified_expenses))
        print("- unclassified: {}".format(num_unclassified_expenses))

        # Some sanity checks
        print("Check 1:", num_transactions == num_expenses)
        print("Check 2:", num_expenses == num_classified_expenses + num_unclassified_expenses)
        print("\n\n\n\n")


if __name__ == "__main__":
    main(INPUT_CSVS)
