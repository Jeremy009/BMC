import copy

import pandas as pd

from apps.autocountancy.csv_builder import CsvBuilder

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def refine_hardcoded(mystring: str):
    mystring = str(mystring)
    mystring = mystring.replace("Virement en euros", "")
    mystring = mystring.replace("De:", "")
    mystring = mystring.replace("nan", "")
    mystring = mystring.replace("(SEPA)", "")

    if mystring.find("GR") != -1 and mystring.find("BANCONTACT"):
        mystring = "Bancontact"

    mystring = ' '.join(str(mystring).split())
    
    return mystring


class CsvParser:
    DROPPABLE_LABELS = ["Rekeningnummer", "Naam van de rekening", "Omzetnummer", "Valutadatum", "Munteenheid"]

    def __init__(self, csv):
        self.builder = CsvBuilder()
        self.frame = pd.read_csv(csv, delimiter=";", encoding='UTF-8')
        self.income = {}
        self.expense = {}
        self.run()

    def run(self):
        self.refine()
        expense_categories = self.builder.get_expense_categories()
        expanded_expense_dict = self.expand_categories(expense_categories)
        income_categories = self.builder.get_income_categories()
        expanded_income_dict = self.expand_categories(income_categories)
        for category in expense_categories:
            self.expense[category] = []
        for category in income_categories:
            self.income[category] = []
        self.parse(expanded_expense_dict, False)
        self.parse(expanded_income_dict, True)

    def parse(self, categories_dict, income):
        blacklist = []
        for category in categories_dict.keys():
            for typo in categories_dict[category]:
                sub_frame = self.find_rows_ids(typo, income)
                for index, row in sub_frame.iterrows():
                    if index not in blacklist:
                        if income:
                            self.income[category].append(row["Bedrag"])
                        else:
                            self.expense[category].append(row["Bedrag"])
                        blacklist.append(index)
        self.list_unknown(blacklist)  # ajouter la différentiation entre les rentrées et les sorties dans cette func

    def list_unknown(self, blacklist):
        self.income["Unknown"] = []
        self.expense["Unknown"] = []
        for index, row in self.frame.iterrows():
            if index not in blacklist and type(row["Bedrag"]) == str:
                if "-" in row["Bedrag"]:
                    self.expense["Unknown"].append(row["Bedrag"])
                else:
                    self.income["Unknown"].append(row["Bedrag"])

    def refine(self):
        # Get rig of rows which have 0 value
        to_delete_indexes = self.frame[self.frame["Bedrag"] == "0,00"].index
        self.frame.drop(to_delete_indexes, inplace=True)

        # Get rid of rows which have nan value
        self.frame["Bedrag"] = self.frame["Bedrag"].apply(lambda s: str(s))
        to_delete_indexes = self.frame[self.frame["Bedrag"] == "nan"].index
        self.frame.drop(to_delete_indexes, inplace=True)

        # Get rid of columns we're not interested in
        self.frame.drop(CsvParser.DROPPABLE_LABELS, 1, inplace=True)

        # # Preprocess other columns and merge communications, details, messages etc.
        self.frame["Omschrijving"] = self.frame["Omschrijving"].apply(lambda s: ' '.join(str(s).split()))
        self.frame["Detail van de omzet"] = self.frame["Detail van de omzet"].apply(lambda s: ' '.join(str(s).split()))
        self.frame["Bericht"] = self.frame["Bericht"].apply(lambda s: ' '.join(str(s).split()))
        self.frame["Features"] = self.frame["Omschrijving"] + " " + self.frame["Detail van de omzet"] + " " + self.frame["Bericht"]

        # Strong manual preprocessing
        self.frame["Features"] = self.frame["Features"].apply(refine_hardcoded)

        self.frame = self.frame[['Rekening tegenpartij', 'Boekingsdatum', 'Bedrag', 'Features', 'Omschrijving', "Detail van de omzet", "Bericht"]]

    def find_rows_ids(self, category, income):
        selected_frame = self.frame[self.frame["Features"].str.contains(("(?i)" + category).lower())]
        if income:
            refined_frame = selected_frame[~selected_frame["Bedrag"].str.contains("-")]
        else:
            refined_frame = selected_frame[selected_frame["Bedrag"].str.contains("-")]
        return refined_frame

    def expand_categories(self, categories):
        """
        result = {i: None for i in categories}
        for word in categories:
            cat = [word]
            for i in self.create_forgot_letter(word):
                cat.append(i)
            for i in self.create_add_letter(word):
                cat.append(i)
            for i in self.create_anagram(word):
                cat.append(i)
            cat = list(set(cat))
            result[word] = copy.copy(cat)
        return result
        """
        return {i: [i] for i in categories}

    @staticmethod
    def create_forgot_letter(word):
        result = []
        for letter in range(len(word) - 1):
            new_word = word[:letter] + word[letter + 1:]
            result.append(new_word)
        return result

    @staticmethod
    def create_add_letter(word):
        result = []
        for letter in range(len(word) - 1):
            new_word = word[:letter] + word[letter] + word[letter:]
            result.append(new_word)
        return result

    @staticmethod
    def create_anagram(word):
        result = []
        for letter_a in range(len(word) - 2):
            for letter_b in range(letter_a + 1, len(word) - 1):
                new_word = word[:letter_a] + word[letter_b] + word[letter_a + 1:letter_b] + word[letter_a] + word[
                                                                                                             letter_b + 1:]
                result.append(new_word)
        return result

    def get_expense(self):
        return copy.deepcopy(self.expense)

    def get_income(self):
        return copy.deepcopy(self.income)
