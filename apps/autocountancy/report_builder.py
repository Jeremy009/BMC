import pandas as pd

class ReportBuilder:

    def __init__(self, income, expense, path):
        total_income = self.calculate_total(income)
        total_expense = self.calculate_total(expense)
        self.create_csv(total_income,income,path+"/income.csv")
        self.create_csv(total_expense,expense,path+"/expense.csv")

    def calculate_total(self,listing):
        result = 0
        for category in listing:
            for transaction in listing[category]:
                result+=float(transaction.replace(",","."))
        return result

    def create_csv(self, total, serie, path):
        serie["value"] = [str(total)]
        max_key = max(serie, key=lambda x: len(set(serie[x])))
        for cat in serie:
            while len(serie[cat]) < len(serie[max_key]):
                serie[cat].append("")
        df = pd.DataFrame(serie, columns=serie.keys())
        new_file = open(path,"w+")
        df.to_csv(path)
        new_file.close()
