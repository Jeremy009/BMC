import pandas
import io


class CsvBuilder:

    def __init__(self):
        expense_categories = self.parse_expense_categories()
        income_categories = self.parse_income_categories()
        self.expense_data = {i.strip(): None for i in expense_categories}
        self.income_data = {i.strip(): None for i in income_categories}

    @staticmethod
    def parse_expense_categories():
        expense_categories = []
        my_file = open("categories.txt")
        for line in my_file:
            if line != "\n":
                line = line.lower().split(',')
                for word in line:
                    expense_categories.append(word.replace("\n", "").lower())
            else:
                break
        my_file.close()
        return expense_categories

    def get_income_categories(self):
        return self.income_data.keys()

    def get_expense_categories(self):
        return self.expense_data.keys()

    @staticmethod
    def parse_income_categories():
        income_categories = []
        my_file = open("categories.txt")
        flag = False
        for line in my_file:
            if line != "\n":
                if flag:
                    line = line.lower().split(',')
                    for word in line:
                        income_categories.append(word.replace("\n", "").lower())
            else:
                flag = True
        my_file.close()
        return income_categories
