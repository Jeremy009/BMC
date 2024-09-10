import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog


class GuiSelector:
    def __init__(self):
        self.__root = tk.Tk()
        self.__root.withdraw()

    def get_file_path(self):
        title = "Welcome"
        msg = "You'll have to select the csv input file_path.\n Click \"Ok\" to continue."
        csv_path = self.__ask_csv_path(title, msg)
        return csv_path

    def get_folder_path(self):
        title = "Finished !"
        msg = "You'll have to select the output folder.\n Click \"Ok\" to continue."
        folder_path = self.__ask_folder_path(title, msg)
        return folder_path

    @staticmethod
    def __ask_csv_path(title, msg):
        messagebox.showinfo(title, msg)
        path = filedialog.askopenfilename(filetypes=[('.csvfiles', '.csv')])
        return path

    @staticmethod
    def __ask_folder_path(title, msg):
        messagebox.showinfo(title, msg)
        path = filedialog.askdirectory()
        return path
