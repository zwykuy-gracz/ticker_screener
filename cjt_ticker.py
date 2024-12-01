import logging
import os
import yfinance as yf
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename="ticker.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

y, BUTTONS = range(2)
x, ABOUT, DVD, MOMENTUM, NEWS, DONE = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Type /t [ticker] to get info")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await context.bot.set_chat_menu_button()


def build_keybord(symbol) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(f"About ${symbol.upper()}", callback_data=str(ABOUT)),
            InlineKeyboardButton(f"DVD ${symbol.upper()}", callback_data=str(DVD)),
        ],
        [
            InlineKeyboardButton(f"News ${symbol.upper()}", callback_data=str(NEWS)),
            InlineKeyboardButton(
                f"Momentum ${symbol.upper()}", callback_data=str(MOMENTUM)
            ),
        ],
        [InlineKeyboardButton("Done", callback_data=str(DONE))],
    ]

    return InlineKeyboardMarkup(keyboard)


async def about_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    # logger.info("query %s started the conversation.", symbol)
    ticker = yf.Ticker(symbol)

    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(
        text=f"About {symbol}\n\n{ticker.info['longBusinessSummary']}",
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="About. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def dvd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # logger.info("query %s started the conversation.", update)
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)
    try:
        dvd_value = ticker.info["lastDividendValue"]
        now = datetime.fromtimestamp(ticker.info["lastDividendDate"])
        formatted = now.strftime("%Y-%m-%d")

        await query.answer()

        await query.edit_message_text(
            text=f"Last dvd: ${dvd_value}, {formatted}",
        )
    except:
        await query.edit_message_text(
            text="No DVD",
        )

    reply_markup = build_keybord(symbol)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Last DVD. Pick another",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def news_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    msg = (
        f"News for {ticker.info['longName']}:\n\n"
        f"{ticker.news[0]['title']}\n"
        f"Time published: {datetime.fromtimestamp(ticker.news[0]['providerPublishTime'])}\n"
        f"Link: {ticker.news[0]['link']}\n"
        "----------------------------------------\n"
        f"{ticker.news[1]['title']}\n"
        f"Time published: {datetime.fromtimestamp(ticker.news[1]['providerPublishTime'])}\n"
        f"Link: {ticker.news[1]['link']}\n"
        "----------------------------------------\n"
        f"{ticker.news[2]['title']}\n"
        f"Time published: {datetime.fromtimestamp(ticker.news[2]['providerPublishTime'])}\n"
        f"Link: {ticker.news[2]['link']}"
    )
    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(text=msg)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Company news. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def momentum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    hist_1mo = ticker.history(period="1mo").iloc[0]["Open"].round(2)
    hist_3mo = ticker.history(period="3mo").iloc[0]["Open"].round(2)
    hist_6mo = ticker.history(period="6mo").iloc[0]["Open"].round(2)
    hist_12mo = ticker.history(period="1y").iloc[0]["Open"].round(2)
    hist_YTD = ticker.history(period="ytd").iloc[0]["Open"].round(2)
    current_price = ticker.info["currentPrice"]
    msg = f"""{ticker.info['longName']} momentum\n
        1 month return: {((current_price / hist_1mo - 1) * 100).round(2)}%\n
        3 months return: {((current_price / hist_3mo - 1) * 100).round(2)}%\n
        6 months return: {((current_price / hist_6mo - 1) * 100).round(2)}%\n
        12 months return: {((current_price / hist_12mo - 1) * 100).round(2)}%\n
        YTD return: {((current_price / hist_YTD - 1) * 100).round(2)}%\n
        50 day MA: ${ticker.info['fiftyDayAverage']}\n
        200 day MA: ${ticker.info['twoHundredDayAverage']}\n
        """
    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(text=msg)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Momentum. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")

    return ConversationHandler.END


# drukuje guziki /t
async def ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # logger.info("User %s started the conversation.", user.first_name)

    symbol = context.args[0]
    try:
        ticker = yf.Ticker(symbol.upper())
        daily_prec_change = (
            (ticker.info["currentPrice"] - ticker.info["previousClose"])
            / ticker.info["previousClose"]
            * 100
        )
        basic_info = f"""${symbol.upper()} {ticker.info['longName']}\n
        Current Price: ${ticker.info['currentPrice']}, {round(daily_prec_change, 2)}%\n
        Market Cap: ${ticker.info['marketCap']:_}\n
        52 Week High: ${ticker.info['fiftyTwoWeekHigh']}\n
        52 Week Low: ${ticker.info['fiftyTwoWeekLow']}\n
        52 Change: ${round(ticker.info['52WeekChange']*100,2)}\n
        Volume: {ticker.info['volume']:_}\n
        Average Volume: {ticker.info['averageVolume']:_}"""

        reply_markup = build_keybord(symbol)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=basic_info
        )

        await update.message.reply_text(
            text="Basic info. Pick one", reply_markup=reply_markup
        )

        return BUTTONS
    except KeyError:
        await update.message.reply_text("ogarnij się!")


def main() -> None:
    application = Application.builder().token(os.getenv("TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CommandHandler("t", ticker_command),
        ],
        states={
            BUTTONS: [
                CallbackQueryHandler(about_company, pattern="^" + str(ABOUT) + "$"),
                CallbackQueryHandler(dvd, pattern="^" + str(DVD) + "$"),
                CallbackQueryHandler(news_company, pattern="^" + str(NEWS) + "$"),
                CallbackQueryHandler(momentum, pattern="^" + str(MOMENTUM) + "$"),
                CallbackQueryHandler(done, pattern="^" + str(DONE) + "$"),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
