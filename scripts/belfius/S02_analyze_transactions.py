import pandas as pd
from S01_process_transactions import EXPENSE_CLASSES, INCOME_CLASSES
import numpy as np

INPUT_PATH = r"/Users/jlb5pbf/Library/CloudStorage/GoogleDrive-jeremy@brusselsmonkeysclimbing.com/My Drive/BMC/BMC-Protected/Comptabilité/2023/Comptabilite/extraits/classified {}.xlsx"
BEGIN_BALANCE = 52298.30
END_BALANCE = 51441.35

DECIMAL_POINT_IN_OUTPUT = ","


def deep_dive_analysis_of_expenses(input_path):
    df = pd.read_excel(input_path.format("expenses"))
    for tt in ["Remunerations", "Services", "Marchandises"]:
        rows_indices = [' '.join(i).replace(tt + " ", "") for i in EXPENSE_CLASSES if ' '.join(i).find(tt) != -1]
        nf = pd.DataFrame([[0.] for _ in rows_indices], columns=["Montant"])
        nf.index = rows_indices

        for index, row in df.iterrows():
            cat = row["Categorie"]
            if cat.find(tt) != -1:
                index = ' '.join(cat.split(", ")).replace(tt + " ", "")
                nf.at[index, "Montant"] += abs(row["Montant"])
                nf = nf.sort_values(by=['Montant'], ascending=True)
        nf.loc['Total'] = nf.sum(numeric_only=True, axis=0)
        nf.to_excel(f"{tt.lower()}.xlsx", index=True)

        print("------- {} -------".format(tt))
        print(nf.to_string(decimal=DECIMAL_POINT_IN_OUTPUT))
        print()
        print()


def main(input_path: str, account_balance_begin: float, account_balance_end: float, year: int) -> None:
    # Define some variables
    num_transactions = 0
    in_frame, out_frame = None, None

    # Analyse income and expenses separately
    for transactions_type in ["incomes", "expenses"]:
        # Create the summarizing dataframe
        classes = EXPENSE_CLASSES if transactions_type == "expenses" else INCOME_CLASSES
        rows_indices = list(set([c[0] for c in classes]))
        cols = ['{}Q1'.format(year), '{}Q2'.format(year), '{}Q3'.format(year), '{}Q4'.format(year)]
        nf = pd.DataFrame([[0., 0., 0., 0.] for _ in rows_indices], columns=cols)
        nf.index = rows_indices

        # Read the excel and add to the summarizing dataframe
        df = pd.read_excel(input_path.format(transactions_type))
        for index, row in df.iterrows():
            num_transactions += 1
            cat = row["Categorie"].split(",")[0]
            nf.at[cat, row["Periode"]] += abs(row["Montant"])

        # Add total column and row
        nf.loc[:, 'Total par catégorie'] = nf.sum(numeric_only=True, axis=1)
        nf = nf.sort_values(by=['Total par catégorie'], ascending=False)
        nf.loc['Total par periode'] = nf.sum(numeric_only=True, axis=0)

        # Save the new frame
        if transactions_type == "incomes":
            in_frame = nf
        else:
            out_frame = nf
        nf.to_excel(f"{transactions_type}.xlsx", index=True)

    # Summarize
    total_in = in_frame.loc['Total par periode', 'Total par catégorie']
    total_out = out_frame.loc['Total par periode', 'Total par catégorie']
    print("Effectif début : {} €".format(np.round(account_balance_begin, 2)))
    print("Chiffre d'affaire : {} €".format(np.round(total_in, 2)))
    print("Dépenses : {} €".format(np.round(total_out, 2)))
    print("Effectif fin (calculé) : {} €".format(np.round(account_balance_begin + total_in - total_out, 2)))
    print("Effectif fin (observé) : {} €".format(np.round(account_balance_end, 2)))
    print()
    print("Bénéfice net : {} €".format(np.round(total_in-total_out, 2)))

    print()
    print()
    print("-------------------------------- Rentrées --------------------------------")
    print(in_frame.to_string(decimal=DECIMAL_POINT_IN_OUTPUT))

    print()
    print()
    print("-------------------------------- Dépenses --------------------------------")
    print(out_frame.to_string(decimal=DECIMAL_POINT_IN_OUTPUT))

    # Checks
    print()
    print()
    diff = account_balance_begin + total_in - total_out - account_balance_end
    assert diff <= 0.01, diff

    deep_dive_analysis_of_expenses(input_path)


if __name__ == "__main__":
    main(INPUT_PATH, BEGIN_BALANCE, END_BALANCE, 2023)
