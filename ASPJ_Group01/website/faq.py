class Faq():
    count_id = 0

    # initializer method
    def __init__(self, question, answer):
        Faq.count_id += 1
        self.__faq_id = Faq.count_id
        self.__question = question
        self.__answer = answer

    # accessor methods
    def get_faq_id(self):
        return self.__faq_id

    def get_question(self):
        return self.__question

    def get_answer(self):
        return self.__answer

    # mutator methods
    def set_faq_id(self, faq_id):
        self.__faq_id = faq_id

    def set_question(self, question):
        self.__question = question

    def set_answer(self, answer):
        self.__answer = answer
