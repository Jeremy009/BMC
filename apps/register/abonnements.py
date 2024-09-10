import datetime
import sqlite3
from pathlib import Path
from typing import List, Tuple

from dateutil.relativedelta import relativedelta


class BMCClient:
    """ The BMCCLient class is used to represent a client. Clients can be read from, and written to our database using
    the db interface class. """

    def __init__(self, first_name: str, last_name: str, db_id: int or None = None, reduced_price: bool = False,
                 email: str = None, phone: str = None, date_of_birth: datetime.date or str = None, sex: str = None,
                 street_name: str = None, street_number: str = None, city_zip: int = None, city_name: str = None,
                 country: str = None):
        """ Create a new client object. For a client to be valid it must at least have a first and last name. Other
        fields can have a default or None value and must not neccesrily be set. Some input formatting is performed
        automatically.

        """
        # Input validation
        if not first_name or not last_name:
            raise ValueError("First name and last name must be provided")

        # Set and format fields
        self.db_id = db_id
        self.first_name = first_name.title()
        self.last_name = last_name.upper()
        self.reduced_price = reduced_price
        self.email = email
        self.phone = phone
        self.date_of_birth = date_of_birth
        self.sex = sex.upper() if sex else None
        self.street_name = street_name.lower().capitalize() if street_name else None
        self.street_number = street_number
        self.city_zip = city_zip
        self.city_name = city_name.lower().capitalize() if city_name else None
        self.country = country.lower().capitalize() if country else None

    @property
    def date_of_birth(self):
        return self.__date_of_birth

    @date_of_birth.setter
    def date_of_birth(self, date_of_birth: datetime.date or None):
        if isinstance(date_of_birth, datetime.date) or date_of_birth is None:
            self.__date_of_birth = date_of_birth

    def __str__(self):
        msg = ""
        msg += "BMCClient {}: {} {}\n".format(self.db_id, self.first_name, self.last_name)
        msg += "    red. price: {}\n".format("yes" if self.reduced_price else "no")
        msg += "    email: {}\n".format(self.email)
        msg += "    phone: {}\n".format(self.phone)
        msg += "    date of b.: {}\n".format(self.date_of_birth)
        msg += "    sex: {}\n".format(self.sex)
        msg += "    address: {} {}, {} {}, {}\n".format(self.street_name, self.street_number, self.city_zip,
                                                      self.city_name, self.country)
        return msg


class BMCAbonnement:
    """ The BMCAbonnement class is used to represent an abonnement. These can be read from, and written to our
    database using the db interface class. """

    def __init__(self, owner: BMCClient, abo_type: str, buy_date: datetime.date, db_id: int or None = None,
                 include_gear: bool = False, end_date: datetime.date = None, entrances_remaining: int = None):
        """ Create a new abonnement object. Since an abonnement can not exist on its own it must neccesarily have an
        owner which is a BMCClient object. """
        self.db_id = db_id
        self.owner = owner
        self.abo_type = abo_type.upper()
        self.buy_date = buy_date
        self.include_gear = include_gear
        self.end_date = end_date
        self.entrances_remaining = entrances_remaining

    @property
    def buy_date(self):
        return self.__buy_date

    @buy_date.setter
    def buy_date(self, buy_date: datetime.date):
        if isinstance(buy_date, datetime.date):
            self.__buy_date = buy_date

    @property
    def end_date(self):
        return self.__end_date

    @end_date.setter
    def end_date(self, end_date: datetime.date):
        if isinstance(end_date, datetime.date) or end_date is None:
            self.__end_date = end_date

    @property
    def is_valid(self):
        if self.abo_type == "C10S" and self.entrances_remaining > 0:
            return True
        elif self.abo_type == "3M" and self.end_date >= datetime.date.today():
            return True
        return False

    def __str__(self):
        msg = ""
        msg += "Abo {}:\n".format(self.db_id)
        msg += "    type: {}\n".format(self.abo_type)
        msg += "    buy date: {}\n".format(self.buy_date)
        msg += "    end date: {}\n".format(self.end_date)
        msg += "    gear is included: {}\n".format("yes" if self.include_gear else "no")
        msg += "    num. entrances left: {}\n".format(self.entrances_remaining)
        msg += "    is still valid: {}\n".format(self.is_valid)

        return msg


class BMCAboDBInterfacer:
    """ The BMCAbonnement class is used to represent an abonnement. These can be read from, and written to our
    database using the db interface class. """

    def __init__(self, path_to_db: Path or str):
        """ Interface class to bridge python to the abonnements sqlite database. """
        self.path_to_db = path_to_db

    def connect_to_db(self) -> sqlite3.Connection:
        """ Open the connection to the db. """
        return sqlite3.connect(self.path_to_db)

    # Create
    def create_client(self, client: BMCClient) -> None:
        """ Create a new client entry in the database. """
        with self.connect_to_db() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO client VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (None,
                            client.first_name,
                            client.last_name,
                            client.reduced_price,
                            client.email,
                            client.phone,
                            client.date_of_birth,
                            client.sex,
                            client.street_name,
                            client.street_number,
                            client.city_zip,
                            client.city_name, client.country))

    def create_abonnement(self, abonnement: BMCAbonnement) -> None:
        """ Create a new abonnement in the database. """
        with self.connect_to_db() as connection:
            owner_id = self.get_client_id(abonnement.owner)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO abonnement VALUES(?, ?, ?, ?, ?, ?, ?)",
                           (None,
                            owner_id,
                            abonnement.abo_type,
                            abonnement.include_gear,
                            abonnement.buy_date,
                            abonnement.end_date,
                            abonnement.entrances_remaining))

    # Read
    def find_client_from_id(self, client_id: int) -> BMCClient or None:
        """ Query the database to find a client whose (unique) client_id matches the provided client_id. """
        with self.connect_to_db() as connection:
            # Execute the query and convert results to python objects
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM client WHERE ID == ?", (client_id,))
            sql_clients = cursor.fetchall()
            if len(sql_clients) == 0:
                return None
            elif len(sql_clients) == 1:
                return self.convert_sql_client_to_python_client(sql_clients[0])
            else:
                raise IOError("Found multiple matches for given first_name last_name combination")

    def find_client_from_name(self, first_name: str, last_name: str) -> BMCClient or None:
        """ The first_name last_name combination is unique by design in the database. Searches the matching client
        provided a first_name and a last_name. """
        with self.connect_to_db() as connection:
            querry = ("SELECT * FROM client "
                      "WHERE first_name == '" + first_name + "' AND " 
                      "last_name == '" + last_name + "'")

            # Execute the query and convert results to python objects
            cursor = connection.cursor()
            cursor.execute(querry)
            sql_clients = cursor.fetchall()
            if len(sql_clients) == 0:
                return None
            elif len(sql_clients) == 1:
                return self.convert_sql_client_to_python_client(sql_clients[0])
            else:
                raise IOError("Found multiple matches for given first_name last_name combination")

    def find_clients_from_namepart(self, name_part: str, first_or_last: str) -> List[BMCClient]:
        """ Query the database to find clients whose names match the provided pattern. Possible to query on
         first name or on last name by setting 'first_or_last' to respectively 'first' or 'last'. Results are returned
         in alphabetical order. """
        with self.connect_to_db() as connection:
            # Determine whether to query on first name or last name
            if first_or_last == "first":
                querry = ("SELECT * FROM client "
                          "WHERE first_name LIKE '" + name_part + "%' "
                          "ORDER BY first_name ASC, last_name ASC")
            elif first_or_last == "last":
                querry = ("SELECT * FROM client "
                          "WHERE last_name LIKE '" + name_part + "%' "
                          "ORDER BY last_name ASC, first_name ASC")
            else:
                raise ValueError("first_or_last must be either 'first' or 'last'")

            # Execute the query and convert results to python objects
            cursor = connection.cursor()
            cursor.execute(querry)
            sql_clients = cursor.fetchall()
            python_clients = []
            for sql_client in sql_clients:
                python_clients.append(self.convert_sql_client_to_python_client(sql_client))

            return python_clients

    # Update
    def update_client(self, client: BMCClient) -> None:
        """ Updates all the information in a client entry. """
        with self.connect_to_db() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE client "
                           "SET first_name=?,"
                           "last_name=?,"
                           "reduced=?,"
                           "email=?,"
                           "phone=?,"
                           "date_of_birth=?,"
                           "sex=?,"
                           "street_name=?,"
                           "street_number=?,"
                           "city_zip=?,"
                           "city_name=?, "
                           "country=?"
                           "WHERE id=?",
                           (client.first_name, client.last_name, client.reduced_price, client.email, client.phone,
                           client.date_of_birth, client.sex, client.street_name, client.street_number, client.city_zip,
                           client.city_name, client.country, client.db_id))

    def update_abonnement(self, abonnement: BMCAbonnement) -> None:
        """ Updates all the information in a client entry. """
        with self.connect_to_db() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE abonnement "
                           "SET client_id=?,"
                           "abo_type=?,"
                           "include_gear=?,"
                           "buy_date=?,"
                           "end_date=?,"
                           "entrances_remaining=?"
                           "WHERE id=?",
                           (abonnement.owner.db_id, abonnement.abo_type, abonnement.include_gear, abonnement.buy_date,
                            abonnement.end_date, abonnement.entrances_remaining, abonnement.db_id))

    # Delete
    def delete_abonnement(self, abonnement: BMCAbonnement) -> None:
        """ Deletes an abonnement. """
        with self.connect_to_db() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM abonnement WHERE id=?", (abonnement.db_id, ))

    # Helper methods
    def get_client_id(self, client: BMCClient) -> int or None:
        """ Get the ID of a client entry in the database based on its supposedly unique first name + last name
        combination. """
        with self.connect_to_db() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM client WHERE first_name LIKE ? AND last_name LIKE ?",
                           (client.first_name, client.last_name))
            res = cursor.fetchall()
            if len(res) == 1:
                return int(res[0][0])
            else:
                return None

    def get_client_abonnements(self, client: BMCClient) -> List[BMCAbonnement] or None:
        """ Given a client returns all the abonnements associated with the client. """
        with self.connect_to_db() as connection:
            client_id = self.get_client_id(client)
            if client_id:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM abonnement WHERE client_id == ?", (client_id,))
                sql_abonnements = cursor.fetchall()
                python_abonnements = []
                for sql_abo in sql_abonnements:
                    python_abonnements.append(self.convert_sql_abonnement_to_python_abonnement(sql_abo))
                return python_abonnements
            return None

    def convert_sql_abonnement_to_python_abonnement(self, abonnement_fields: Tuple) -> BMCAbonnement:
        """ Converts a client database table entry to a python client object. """
        python_abonnement = BMCAbonnement(
            db_id=int(abonnement_fields[0]),
            abo_type=abonnement_fields[2],
            buy_date=datetime.datetime.strptime(abonnement_fields[4], "%Y-%m-%d").date(),
            end_date=datetime.datetime.strptime(abonnement_fields[5], "%Y-%m-%d").date() if abonnement_fields[5] is not None else None,
            entrances_remaining=int(abonnement_fields[6]) if abonnement_fields[6] is not None else None,
            include_gear=bool(abonnement_fields[3]),
            owner=self.find_client_from_id(abonnement_fields[1])
        )

        return python_abonnement

    @staticmethod
    def convert_sql_client_to_python_client(client_fields: Tuple) -> BMCClient:
        """ Converts a client database table entry to a python client object. """
        python_client = BMCClient(
            db_id=int(client_fields[0]),
            first_name=client_fields[1],
            last_name=client_fields[2],
            reduced_price=bool(client_fields[3]) if client_fields[3] is not None else None,
            email=client_fields[4],
            phone=client_fields[5],
            date_of_birth=datetime.datetime.strptime(client_fields[6], "%Y-%m-%d").date() if client_fields[6] is not None else None,
            sex=client_fields[7],
            street_name=client_fields[8],
            street_number=client_fields[9],
            city_zip=client_fields[10],
            city_name=client_fields[11],
            country=client_fields[12],
        )

        return python_client


class BMCAboManager:
    """ The BMCAboManager is responsible for managing the clients and abonnements and it basically an adittional bridge
    which wraps the client and abonnements classes in convenient methods, and interacts with them and the db through
    the DBInterfacer to read and write data. """

    def __init__(self, path_to_db: str or Path):
        self.path_to_db = path_to_db
        self.db_interface = BMCAboDBInterfacer(path_to_db)

        self.current_client = None
        self.current_client_abonnements = None
        self.valid_client_abonnement = None

        self.matching_clients = []

    @property
    def current_client(self) -> BMCClient:
        return self.__current_client

    @current_client.setter
    def current_client(self, client: BMCClient or None) -> None:
        if isinstance(client, BMCClient):
            self.__current_client = client
            self.current_client_abonnements = self.db_interface.get_client_abonnements(self.current_client)
            valid_abos = []
            for ab in self.current_client_abonnements:
                if ab.is_valid:
                    valid_abos.append(ab)
            if len(valid_abos) == 0:
                self.valid_client_abonnement = None
            elif len(valid_abos) == 1:
                self.valid_client_abonnement = valid_abos[0]
            else:
                raise IOError("Found more than one valid abonnement for current client {}".
                                format(self.current_client.db_id))
        else:
            self.__current_client = None
            self.current_client_abonnements = None
            self.valid_client_abonnement = None

    def search_clients(self, name_part: str) -> None:
        """ Looks for clients whose first name OR last name begin with the provided name part and sets all the
        matches in the matching_clients field. """
        fn_matches = self.db_interface.find_clients_from_namepart(name_part, "first")
        ln_matches = self.db_interface.find_clients_from_namepart(name_part, "last")

        self.matching_clients = fn_matches + ln_matches

    def create_new_client(self, first_name: str, last_name: str, reduced_price: bool = False, email: str = None,
                          phone: str = None, date_of_birth: datetime.date = None, sex: str = None,
                          street_name: str = None,
                          street_number: str = None, city_zip: int = None, city_name: str = None,
                          country: str = None) -> None:
        """ Creates a new client and saves the client to the db. """
        new_client = BMCClient(first_name, last_name, None, reduced_price, email, phone, date_of_birth, sex,
                               street_name,
                               street_number, city_zip, city_name, country)

        self.db_interface.create_client(new_client)
        self.current_client = self.db_interface.find_client_from_name(new_client.first_name, new_client.last_name)

    def create_new_abonnement(self, abo_type: str, reduced_price: bool, include_gear: bool) -> None:
        """ Creates a new abonnement for the current client, and if neccesary updates the current client's reduced price
        field. """
        assert self.valid_client_abonnement is None
        self.current_client.reduced_price = reduced_price
        self.db_interface.update_client(self.current_client)
        buy_date = datetime.date.today()
        end_date = datetime.date.today()+relativedelta(months=+3)+relativedelta(days=-1) if abo_type == "3M" else None
        entrances_remaining = 10 if abo_type == "C10S" else None
        abo = BMCAbonnement(self.current_client, abo_type, buy_date, None, include_gear, end_date, entrances_remaining)
        self.db_interface.create_abonnement(abo)
        self.current_client = self.current_client  # Triggers an update of the clients' abonnements

    def update_current_client(self, first_name: str, last_name: str, reduced_price: bool = False, email: str = None,
                              phone: str = None, date_of_birth: datetime.date = None, sex: str = None,
                              street_name: str = None,
                              street_number: str = None, city_zip: int = None, city_name: str = None,
                              country: str = None) -> None:
        """ Updates the current client. """
        existing_client = BMCClient(first_name, last_name, self.current_client.db_id, reduced_price, email, phone,
                                    date_of_birth, sex, street_name, street_number, city_zip, city_name, country)

        self.db_interface.update_client(existing_client)
        self.current_client = existing_client

    def update_valid_abonnement_end_date(self, new_end_date: datetime.date):
        """ Modifies the current valid abonnement's end date and saves to the db. """
        assert self.valid_client_abonnement is not None
        self.valid_client_abonnement.end_date = new_end_date
        self.db_interface.update_abonnement(self.valid_client_abonnement)
        self.current_client = self.current_client

    def update_valid_abonnement_entrances(self, num_entries_to_subtract: int):
        """ Subtracts a number of entries from a C10S type abonnement. """
        assert self.valid_client_abonnement is not None
        self.valid_client_abonnement.entrances_remaining -= num_entries_to_subtract
        self.db_interface.update_abonnement(self.valid_client_abonnement)
        self.current_client = self.current_client

    def delete_valid_abonnement(self):
        """ Deletes the current client's currently valid abonnement. """
        assert self.valid_client_abonnement is not None
        if self.valid_client_abonnement.db_id is not None:
            self.db_interface.delete_abonnement(self.valid_client_abonnement)
            self.valid_client_abonnement = None
            self.current_client = self.current_client
        else:
            raise IOError("Requested DELETE on an abonnement which has no db id")



