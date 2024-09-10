import sqlite3


class BMCProduct:
    """The BMCProduct class is used to represent a product that is sold at BMC. """

    def __init__(self, name, price, stock, color=None):
        self.name = name
        self.price = price
        self.stock = stock
        self.color = color
        self.changed_stock = False
        self.stock_backup = stock

    @property
    def description(self):
        return str(self.name) + "\nStock: " + str(self.stock)

    def sell(self):
        self.stock -= 1
        self.changed_stock = True

    def restore(self):
        self.changed_stock = False
        self.stock = self.stock_backup


def convert_sql_product_to_python_product(product_field):
    return BMCProduct(
        name=product_field[0],
        price=product_field[1],
        stock=product_field[2],
        color=product_field[3]
    )


class BMCProductsManager:
    """ The BMCProductsManager is responsible for managing the products and sales and it basically an adittional bridge
    which wraps the products and sales classes in convenient methods, and interacts with them and the DBManager through
    the DBInterfacer to read and write data. """

    products = None

    @staticmethod
    def connect_to_db(path_to_db) -> sqlite3.Connection:
        """ Open the connection to the db. """
        return sqlite3.connect(path_to_db)

    @staticmethod
    def fetch_products(path_to_db):
        """ get all products from the db"""
        try:
            with BMCProductsManager.connect_to_db(path_to_db) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM produit")
                sql_products = cursor.fetchall()
        except Exception:
            return []
        python_products = []
        sql_products.sort(key=lambda x: x[3])
        for sql_product in sql_products:
            python_products.append(convert_sql_product_to_python_product(sql_product))
        BMCProductsManager.products = python_products

    @staticmethod
    def adjust_local_stocks(product_name):
        product = list(filter(lambda x: x.name == product_name, BMCProductsManager.products))[0]
        product.sell()

    @staticmethod
    def update_db(path_to_db):
        with BMCProductsManager.connect_to_db(path_to_db) as connection:
            cursor = connection.cursor()
            for product in BMCProductsManager.products:
                if product.changed_stock:
                    try:
                        cursor.execute("UPDATE produit SET stock=? WHERE name=?", (product.stock, product.name))
                    except Exception:
                        raise Exception("Erreur lors de la mise à jour des stocks")
                    product.changed_stock = False

    @staticmethod
    def get_with_name(name):
        return list(filter(lambda x: x.name == name, BMCProductsManager.products))[0]

    @staticmethod
    def confirm_stock():
        for product in BMCProductsManager.products:
            if product.changed_stock:
                product.stock_backup = product.stock
                product.changed_stock = False
