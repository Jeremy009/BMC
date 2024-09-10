import datetime
import sqlite3
from dateutil.relativedelta import relativedelta
from apps.register.abonnements import BMCClient, BMCAboDBInterfacer, BMCAbonnement

# Connection to the old db and new db
legacy_connection = sqlite3.connect("/Applications/BMCRegistry/legacy.db")
interfacer = BMCAboDBInterfacer("/Applications/BMCRegistry/prod.db")

# Wipe the whole new db
with interfacer.connect_to_db() as connection:
    cursor = connection.cursor()
    cursor.execute("DELETE FROM abonnement")
    cursor.execute("DELETE FROM client")

# Connect to the old db
with legacy_connection as connection:
    no_errors = True
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Abonnements")
    results = cursor.fetchall()
    interfacer = BMCAboDBInterfacer("/Applications/BMCRegistry/prod.db")

    # For every entry in the old db try to make a client in the new db
    for res in results:
        lname = res[0]
        fname = res[1]
        client = BMCClient(first_name=fname, last_name=lname)
        try:
            interfacer.create_client(client)
        except Exception as e:
            print(e)
            no_errors = False

    # If everything went smoothly try to make for every row a new abonnement, regardless off if it is still valid
    if no_errors:
        for res in results:
            lname = res[0].upper()
            fname = res[1].title()
            abo_type = res[3]
            buy_date = datetime.datetime.strptime(res[4], "%Y-%m-%d").date()
            gear_included = bool(res[6])
            end_date = buy_date + relativedelta(months=+3) + relativedelta(days=-1) if abo_type == "3M" else None
            entrances_remaining = int(res[5]) if abo_type == "C10S" else None

            try:
                client = interfacer.find_client_from_name(last_name=lname, first_name=fname)
                new_abo = BMCAbonnement(owner=client, abo_type=abo_type, buy_date=buy_date, db_id=None,
                 include_gear=gear_included, end_date=end_date, entrances_remaining=entrances_remaining)
                interfacer.create_abonnement(new_abo)

            except Exception as e:
                print(e)
                print(lname)
                print(fname)


