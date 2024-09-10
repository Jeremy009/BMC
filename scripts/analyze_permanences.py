import csv
from datetime import date
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = Path(r"/Users/jeremylombaerts/Library/CloudStorage/Dropbox/BMCRegistry/accountancy/2022")


def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        offset = 0 if height > 0 else -12
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, offset),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def main():
    for month_dir in DATA_DIR.iterdir():
        if month_dir.is_dir():
            perms = {
                "Dates": [],
                "Jours": [],
                "Permanents": [],
                "Erreurs caisse": [],
                "Rentrées": [],
                "Nom. clients": []
            }
            for perm_file in month_dir.iterdir():
                if perm_file.is_file() and perm_file.suffix == ".csv":
                    perm_date, jour, permanent, erreur_caisse, nom_clients = None, None, None, None, None
                    rentrees = 0.0
                    total_rentrees = 0.0
                    with open(str(perm_file)) as csvfile:
                        csv_reader = csv.reader(csvfile, delimiter=';')
                        for i, row in enumerate(csv_reader):
                            if i == 0:
                                jour = str(row[1])
                            if i == 1:
                                perm_date = date(year=int(row[1].split("/")[2]),
                                                 month=int(row[1].split("/")[1]),
                                                 day=int(row[1].split("/")[0]))
                            if i == 2:
                                permanent = str(row[1])
                            if i == 4:
                                erreur_caisse = round(float(row[1]), 2)
                            if row[0] == "# de clients":
                                nom_clients = int(row[1])
                            if len(row) == 4:
                                value = float(row[3])
                                if value > 0.0:
                                    rentrees += value
                                elif value < 0.0:
                                    print(str(perm_date) + " " + str(permanent) + " : " + str(row[1]) + " (" + str(row[3]) + "€): Accept (y/n)? ", end="")
                                    while True:
                                        resp = input()
                                        if resp.lower() == "y":
                                            rentrees += value
                                            break
                                        elif resp.lower() == "n":
                                            break
                            if row[0] == "Total rentrées":
                                total_rentrees = round(float(row[1]), 2)
                            if str(row).lower().find("vente") != -1:
                                print(str(perm_date), " - ", str(row[1]))
                        if rentrees != total_rentrees:
                            print("Rentrées = {}, total rentrees = {}".format(rentrees, total_rentrees))
                            print()
                    assert jour is not None and perm_date is not None and permanent is not None and erreur_caisse is not None
                    assert rentrees is not None and nom_clients is not None

                    if perm_date not in perms["Dates"]:
                        perms["Dates"].append(perm_date)
                        perms["Jours"].append(jour)
                        perms["Permanents"].append(permanent)
                        perms["Erreurs caisse"].append(erreur_caisse)
                        perms["Rentrées"].append(rentrees)
                        perms["Nom. clients"].append(nom_clients)
                    else:
                        ind = perms["Dates"].index(perm_date)
                        perms["Permanents"][ind] += " et " + permanent
                        perms["Erreurs caisse"][ind] += erreur_caisse
                        perms["Rentrées"][ind] += rentrees
                        perms["Nom. clients"][ind] += nom_clients

            # Sort the data
            sorted_dates = perms["Dates"].copy()
            sorted_dates.sort()
            sorted_inds = [perms["Dates"].index(sorted_date) for sorted_date in sorted_dates]

            perms["Dates"] = [perms["Dates"][sorted_ind] for sorted_ind in sorted_inds]
            perms["Jours"] = [perms["Jours"][sorted_ind] for sorted_ind in sorted_inds]
            perms["Permanents"] = [perms["Permanents"][sorted_ind] for sorted_ind in sorted_inds]
            perms["Erreurs caisse"] = [perms["Erreurs caisse"][sorted_ind] for sorted_ind in sorted_inds]
            perms["Rentrées"] = [perms["Rentrées"][sorted_ind] for sorted_ind in sorted_inds]
            perms["Nom. clients"] = [perms["Nom. clients"][sorted_ind] for sorted_ind in sorted_inds]

            # Compute some metrics
            rentrees_totale = sum(perms["Rentrées"])
            rentrees_moyenne = np.average(perms["Rentrées"])
            clients_totale = sum(perms["Nom. clients"])
            clients_moyenne = np.average(perms["Nom. clients"])
            erreur_caisse_totale = sum(perms["Erreurs caisse"])

            # Refine the data for visualization
            x_ticks = [i for i in range(len(perms["Dates"]))]
            x_labels = [j[:3] + " " + str(d) + "\n" + p for j, d, p in
                        zip(perms["Jours"], perms["Dates"], perms["Permanents"])]
            y_rentrees = [int(r) for r in perms["Rentrées"]]
            y_clients = perms["Nom. clients"]
            y_err_caisse = [int(r) for r in perms["Erreurs caisse"]]

            # Render
            fig, ax = plt.subplots(figsize=(2 * 11.69, 1 * 8.27))
            x = np.arange(len(x_labels))  # the label locations
            width = 0.25  # the width of the bars

            ax.plot([-1, len(x_labels)], [rentrees_moyenne, rentrees_moyenne], "--", color="C0", zorder=0)
            ax.plot([-1, len(x_labels)], [clients_moyenne, clients_moyenne], "--", color="C1", zorder=1)
            ax.plot([-1, len(x_labels)], [0, 0], "k", zorder=10)
            ax.text(-1, rentrees_moyenne + 5, "$\mu$: €{:.2f}".format(round(rentrees_moyenne, 2)))
            ax.text(-1, clients_moyenne + 5, "$\mu$: {}".format(round(clients_moyenne, 1)))

            rects1 = ax.bar(x - width, y_rentrees, width, label='Rentrées: €{:.2f}'.format(round(rentrees_totale, 2)),
                            zorder=2)
            rects2 = ax.bar(x, y_clients, width, label='Nombre de clients: {}'.format(clients_totale), zorder=3)
            rects3 = ax.bar(x + width, y_err_caisse, width,
                            label='Erreurs caisse: €{:.2f}'.format(round(erreur_caisse_totale, 2)), zorder=3,
                            color="C3")

            ax.set_title('Analyse des permanences de {} {}'.format(month_dir.name, month_dir.parent.name))
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels)
            plt.xticks(rotation=90)
            ax.legend(loc="upper left")

            autolabel(rects1, ax)
            autolabel(rects2, ax)
            autolabel(rects3, ax)

            fig.tight_layout()
            plt.savefig(str(month_dir.joinpath("Analyze.pdf")), format='pdf')
            plt.cla()
            plt.clf()
            plt.close()


if __name__ == "__main__":
    main()
