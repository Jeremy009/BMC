import pandas as pd


# READ ME
""" A small script which parses the most recent and previous version of the affiliations csv file_path. These files
contain all the information of BMC members which have/request a CAB membership. The outputs should be 2 files:
- to_sync.csv: a csv containing all the strictly new members to send to the CAB
- to_update.csv: a csv containing all the members which should already be send to CAB, but which have updated info
"""


def main(old_csv: str, new_csv: str, to_sync_csv: str, to_update_csv: str, write: bool = False):
    # Read in old and current file_path
    old_frame = pd.read_csv(old_csv, delimiter=";", converters={'Téléphone': lambda x: str(x)})
    new_frame = pd.read_csv(new_csv, delimiter=";", converters={'Téléphone': lambda x: str(x)})
    print("Number of previously affiliations:", len(old_frame))
    print("Number of new affiliations:", len(new_frame))
    print()

    # Filter out any unpaid affiliations
    old_paid = old_frame[old_frame['Payement ok']].sort_values(by=['Prénom']).sort_values(by=['Nom'])
    print("Number of previously paid affiliations:", len(old_paid))
    new_paid = new_frame[new_frame['Payement ok']].sort_values(by=['Prénom']).sort_values(by=['Nom'])
    print("Number of currently paid affiliations:", len(new_paid))

    # Get rows whose id's are in new but not old frame (should be number of new - number of old)
    strictly_new = new_paid.loc[~new_paid['id'].isin(old_paid['id'])]
    if write:
        strictly_new.to_csv(path_or_buf=to_sync_csv, sep=";")
    print("Number of strictly new affiliations:", len(strictly_new))

    # Get rows whose id's are in old but not new frame (should be 0)
    strictly_old = old_paid.loc[~old_paid['id'].isin(new_paid['id'])]
    print("Number of strictly old affiliations:", len(strictly_old))
    print()

    # Filter the frames to only contain rows whose id is in both frames.
    new_with_common_id = new_paid.loc[new_paid['id'].isin(old_paid['id'])].reset_index(drop=True)
    old_with_common_id = old_paid.loc[old_paid['id'].isin(new_paid['id'])].reset_index(drop=True)
    new_with_common_id = new_with_common_id.astype(str).sort_values(by=['Prénom']).sort_values(by=['Nom'])
    old_with_common_id = old_with_common_id.astype(str).sort_values(by=['Prénom']).sort_values(by=['Nom'])
    print("Number of common affiliations:", len(old_with_common_id))

    # Get the inner join of the common id frames to find the rows which remain unchanged
    header_wo_begin_date = ['Nom', 'Prénom', 'Date de naissance', 'Genre', 'Téléphone', 'Email', 'Nationalité', 'Rue',
                            'Boite', 'Code postal', 'Ville', 'Pays', 'Type de renouvellement', "Type d'affiliation",
                            'Code transaction', 'Payement ok', 'Payement annulé', 'id']  # To exclude the begin date...
    joined = pd.merge(new_with_common_id, old_with_common_id, on=header_wo_begin_date, how="inner")
    print("Number of unchanged affiliations:", len(joined))

    # Get the left anti outer join of the common id frames to find the rows which were updated
    updated = pd.merge(new_with_common_id, old_with_common_id, on=header_wo_begin_date, how="left")
    updated = updated[~updated.isin(joined)].dropna()
    if write:
        updated.to_csv(path_or_buf=to_update_csv, sep=";")
    print("Number of updated affiliations:", len(updated))

    # Get the right anti outer join of the common id frames to find the rows which appear in old but not new should be 0
    erronous = pd.merge(new_with_common_id, old_with_common_id, on=header_wo_begin_date, how="right")
    erronous = erronous[~erronous.isin(joined)].dropna()
    print("Number of erronous affiliations:", len(erronous))

    # Perform some sanity checks
    print()
    print("Check 1:", len(strictly_new) == len(new_paid) - len(old_paid))
    print("Check 2:", len(new_paid) == len(strictly_new) + len(new_with_common_id))
    print("Check 3:", len(old_paid) == len(strictly_old) + len(old_with_common_id))
    print("Check 4:", len(new_with_common_id) == len(old_with_common_id) == len(old_paid))
    print("Check 5:", len(new_with_common_id) == len(joined) + len(updated) + len(erronous))
    print("Check 6:", len(strictly_old) + len(strictly_new) + len(joined) + len(updated) + len(erronous)
          == len(new_paid))


if __name__ == "__main__":
    # The csv with the previous iteration of affiliations
    path_to_old_csv = "/Users/jeremy/Library/Mobile Documents/com~apple~CloudDocs/BMC/CAB/Affiliations BMC/2021:11:22 " \
                      "synced affiliations.csv"

    # The csv with the current iteration of affiliations
    path_to_new_csv = "/Users/jeremy/Library/Mobile Documents/com~apple~CloudDocs/BMC/CAB/Affiliations BMC/2022:05:17 " \
                      "synced affiliations.csv"

    # The path to where to save the affiliations to send to cab
    path_to_to_sync_csv = "/Users/jeremy/Desktop/to_sync.csv"

    # The path to where to save the affiliations that are already send to cab, but which have new or updated info
    path_to_to_update_csv = "/Users/jeremy/Desktop/to_update.csv"

    main(path_to_old_csv, path_to_new_csv, path_to_to_sync_csv, path_to_to_update_csv, write=True)
