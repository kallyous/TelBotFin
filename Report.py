import json



class Report:

    def __init__(self, data):
        self.data = data

    def get_balance(self):

        balance = 0

        for y in self.data:
            for m in self.data[y]:
                for d in self.data[y][m]:
                    for stamp in self.data[y][m][d]:
                        balance += self.data[y][m][d][stamp]["amount"]

        return balance

    def get_history(self):

        history = ""

        for y in self.data:
            for m in self.data[y]:
                for d in self.data[y][m]:
                    history += "----------------------------------------"
                    history += f"\n{y}-{m}-{d}\n\n"

                    for stamp in self.data[y][m][d]:
                        history += f"{stamp}\n"
                        history += f"R$ {self.data[y][m][d][stamp]['amount']}"
                        if len(self.data[y][m][d][stamp]["tags"]) > 0:
                            history += "\n"
                            for tag in self.data[y][m][d][stamp]["tags"]:
                                history += f"{tag} "
                        if self.data[y][m][d][stamp]["info"] != "":
                            history += f"\n{self.data[y][m][d][stamp]['info']}"
                        history += "\n\n"

        return history