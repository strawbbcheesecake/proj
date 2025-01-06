class Product:
    count_id = 0

    def __init__(self, name, desc, category, price):
        Product.count_id += 1

        self.__product_id = Product.count_id  # 1, 2 ,3 etc
        self.__name = name  # Green Shirt etc
        self.__desc = desc
        self.__category = category  # shirt, pants etc
        self.__price = price  # 15.00 etc

    # Getter methods
    def get_product_id(self):
        return self.__product_id

    def get_name(self):
        return self.__name

    def get_desc(self):
        return self.__desc

    def get_price(self):
        return self.__price

    def get_category(self):
        return self.__category

    # Setter methods
    def set_product_id(self, product_id):
        self.__product_id = product_id

    def set_name(self, name):
        self.__name = name

    def set_desc(self, desc):
        self.__desc = desc

    def set_price(self, price):
        self.__price = price

    def set_category(self, category):
        self.__category = category


class Cart:
    count_id = 0

    def __init__(self, product_id, name, price, quantity=1):
        self.__product_id = product_id  # product object id
        self.__name = name
        self.__price = price
        self.__quantity = quantity

    def get_product_id(self):
        return self.__product_id

    def get_name(self):
        return self.__name

    def get_price(self):
        return self.__price

    def get_quantity(self):
        return self.__quantity

        # Setter methods

    def set_product_id(self, product_id):
        self.__product_id = product_id

    def add_quantity(self):
        self.__quantity += 1

    def minus_quantity(self):
        self.__quantity -= 1