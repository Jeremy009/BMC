from apps.autocountancy.gui_selector import GuiSelector
from apps.autocountancy.csv_parser import CsvParser
from apps.autocountancy.report_builder import ReportBuilder

if __name__ == "__main__":
    selector = GuiSelector()
    # input_csv_path = selector.get_file_path()
    input_csv_path = r"/Users/jeremy/Desktop/363-0989738-87 CA (EUR) 20190101 - 20191101.csv"
    parser = CsvParser(input_csv_path)
    expense = parser.get_expense()
    income = parser.get_income()
    path = selector.get_folder_path()
    report = ReportBuilder(income, expense, path)
