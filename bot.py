import logging
from CryptoPayments import CryptoPayments
from telegram import (Update,
                      ForceReply,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup)
from telegram.ext import (Updater,
                          ConversationHandler,
                          CommandHandler,
                          MessageHandler,
                          Filters,
                          CallbackContext,
                          CallbackQueryHandler)

# bot token from botfather
TOKEN = "2034281759:AAFJ8naFmFkdx15DFptRoPUscKuck29Mjag"
# api keys from coinpayments
API_KEY = 'a54fa86f68dc895fcdb42d9d50a12133bd8ab9be028fb5b007d2aa1beed48474'
API_SECRET = '1E7A4f4da16A49Be4cF5699211125E33b3Ff5884e0250F52Adf7Acd085938b89'

client = CryptoPayments(API_KEY, API_SECRET)
EMAIL = 0

PRODUCTS = [{
    'id': 0,
    'name': 'Sample Product 1',  # product name
    'desc': 'Sample Product 1 Description Lorem Ipsum',  # product Description
    'image': 'shoppingbag-.jpg',  # full path of product image
    'price': 150 # price in USD
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def buy(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Product Selected ...")
    context.user_data['pid'] = int(query.data.split(":")[1])
    context.bot.send_message(chat_id=update.effective_message.chat_id,
                             text='Please input your email\nMake sure it is correct\nIt will be used for delivery')
    return EMAIL


def check_payment(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    txid = query.data.split(":")[1]
    query.answer()
    context.bot.send_message(chat_id=update.effective_message.chat_id,
                             text='checking the status of your transaction ...')
    info = client.getTransactionInfo(txid)
    if info['error'] == 'ok':
        message = "⚙️ Payment Check\n"\
                  f"Ordre ID : {txid}\n"\
                  f"⏳ {info['status_text']}\n"\
                  "If you have already sent, please wait for confirmations\n"\
                  "After confirmation you will receive your ordre automatically to your email"
    else:
        print(info)
        message = "⚙️ Payment Check\n"\
                  f"Ordre ID : {txid}\n"\
                  "Error while checking the status of your paiment "
    context.bot.send_message(chat_id=update.effective_message.chat_id,
                             text=message)


def email(update: Update, context: CallbackContext):
    # Receive Email and creat transaction
    EMAIL = update.message.text
    prod = PRODUCTS[int(context.user_data['pid'])]
    data = {}
    data['cmd'] = 'create_transaction'
    data['amount'] = prod['price']
    data['currency1'] = 'USD'
    data['currency2'] = 'BTC'
    data['buyer_email'] = EMAIL
    data['item_number'] = prod['id']
    data['item_name'] = prod['name']
    data['custom'] = update.message.from_user['username']

    transaction = client.createTransaction(data)
    if transaction['error'] == 'ok':
        options = []
        options.append(InlineKeyboardButton(f"payment receipt",
                                            callback_data=f"check_payment:{transaction['txn_id']}",))
        reply_markup = InlineKeyboardMarkup([options])
        # paiment info message
        message = f"⚙️ ORDRE ID : <b>{transaction['txn_id']}</b>\n"\
                  f"send <b>{transaction['amount']}</b> in BTC\n"\
                  f"Wallet :  <b>{transaction['address']}</b>\n"\
                  f"Click on ‘𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗥𝗘𝗖𝗘𝗜𝗣𝗧’ once you make payment"
        update.message.reply_text(message, reply_markup=reply_markup,parse_mode='HTML')
        # paiment qr code
        update.message.reply_photo(transaction['qrcode_url'])
        # paiment qddress
        update.message.reply_text(f"{transaction['address']}")
        message = "Notice ❗️\n"\
                  "we accept BITCOINS Only\n" \
                  "(other tokens can not be recovered)"
        update.message.reply_text(message)
    else:
        update.message.reply_text(f"ERROR {transaction['error']} please "
                                  "contact <telegram user of admin> to fix it")
        print(transaction)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    # start message
    message = fr'🔱 Welcome {user.mention_markdown_v2()} 🔱'\
              f'\n💠Select your Subscription 🤖 '\
              f'\n🔽🔽🔽🔽🔽🔽'\
              f'\nType /subscription to list available subscriptions'\
              f'\nType /about\_us for more information about this bot'
    update.message.reply_markdown_v2(
        message,
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    # about us messsage
    message = ""
    update.message.reply_text(message)


def list_command(update: Update, context: CallbackContext) -> None:
    for prod in PRODUCTS:
        options = []

        # buttons
        price_usd = prod['price']
        price_btc = price_usd * float(client.rates()["USD"]["rate_btc"])
        options.append(InlineKeyboardButton(f"{price_usd}$     \n     {price_btc:.9f} BTC",
                                            callback_data=f"select_product:{prod['id']}",))
        reply_markup = InlineKeyboardMarkup([options])
        message = f"<b>{prod['name']}</b>\n{prod['desc']}"
        update.message.reply_photo(open(prod['image'], 'rb'))
        update.message.reply_text(message,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


def main() -> None:

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("about_us", help))
    dispatcher.add_handler(CommandHandler("subscription", list_command))
    dispatcher.add_handler(CallbackQueryHandler(check_payment, pattern=r'^check_payment:?.+$'))
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy, pattern=r'^select_product:?.+$')],
        states={
            EMAIL: [MessageHandler(Filters.regex(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), email)],
        },
        fallbacks=[CommandHandler('cancel', start)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
