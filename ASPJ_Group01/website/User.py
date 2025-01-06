class User:
    count_id = 0

    # initializer method
    def __init__(self, fname, lname, email, password):
        User.count_id += 1
        self.__user_id = User.count_id
        self.__fname = fname
        self.__lname = lname
        self.__email = email
        self.__password = password

    # accessor methods
    def get_user_id(self):
        return self.__user_id

    def get_fname(self):
        return self.__fname

    def get_lname(self):
        return self.__lname

    def get_email(self):
        return self.__email

    def get_password(self):
        return self.__password

    # mutator methods
    def set_user_id(self, user_id):
        self.__user_id = user_id

    def set_fname(self, fname):
        self.__fname = fname

    def set_lname(self, lname):
        self.__lname = lname

    def set_email(self, email):
        self.__email = email

    def set_password(self, password):
        self.__password = password

