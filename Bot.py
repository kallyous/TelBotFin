import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from Database import Database
from Report import Report



def validate_transaction(args, types, tags):

    if len(args) < 1:
        return False, "Informar ao menos o valor."

    try:
        amount = float(args[0])
    except ValueError:
        return False, "Primeiro argumento deve ser um número."

    if len(args) > 1:
        if args[1] in types:
            transaction_type = args[1]
        else:
            return False, "Segundo argumento deve dizer o tipo da movimentação, dentre: " + " ".join(types)
    else:
        transaction_type = types[0]

    used_tags = []
    if len(args) > 2:
        for arg in args[2:]:
            if arg not in tags:
                return False, "A tag " + arg + " não está registrada."
        used_tags = args[2:]

    return True, (amount, transaction_type, used_tags)



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

    return True, start_year, start_month, end_year, end_month



def update_active_transaction(chat_id, year, month, day, stamp):
    at_path = f"{chat_id}_at.txt"
    with open(at_path, "w") as f:
        f.write(f"{year} {month} {day} {stamp}")



def get_active_transaction(chat_id):
    at_path = f"{chat_id}_at.txt"
    try:
        with open(at_path, "r") as f:
            year, month, day, stamp = f.readline().split()
    except Exception as e:
        logging.info(e)
        return "", "", "", ""
    return year, month, day, stamp



async def cash_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    valid, stat = validate_transaction(context.args, db.types, db.tags)

    if valid:
        amount, transaction_type, used_tags = stat
        year, month, day, stamp = db.push_transaction(amount, transaction_type, used_tags)
        update_active_transaction(update.effective_chat.id, year, month, day, stamp)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Quanto: {amount}\nTipo: {transaction_type}\nTags: {used_tags}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=stat)



async def cash_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    valid, stat = validate_transaction(context.args, db.types, db.tags)

    if valid:
        amount, transaction_type, used_tags = stat
        amount = amount * -1
        year, month, day, stamp = db.push_transaction(amount, transaction_type, used_tags)
        update_active_transaction(update.effective_chat.id, year, month, day, stamp)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Quanto: {amount}\nTipo: {transaction_type}\nTags: {used_tags}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=stat)



async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    valid, start_year, start_month, end_year, end_month = parse_range(context.args)

    if valid:
        reply = f"Saldo de {start_year}/{start_month} - {end_year}/{end_month}:\n"
        results = db.fetch_transactions_by_range(start_year, start_month, end_year, end_month)
        report = Report(results)
        reply += f"R$ {report.get_balance()}"

    else:
        reply = "Argumentos devem ser numéricos, descrevendo intervalo de meses desejado."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    valid, start_year, start_month, end_year, end_month = parse_range(context.args)

    if valid:
        reply = f"Extrato de {start_year}/{start_month} - {end_year}/{end_month}:\n\n"
        results = db.fetch_transactions_by_range(start_year, start_month, end_year, end_month)
        report = Report(results)
        reply += f"{report.get_history()}"

    else:
        reply = "Argumentos devem ser numéricos, descrevendo intervalo de meses desejado."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def get_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    if len(context.args) == 0:
        year, month, day, stamp = get_active_transaction(update.effective_chat.id)

    elif len(context.args) == 4:
        year = context.args[0]
        month = context.args[1]
        day = context.args[2]
        stamp = context.args[3]

    else:
        reply = "Argumentos devem ser ano, mês, dia e horário da transação, ou nada para ver a transação atual."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
        return

    transaction = db.get_transaction(year, month, day, stamp)

    if not transaction:
        reply = "Transação não encontrada."

    else:
        reply = f"{year}/{month}/{day} {stamp}\n"
        reply += f"R$ {transaction['amount']}\n"
        reply += f"Tipo: {transaction['type']}\n"
        if len(transaction['tags']) > 0:
            reply += f"Tags: {' '.join(transaction['tags'])}\n"
        if len(transaction["info"]) > 0:
            reply += f"{transaction['info']}\n"

        # Atualiza transação ativa para a transação visualizada.
        update_active_transaction(update.effective_chat.id, year, month, day, stamp)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def update_transaction_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 1:
        reply = "Forneça o novo tipo para a transação selecionada."

    else:
        # Atualiza transação selecionada.
        year, month, day, stamp = get_active_transaction(update.effective_chat.id)
        db = Database(update.effective_chat.id)
        result, reply = db.update_transaction_type(year, month, day, stamp, context.args[0])

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def update_transaction_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

        # Atualiza transação selecionada.
        year, month, day, stamp = get_active_transaction(update.effective_chat.id)
        db = Database(update.effective_chat.id)
        result, msg = db.update_transaction_tags(year, month, day, stamp, add_tags, remove_tags)
        reply += msg

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def update_transaction_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 1:
        reply = "Forneça uma descrição para adicionar à transação selecionada."

    else:
        year, month, day, stamp = get_active_transaction(update.effective_chat.id)
        db = Database(update.effective_chat.id)
        result, reply = db.update_transaction_info(year, month, day, stamp, " ".join(context.args))

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)
    reply = " ".join(db.types)

    if len(context.args) > 0:

        if context.args[0] == "adi":
            db.register_types(context.args[1:])
            reply = "Atualizado:\n" + " ".join(db.types)

        elif context.args[0] == "rem":
            db.unregister_types(context.args[1:])
            reply = "Atualizado:\n" + " ".join(db.types)

        else:
            reply = "Uso:\n"
            reply += "  Exibir tipos: /tipos\n"
            reply += "  Adicionar tipos: /tipos adi novo_tipo_1 novo_tipo_2 ...\n"
            reply += "  Remover tipos: /tipos rem tipo_1 tipo_2 ..."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(update.effective_chat.id)

    if len(context.args) == 0:
        reply = " ".join(db.tags)

    elif context.args[0] == "adi":
        db.register_tags(context.args[1:])
        reply = "Atualizado:\n" + " ".join(db.tags)

    elif context.args[0] == "rem":
        db.unregister_tags(context.args[1:])
        reply = "Atualizado:\n" + " ".join(db.tags)

    else:
        reply = "Uso:\n"
        reply += "  Exibir tags: /tags\n"
        reply += "  Adicionar tags: /tags adi nova_tag_1 nova_tag_2 ...\n"
        reply += "  Remover tags: /tags rem tag_1 tag_2 ..."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)



if __name__ == "__main__":

    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO")
    print(f"Log level: {log_level}")

    if log_level == "ERROR":
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=logging.ERROR
        )
    elif log_level == "WARNING":
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=logging.WARNING
        )
    elif log_level == "DEBUG":
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=logging.DEBUG
        )
    else:
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=logging.INFO
        )

    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

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