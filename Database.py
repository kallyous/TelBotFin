import json
from pathlib import Path
from datetime import datetime


class Database:

    def __init__(self, chat_id):
        
        self.chat_id = chat_id
        
        self.data_path = Path(f"{chat_id}.json")
        if not self.data_path.exists():
            data = {}
            with open(self.data_path, 'w') as f:
                f.write(json.dumps(data))
        with open(self.data_path, 'r') as f:
            self.data = json.load(f)

        self.types_path = Path(f"{self.chat_id}_types.txt")
        if not self.types_path.exists():
            self.types = ["variável", "fixa"]
            with open(self.types_path, 'w') as f:
                f.write(" ".join(self.types))
        else:
            with open(self.types_path, 'r') as f:
                self.types = f.read().split()

        self.tags_path = Path(f"{self.chat_id}_tags.txt")
        if not self.tags_path.exists():
            self.tags = ["outros", "alimentação", "transporte", "energia", "água", "telefone", "saúde", "lazer"
                         "educação", "internet", "aluguel"]
            with open(self.tags_path, 'w') as f:
                f.write(" ".join(self.tags))
        else:
            with open(self.tags_path, 'r') as f:
                self.tags = f.read().split()


    def details(self):
        print("\nData path:", self.data_path)
        print("Data:\n", self.data)
        print("\nTags path:", self.tags_path)
        print("Tags:\n", self.tags)
        print("\nTypes path:", self.types_path)
        print("Types:\n", self.types)
        print()


    def register_tags(self, new_tags):
        for tag in new_tags:
            if tag not in self.tags:
                self.tags.append(tag)
        with open(self.tags_path, "w") as f:
            f.write(" ".join(self.tags))


    def unregister_tags(self, remove_tags):
        tags = set(self.tags) - set(remove_tags)
        self.tags = list(tags)
        with open(self.tags_path, "w") as f:
            f.write(" ".join(self.tags))


    def register_types(self, new_types):
        for new_type in new_types:
            if new_type not in self.types:
                self.types.append(new_type)
        with open(self.types_path, "w") as f:
            f.write(" ".join(self.types))


    def unregister_types(self, remove_types):
        types = set(self.types) - set(remove_types)
        self.types = list(types)
        with open(self.types_path, "w") as f:
            f.write(" ".join(self.types))


    def get_transaction(self, year, month, day, stamp):
        try:
            trans = self.data[year][month][day][stamp]
        except KeyError:
            trans = None
        return trans


    def push_transaction(self, amount, transaction_type, tags=()):

        with open(self.data_path, 'r') as f:
            data = json.load(f)

        now = datetime.now()
        stamp = now.strftime('%H%M%S')

        year = f"{now.year}"
        month = f"{now.month}"
        day = f"{now.day}"

        if not year in data:
            data[year] = {}

        if not month in data[year]:
            data[year][month] = {}

        if not day in data[year][month]:
            data[year][month][day] = {}

        data[year][month][day][stamp] = {
            "amount": amount,
            "type": transaction_type,
            "tags": tags,
            "info": ""
        }

        with open(self.data_path, 'w') as f:
            f.write(json.dumps(data))

        return year, month, day, stamp


    def fetch_transactions_by_range(self, start_year, start_month, end_year, end_month):

        results = {}

        for year in range(int(start_year), int(end_year) + 1):

            y = f"{year}"
            if y in self.data:

                results[y] = {}

                for month in range(1, 13):
                    if y == start_year and month < int(start_month): continue
                    if y == end_year and month > int(end_month): continue

                    m = f"{month}"
                    if m in self.data[y]:

                        results[y][m] = {}

                        for day in range(1, 31):

                            d = f"{day}"
                            if d in self.data[y][m]:

                                results[y][m][d] = {}

                                for stamp in self.data[y][m][d]:
                                    results[y][m][d][stamp] = self.data[y][m][d][stamp]

        return results


    def update_transaction_type(self, year, month, day, stamp, new_type):

        if new_type not in self.types:
            return False, "Tipo inválido."

        try:
            self.data[year][month][day][stamp]["type"] = new_type

        except KeyError:
            return False, "Transação não encontrada."

        # Salva alterações.
        with open(self.data_path, 'w') as f:
            f.write(json.dumps(self.data))

        return True, "Transação atualizada."


    def update_transaction_tags(self, year, month, day, stamp, add_tags, remove_tags):

        msg = ""

        try:
            # Lista atual de tags.
            curr_tags = self.data[year][month][day][stamp]["tags"]

            # Remove tags com aritmética de conjuntos. O teste de pertencimento é O(1), contra O(n) para o mesmo teste
            new_tags = set(curr_tags) - set(remove_tags)  # em lista, o que é importante para subtração.

            # Para as adições, temos que checar se a tag é válida antes de adicionar.
            for tag in add_tags:
                if tag in self.tags:
                    new_tags.add(tag)
                else:
                    msg += f"Atenção: '{tag}' não adicionada pois não existe na lista de tags.\n"

            # Substitui lista de tags
            new_tags = list(new_tags)
            self.data[year][month][day][stamp]["tags"] = new_tags

            # Salva alterações.
            with open(self.data_path, 'w') as f:
                f.write(json.dumps(self.data))

        except KeyError:
            return False, "Transação não encontrada."

        msg += "Transação atualizada."
        return True, msg


    def update_transaction_info(self, year, month, day, stamp, info):

        try:
            self.data[year][month][day][stamp]["info"] = info
        except KeyError:
            return False, "Transação não encontrada."

        with open(self.data_path, 'w') as f:
            f.write(json.dumps(self.data))

        return True, "Transação atualizada."
