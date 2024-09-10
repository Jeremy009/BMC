import copy
import re
import unicodedata
import pandas as pd
from scripts.legacy.support import preprocess_frame, prune_frame

REFINE_MANUALLY = True

EXPENSE_CLASSES = [
    ["Loyer"],
    ["Salaires", "Volontaires"],
    ["Salaires", "CDI", "ONSS"],
    ["Salaires", "CDI", "Precompte prof."],
    ["Salaires", "CDI", "Cheques repas"],
    ["Salaires", "CDI", "Kevin"],
    ["Salaires", "CDI", "Ben"],
    ["Salaires", "TA", "Michael"],
    ["Salaires", "TA", "Jeremy"],
    ["Salaires", "TA", "Guillaume"],
    ["Salaires", "Etudiants"],
    ["Services", "Secretariat sociale"],
    ["Services", "Comptabilité"],
    ["Services", "Bancontact"],
    ["Services", "Assurances"],
    ["Services", "Club Alpin"],
    ["Services", "Stib"],
    ["Marchandises", "Lecomte"],
    ["Marchandises", "Brico"],
    ["Marchandises", "Decathlon"],
    ["Marchandises", "Media Markt"],
    ["Marchandises", "Ikea"],
    ["Marchandises", "Agripp"],
    ["Marchandises", "Carburant"],
    ["Marchandises", "Prises"],
    ["Marchandises", "Apple"],
    ["Remboursements"],
    ["Mastercard"],
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
    ["Subsides"],
    ["Autre rentrées"],
    ["-1"]
]


def main(input_path: str) -> None:
    # Read and prepare the data
    transactions_frame = pd.read_csv(input_path, delimiter=";", encoding="UTF-8")
    transactions_frame = preprocess_frame(transactions_frame)
    transactions_frame = prune_frame(transactions_frame)

    # Extract expenses and incomes
    expenses_frame = copy.deepcopy(transactions_frame[transactions_frame["Bedrag"] < 0.])
    incomes_frame = copy.deepcopy(transactions_frame[transactions_frame["Bedrag"] > 0.])

    # Classify transaction
    expenses_frame["Categorie"] = expenses_frame.apply(classify_expense, axis=1)
    incomes_frame["Categorie"] = incomes_frame.apply(classify_income, axis=1)

    # Add a period field
    expenses_frame["Periode"] = expenses_frame.apply(determine_period, axis=1)
    incomes_frame["Periode"] = incomes_frame.apply(determine_period, axis=1)

    # Export processed frames
    transactions_frame = pd.concat([expenses_frame, incomes_frame])
    export_frame(transactions_frame, input_path.replace(".csv", "_classified.csv"))

    # Some stats
    num_transactions = transactions_frame.shape[0]
    num_expenses = expenses_frame.shape[0]
    num_incomes = incomes_frame.shape[0]
    num_classified_expenses = len(expenses_frame[expenses_frame["Categorie"] != "Autre dépenses"].index)
    num_unclassified_expenses = len(expenses_frame[expenses_frame["Categorie"] == "Autre dépenses"].index)
    num_classified_incomes = len(incomes_frame[incomes_frame["Categorie"] != "Autre rentrées"].index)
    num_unclassified_incomes = len(incomes_frame[incomes_frame["Categorie"] == "Autre rentrées"].index)

    print("Number of transactions: {}".format(num_transactions))

    print("Number of expenses: {}".format(num_expenses))
    print("- classified: {}".format(num_classified_expenses))
    print("- unclassified: {}".format(num_unclassified_expenses))

    print("Number of incomes: {}".format(num_incomes))
    print("- classified: {}".format(num_classified_incomes))
    print("- unclassified: {}".format(num_unclassified_incomes))

    # Some sanity checks
    print("\n")
    print("Check 1:", num_transactions == num_expenses + num_incomes)
    print("Check 2:", num_expenses == num_classified_expenses + num_unclassified_expenses)
    print("Check 3:", num_incomes == num_classified_incomes + num_unclassified_incomes)


def export_frame(df: pd.DataFrame, save_path: str) -> None:
    """ Makes the frame more readable and then exports it. """
    ef = df[["Rekening tegenpartij", "Boekingsdatum", "Periode", "Bedrag", "Categorie", "Omschrijving",
             "Detail van de omzet", "Bericht"]]
    ef.columns = ["IBAN beneficiaire", "Date", "Periode", "Montant", "Categorie", "Description", "Communication",
                  "Message"]
    ef["Communication"] = ef["Communication"].apply(lambda s: s[s.find("Communic"):] if s.find("Communic") != -1 else s)
    ef = ef.sort_values(by=["Categorie"])
    ef.to_csv(str(save_path))

    return


def strip_accents(s: str) -> str:
    """ Accepts a string and returns the string without accents. """
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def determine_period(data_row: pd.Series) -> str:
    """ Determines the quarterly period based on the transaction date. """
    date = data_row["Boekingsdatum"]
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


def manually_classify(amount: str, features: str, transaction_type: str):
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


def classify_expense(data_row: pd.Series) -> str:
    """ Classifies all expenses. """
    # Define some variables which can be used to determine the classification of the current row
    features = (data_row["Omschrijving"] + " " + data_row["Detail van de omzet"] + " " + data_row["Bericht"]).lower()
    iban = str(data_row["Rekening tegenpartij"])
    amount = str(data_row["Bedrag"])
    classification = list()
    num_classifications = 0
    assert float(amount) < 0.0

    # Loyers
    if iban == "068-2286500-43":
        classification.extend(["Loyer"])
        num_classifications += 1

    # Salaires
    if features.find("volontariat") != -1:
        classification.extend(["Salaires", "Volontaires"])
        num_classifications += 1
    if iban == "679-0261811-08":
        classification.extend(["Salaires", "CDI", "ONSS"])
        num_classifications += 1
    if iban == "679-2002276-02" or iban == "679-2002402-31":
        classification.extend(["Salaires", "CDI", "Precompte prof."])
        num_classifications += 1
    if features.find("edenred") != -1:
        classification.extend(["Salaires", "CDI", "Cheques repas"])
        num_classifications += 1
    if iban == "973-3545458-45" or iban == "310-1759480-83":
        classification.extend(["Salaires", "CDI", "Kevin"])
        num_classifications += 1
    if iban == "001-4199021-64":
        classification.extend(["Salaires", "CDI", "Ben"])
        num_classifications += 1
    if iban == "310-1496092-50" or iban == "310-4617628-29":
        classification.extend(["Salaires", "TA", "Michael"])
        num_classifications += 1
    if iban == "370-1186881-76":
        classification.extend(["Salaires", "TA", "Guillaume"])
        num_classifications += 1
    if iban == "063-3820090-71" or iban == "083-2834552-21" or features.find("jeremy lombaerts") != -1:
        classification.extend(["Salaires", "TA", "Jeremy"])
        num_classifications += 1
    if features.find("salaire etudiant") != -1 or features.find("salaire étudiant") != -1:
        classification.extend(["Salaires", "Etudiants"])
        num_classifications += 1

    # Services
    if iban == "310-1070573-70":
        classification.extend(["Services", "Secretariat sociale"])
        num_classifications += 1
    if iban == "063-5847507-91":
        classification.extend(["Services", "Comptabilité"])
        num_classifications += 1
    if iban == "310-0269424-44":
        classification.extend(["Services", "Bancontact"])
        num_classifications += 1
    if features.find("axa") != -1 or features.find("ethias") != -1:
        classification.extend(["Services", "Assurances"])
        num_classifications += 1
    if iban == "523-0808203-74" or iban == "088-2166008-90":
        classification.extend(["Services", "Club Alpin"])
        num_classifications += 1
    if features.find("stib".lower()) != -1:
        classification.extend(["Services", "Stib"])
        num_classifications += 1

    # Marchandises
    if iban == "310-0601340-26" or features.find("alpinisme et ran") != -1:
        classification.extend(["Marchandises", "Lecomte"])
        num_classifications += 1
    if features.find("brico") != -1:
        classification.extend(["Marchandises", "Brico"])
        num_classifications += 1
    if features.find("decathlon") != -1:
        classification.extend(["Marchandises", "Decathlon"])
        num_classifications += 1
    if features.find("media markt") != -1:
        classification.extend(["Marchandises", "Media Markt"])
        num_classifications += 1
    if features.find("ikea") != -1:
        classification.extend(["Marchandises", "Ikea"])
        num_classifications += 1
    if features.find("agripp") != -1 or features.find("bavaria holds") != -1 or features.find("rokodromo") != -1:
        classification.extend(["Marchandises", "Prises"])
        num_classifications += 1
    if features.find("apple") != -1:
        classification.extend(["Marchandises", "Apple"])
        num_classifications += 1
    if (features.find("carburant") != -1 or
            features.find("ESSO") != -1 or
            features.find("TEXACO") != -1 or
            features.find("Q8") != -1 or
            features.find("Shell") != -1 or
            features.find("LUKOIL") != -1 or
            features.find("OCTA") != -1):
        classification.extend(["Marchandises", "Carburant"])
        num_classifications += 1

    # Remboursements
    if features.find("remboursement") != -1:
        classification.extend(["Remboursements"])
        num_classifications += 1

    # Mastercard
    if features.find("mastercard") != -1:
        classification.extend(["Mastercard"])
        num_classifications += 1

    # Autres salles
    if (features.find("agb puurs vrijha") != -1 or
            features.find("complexe sportif - louvain-la") != -1 or
            features.find("petite ile scrl") != -1 or
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
            features.find("terres verticale") != -1 or
            features.find("arkose") != -1 or
            features.find("gemeente puurs") != -1 or
            features.find("blackbox") != -1 or
            features.find("boulderhal breda") != -1 or
            features.find("ecole d'escalade") != -1):
        classification.extend(["Entrées salles"])
        num_classifications += 1

    # Check that the classification is correct
    assert num_classifications >= 0
    if num_classifications == 0:
        classification.extend(["Autre dépenses"])
    elif num_classifications > 1:
        classification = manually_classify(amount, features, transaction_type="expense")

    # Validate the classification and return
    assert classification in EXPENSE_CLASSES, "{}".format(classification)
    return ", ".join(classification)


def classify_income(data_row: pd.Series) -> str:
    """ Classifies all incomes. """
    # Define some variables which can be used to determine the classification of the current row
    features = (data_row["Omschrijving"] + " " + data_row["Detail van de omzet"] + " " + data_row["Bericht"]).lower()
    amount = str(data_row["Bedrag"])
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
    if features.find("boissons") != -1:
        classification.extend(["Consumations"])
        num_classifications += 1

    # Cours
    crs_rexes = re.findall(r"t2017\d+", features) + re.findall(r"t2018\d+", features) + \
        re.findall(r"t2019\d+", features) + re.findall(r"t2020\d+", features) + \
        re.findall(r"t2021\d+", features) + re.findall(r"t2022\d+", features) + \
        re.findall(r"t2021\d+", features) + re.findall(r"t2021\d+", features) + \
        re.findall(r"communication : t\d+\s", features)
    if len(crs_rexes) > 0 or \
            features.find("2017t3") != -1 or \
            features.find("2018t1") != -1 or \
            features.find("2018t2") != -1 or \
            features.find("2018t3") != -1 or \
            features.find("t2021-") != -1:
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
        classification = manually_classify(amount, features, transaction_type="income")

    # Validate the classification and return
    assert classification in INCOME_CLASSES
    return ", ".join(classification)


if __name__ == "__main__":
    # Define where to find the data
    input_csv = r"/Users/jeremy/Library/Mobile Documents/com~apple~CloudDocs/BMC/Comptabilité/Bilans/2021/363-0989738-87 ZR (EUR) 20200101 - 20211231.csv"
    main(input_csv)
