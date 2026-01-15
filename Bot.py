import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from Database import Database
from Report import Report

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
if LOG_LEVEL == "ERROR":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.ERROR
    )
elif LOG_LEVEL == "WARNING":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.WARNING
    )
elif LOG_LEVEL == "DEBUG":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.DEBUG
    )
else:
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.INFO
    )

DATAPATH = Path(os.getenv("DATAPATH", default="data"))
if not Path.exists(DATAPATH):
    Path.mkdir(DATAPATH)



def parse_range(args):

    now = datetime.now()
    start_year = f"{now.year}"
    start_month = f"{now.month}"
    end_year = start_year
    end_month = start_month

    for a in args:
        try:
            test = int(a)
        except ValueError:
            return False, None, None, None, None

    # Mês do ano corrente.
    if len(args) == 1:
        start_month = end_month = args[0]

    # Mês inicial e mês final do ano corrente.
    elif len(args) == 2:
        start_month = args[0]
        end_month = args[1]

    # Ano especificado, seguido do mês inicial e do mês final.
    elif len(args) == 3:
        start_year = end_year = args[0]
        start_month = args[1]
        end_month = args[2]

    # Especificados ano de começo, mês de começo, ano final e mês final.
    elif len(args) == 4:
        start_year = args[0]
        start_month = args[1]
        end_year = args[2]
        end_month = args[3]

    if int(start_year) < 10:
        start_year = "0" + start_year
    if int(start_month) < 10:
        start_month = "0" + start_month
    if int(end_year) < 10:
        end_year = "0" + end_year
    if int(end_month) < 10:
        end_month = "0" + end_month

    return True, start_year, start_month, end_year, end_month



def update_active_transaction(chat_id, transaction_id):
    sel_trans_path = DATAPATH / f"{chat_id}_selected.txt"
    with open(sel_trans_path, "w") as f:
        f.write(f"{transaction_id}")



def get_active_transaction(chat_id):
    """Retorna o ID da transação atualmente selecionada.

    Args:
        chat_id: ID do chat atual.

    Returns:
        id (int): ID da transação selecionada.
    """

    sel_trans_path = DATAPATH / f"{chat_id}_selected.txt"
    try:
        with open(sel_trans_path, "r") as f:
            sel_trans_id = int(f.read())
    except (FileNotFoundError, ValueError):
        return 0
    return sel_trans_id



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    with open("README.md", "r") as f:
        reply = f.read()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def cash_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    db = Database(DATAPATH, chat_id)

    arg_count = len(context.args)

    if arg_count > 0:
        amount = context.args[0]
    else:
        reply = "Forneça ao menos o valor da entrada."
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    if arg_count > 1:
        trans_type = context.args[1]
    else:
        trans_type = None

    if arg_count > 2:
        trans_tags = context.args[2:]
    else:
        trans_tags = ()

    reply, trans_id = db.push_transaction(amount, trans_type, trans_tags)
    update_active_transaction(chat_id, trans_id)

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def cash_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    db = Database(DATAPATH, chat_id)

    arg_count = len(context.args)

    if arg_count > 0:
        amount = f"-{context.args[0]}"
    else:
        reply = "Forneça ao menos o valor da saída."
        await context.bot.send_message(chat_id=chat_id, text=reply)
        return

    if arg_count > 1:
        trans_type = context.args[1]
    else:
        trans_type = None

    if arg_count > 2:
        trans_tags = context.args[2:]
    else:
        trans_tags = ()

    reply, trans_id = db.push_transaction(amount, trans_type, trans_tags)
    update_active_transaction(chat_id, trans_id)

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    db = Database(DATAPATH, chat_id)

    valid, start_year, start_month, end_year, end_month = parse_range(context.args)

    if valid:
        reply = f"Saldo de {start_year}/{start_month} - {end_year}/{end_month}:\n"
        results = db.fetch_transactions_by_range(start_year, start_month, end_year, end_month)
        report = Report(results)
        reply += f"R$ {report.get_balance()}"

    else:
        reply = "Argumentos devem ser numéricos, descrevendo intervalo de meses desejado."

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    db = Database(DATAPATH, chat_id)

    valid, start_year, start_month, end_year, end_month = parse_range(context.args)

    if valid:
        reply = f"Extrato de {start_year}/{start_month} - {end_year}/{end_month}:\n\n"
        results = db.fetch_transactions_by_range(start_year, start_month, end_year, end_month)
        report = Report(results)
        reply += f"{report.get_history()}"

    else:
        reply = "Argumentos devem ser numéricos, descrevendo intervalo de meses desejado."

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def get_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) == 0:
        trans_id = get_active_transaction(chat_id)
    else:
        trans_id = context.args[0]

    try:
        trans_id = int(trans_id)
    except ValueError:
        reply = "ID da transação desejada deve ser um número inteiro."
    else:
        db = Database(DATAPATH, chat_id)
        transaction = db.get_transaction(trans_id)

        if transaction is None:
            reply = "Transação não encontrada."
        else:
            update_active_transaction(chat_id, trans_id)
            reply = f"{transaction[2]}\n"
            reply += f"ID: {transaction[0]}\n"
            reply += f"Valor: R$ {transaction[1]}\n"
            reply += f"Tipo: {transaction[3]}\n"
            if transaction[4]:
                reply += f"Tags: {transaction[4]}\n"
            if transaction[5]:
                reply += f"{transaction[5]}"
            reply = reply.strip()

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def update_transaction_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        reply = "Forneça o novo valor da transação."

    else:
        transaction_id = get_active_transaction(chat_id)
        db = Database(DATAPATH, chat_id)
        result, reply = db.update_transaction_value(transaction_id, context.args[0])

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def update_transaction_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        reply = "Forneça o novo tipo para a transação selecionada."

    else:
        transaction_id = get_active_transaction(chat_id)
        db = Database(DATAPATH, chat_id)
        result, reply = db.update_transaction_type(transaction_id, context.args[0])

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def update_transaction_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        reply = "Forneça as tags a adicionar ou remover. Remova uma tag com prefixo '-', e.g. -alimentação."

    else:

        # Separa as tags a serem removidas das a serem adicionadas.
        remove_tags = []
        add_tags = []
        for tag in context.args:
            if tag.startswith("-"):
                remove_tags.append(tag.strip("-"))
            else:
                add_tags.append(tag)
        reply = f"Remover: {' '.join(remove_tags)}\n"
        reply += f"Adicionar: {' '.join(add_tags)}\n"

        transaction_id = get_active_transaction(chat_id)
        db = Database(DATAPATH, chat_id)
        result, msg = db.update_transaction_tags(transaction_id, add_tags, remove_tags)
        reply += msg

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def update_transaction_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        reply = "Forneça a descrição a adicionar à transação."

    else:
        transaction_id = get_active_transaction(chat_id)
        info = " ".join(context.args)
        db = Database(DATAPATH, chat_id)
        result, reply = db.update_transaction_info(transaction_id, info)

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = Database(DATAPATH, chat_id)

    if len(context.args) < 1:
        reply = " ".join(db.get_types())

    else:

        if context.args[0] == "adi":
            msg = db.register_types(context.args[1:])
            logging.info(msg)
            reply = "Atualizado:\n" + " ".join(db.get_types())

        elif context.args[0] == "rem":
            msg = db.unregister_types(context.args[1:])
            logging.info(msg)
            reply = "Atualizado:\n" + " ".join(db.get_types())

        else:
            reply = "Uso:\n"
            reply += "  Exibir tipos: /tipos\n"
            reply += "  Adicionar tipos: /tipos adi novo_tipo_1 novo_tipo_2 ...\n"
            reply += "  Remover tipos: /tipos rem tipo_1 tipo_2 ..."

    await context.bot.send_message(chat_id=chat_id, text=reply)



async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = Database(DATAPATH, chat_id)

    if len(context.args) == 0:
        reply = " ".join(db.get_tags())

    elif context.args[0] == "adi":
        msg = db.register_tags(context.args[1:])
        logging.info(msg)
        reply = "Atualizado:\n" + " ".join(db.get_tags())

    elif context.args[0] == "rem":
        msg = db.unregister_tags(context.args[1:])
        logging.info(msg)
        reply = "Atualizado:\n" + " ".join(db.get_tags())

    else:
        reply = "Uso:\n"
        reply += "  Exibir tags: /tags\n"
        reply += "  Adicionar tags: /tags adi nova_tag_1 nova_tag_2 ...\n"
        reply += "  Remover tags: /tags rem tag_1 tag_2 ..."

    await context.bot.send_message(chat_id=chat_id, text=reply)



if __name__ == "__main__":

    print(f"Log level: {LOG_LEVEL}")

    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    cash_in_handler = CommandHandler("entra", cash_in)
    application.add_handler(cash_in_handler)

    cash_out_handler = CommandHandler("sai", cash_out)
    application.add_handler(cash_out_handler)

    balance_handler = CommandHandler("saldo", balance)
    application.add_handler(balance_handler)

    history_handler = CommandHandler("extrato", history)
    application.add_handler(history_handler)

    get_transaction_handler = CommandHandler("ver", get_transaction)
    application.add_handler(get_transaction_handler)

    update_trans_value_handler = CommandHandler("valor", update_transaction_value)
    application.add_handler(update_trans_value_handler)

    update_trans_type_handler = CommandHandler("tipo", update_transaction_type)
    application.add_handler(update_trans_type_handler)

    update_trans_tags_handler = CommandHandler("tag", update_transaction_tags)
    application.add_handler(update_trans_tags_handler)

    update_trans_info_handler = CommandHandler("detalhes", update_transaction_info)
    application.add_handler(update_trans_info_handler)

    see_types_handler = CommandHandler("tipos", types)
    application.add_handler(see_types_handler)

    see_tags_handler = CommandHandler("tags", tags)
    application.add_handler(see_tags_handler)

    print("Bot starting...")

    application.run_polling()

    print("Bot stopped")