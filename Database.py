import sqlite3
from pathlib import Path
from datetime import datetime


class Database:

    def __init__(self, datapath: Path, chat_id):

        self.chat_id = chat_id
        self.data_path = datapath / f"{chat_id}.db"

        if not Path.exists(self.data_path):
            with sqlite3.connect(self.data_path) as conn:

                cursor = conn.cursor()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value REAL NOT NULL,
                    time TEXT NOT NULL,
                    type TEXT,
                    tags TEXT,
                    info TEXT
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
                """)
                types = [("variável",), ("fixa",)]
                cursor.executemany("INSERT INTO types (name) VALUES (?)", types)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
                """)
                tags = [("outros",), ("alimentação",), ("transporte",), ("energia",), ("água",), ("telefone",),
                        ("saúde",), ("lazer",), ("educação",), ("internet",), ("aluguel",)]
                cursor.executemany("INSERT INTO tags (name) VALUES (?)", tags)


    def push_transaction(self, amount, transaction_type, transaction_tags=()):
        """Cria nova transação.

        Args:
            amount : valor da transação
            transaction_type : tipo da transação
            transaction_tags : tupla com as tags da transação

        Returns:
            (message, transaction_id)
        """

        comments = ""

        # Valida valor fornecido.
        try:
            value = float(amount)
        except ValueError:
            return "Valor deve ser numérico.", None

        # Começa operações com BD pois próximas validações dependem dos tipos e tags registrados.
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()

            # Validação de tipo
            cursor.execute("SELECT name FROM types")
            rows = cursor.fetchall()  # Lista de tuplas. Cada tupla é uma linha dos resultados.

            # Se não foi fornecido um tipo, pegue o tipo de transação default.
            if not transaction_type:
                trans_type = rows[0][0]
                comments += f"Tipo não fornecido, usando '{trans_type}'.\n"

            # Se foi fornecido, vamos verificar se é um tipo válido.
            else:
                trans_type = None
                for row in rows:
                    if row[0] == transaction_type:
                        trans_type = transaction_type

                # Se tipo fornecido não coincidiu com nenhum tipo registrado, reporte erro.
                if not trans_type:
                    return "Tipo de transação não registrado.", None

            # Validação de tags. Apenas ignora tags não registradas.
            cursor.execute("SELECT name FROM tags")
            rows = cursor.fetchall()
            registered_tags = [row[0] for row in rows]
            effective_tags = []
            for tag in transaction_tags:
                if tag in registered_tags:
                    effective_tags.append(tag)
                else:
                    comments += f"Ignorando '{tag}' pois não está registrada como tag.\n"
            effective_tags = " ".join(effective_tags)
            if effective_tags == "":
                effective_tags = None

            # Horário da Transação
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("INSERT INTO transactions (value, time, type, tags) VALUES (?, ?, ?, ?)",
                           (value, timestamp, trans_type, effective_tags))

            transaction_id = cursor.lastrowid

        main_msg = timestamp + "\n\n"
        main_msg += f"ID: {transaction_id}\n"
        main_msg += f"Valor: R$ {value}\n"
        main_msg += f"Tipo: {trans_type}\n"
        if effective_tags:
            main_msg += f"Tags: {effective_tags}\n"
        else:
            main_msg += "Sem tags\n"
        if comments:
            main_msg += f"\n{comments}"
        main_msg = main_msg.strip()

        return main_msg, transaction_id


    def get_types(self):
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT name FROM types")
            types = [t[0] for t in rows]
        return types


    def register_types(self, new_types):

        msg = ""

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM types")
            rows = cursor.fetchall()
            current_types = [t[0] for t in rows]

            next_types = []
            for t in new_types:
                if t not in current_types:
                    msg += f"Tipo novo: {t}\n"
                    next_types.append((t,))
                else:
                    msg += f"Tipo repetido: {t}\n"

            if len(next_types) > 0:
                cursor.executemany("INSERT INTO types (name) VALUES (?)", next_types)
            else:
                msg += "Nenhum tipo nova a adicionar."

        return msg


    def unregister_types(self, remove_types):

        # Transforma a lista de tipos em uma lista de tuplas com os tipos, para uso com cursor.executemany() .
        remove_types = [(t, ) for t in remove_types]

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM types WHERE name = ?", remove_types)

        return "Tipos removidos."


    def get_tags(self):
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT name FROM tags")
            tags = [t[0] for t in rows]
        return tags


    def register_tags(self, new_tags):

        msg = ""

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM tags")
            rows = cursor.fetchall()
            current_tags = [row[0] for row in rows]
            next_tags = []
            for tag in new_tags:
                if tag not in current_tags:
                    msg += f"Tag Nova: {tag}\n"
                    next_tags.append((tag,))
                else:
                    msg += f"Tag repetida: {tag}\n"

            if len(next_tags) > 0:
                cursor.executemany("INSERT INTO tags (name) VALUES (?)", next_tags)
            else:
                msg += "Nenhuma tag nova a adicionar."

        return msg


    def unregister_tags(self, remove_tags):

        ### NOVO ###

        # Transforma a lista de tags em uma lista de tuplas com as tags, para uso com cursor.executemany() .
        remove_tags = [(tag,) for tag in remove_tags]

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM tags WHERE name = ?", remove_tags)

        return "Tags removidas."


    def get_transaction(self, transaction_id):
        """Retorna tupla contendo os dados de uma transação.

        Args:
            transaction_id : ID da transação desejada.

        Returns:
             (id, value, time, type, tags, info)
        """

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return None


    def fetch_transactions_by_range(self, start_year, start_month, end_year, end_month):

        start = f"{start_year}-{start_month}-01 00:00:00"
        end = f"{end_year}-{end_month}-32 23:59:59"

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE time >= ? AND time <= ?", (start, end))
            rows = cursor.fetchall()

        return rows


    def update_transaction_value(self, transaction_id, new_value):

        try:
            value = float(new_value)
        except ValueError:
            return False, "Forneça um valor numérico."

        try:
            trans_id = int(transaction_id)
        except KeyError:
            return False, "ID da transação deve ser um número inteiro."

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transactions SET value = ? WHERE id = ?", (value, trans_id))
            row_count = cursor.rowcount

        if row_count > 0:
            return True, "Transação atualizada."
        else:
            return False, "Nenhuma transação atualizada."


    def update_transaction_type(self, transaction_id, new_type):

        try:
            trans_id = int(transaction_id)
        except KeyError:
            return False, "ID da transação deve ser um número inteiro."

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()

            # Obtém tipos registrados.
            cursor.execute("SELECT name FROM types")
            rows = cursor.fetchall()
            types = [t[0] for t in rows]

            if new_type not in types:
                return False, f"Tipo '{new_type}' não registrado."

            cursor.execute("UPDATE transactions SET type = ? WHERE id = ?", (new_type, trans_id))
            row_count = cursor.rowcount

            if row_count > 0:
                return True, "Transação atualizada."
            else:
                return False, "Nenhuma transação atualizada."

        return True, "Transação atualizada."


    def update_transaction_tags(self, transaction_id, add_tags, remove_tags):

        main_msg = ""
        comments = ""

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()

            # Resgada tags da transação pertinente.
            cursor.execute("SELECT tags FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()

            if len(row) < 1:
                return False, "Transação não encontrada."

            # Lista de tags atuais da transação.
            if row[0] is not None:
                current_tags = row[0].split()
            else:
                current_tags = []

            # Obtém tags registradas.
            cursor.execute("SELECT name FROM tags")
            rows = cursor.fetchall()
            available_tags = [row[0] for row in rows]

            # Tags a adicionar devem estar registradas.
            effective_add_tags = []
            for t in add_tags:
                if t in available_tags:
                    effective_add_tags.append(t)
                else:
                    comments += f"Ignorando '{t}' pois não está registrada."

            # Inclui novas tags.
            for tag in effective_add_tags:
                if tag not in current_tags:
                    current_tags.append(tag)

            # Exclui tags.
            current_tags = set(current_tags) - set(remove_tags)
            current_tags = list(current_tags)
            current_tags = " ".join(current_tags)

            if not current_tags:
                current_tags = None

            # Escreve novo conjunto de tags no banco.
            cursor.execute("UPDATE transactions SET tags = ? WHERE id = ?", (current_tags, transaction_id))

            # Monta mensagem de resposta.
            main_msg = "Transação atualizada."
            if comments:
                main_msg += f"\n{comments}"

        return True, main_msg


    def update_transaction_info(self, transaction_id, info):

        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transactions SET info = ? WHERE id = ?", (info, transaction_id))
            row_count = cursor.rowcount

            if row_count > 0:
                return True, "Transação atualizada."
            else:
                return False, "Nenhuma transação atualizada."

