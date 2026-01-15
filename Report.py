import json



class Report:

    def __init__(self, data):
        self.data = data

    def get_balance(self):

        balance = 0

        for row in self.data:
            balance += row[1]

        return balance

    def get_history(self):

        history = ""

        for row in self.data:
            history += f"{row[2]}\n"
            history += f"ID: {row[0]}\n"
            history += f"R$: {row[1]}\n"
            history += f"Tipo: {row[3]}\n"
            if row[4]:
                history += f"Tags: {row[4]}\n"
            if row[5]:
                history += f"{row[5]}\n"
            history += "\n"

        return history