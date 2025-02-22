import os
import html
import json
import logging
import traceback
import yfinance as yf
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
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
    await update.message.reply_text("Use /start to test this bot.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    # chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML
    await context.bot.send_message(
        chat_id=os.getenv("MY_ID"), text=message, parse_mode=ParseMode.HTML
    )


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
        message_thread_id=query.message.message_thread_id,
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
        message_thread_id=query.message.message_thread_id,
        text="Last DVD. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def news_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    date1 = datetime.fromisoformat(
        ticker.news[0]["content"]["pubDate"].replace("Z", "+00:00")
    )
    dt1 = date1.strftime("%Y-%m-%d %H:%M:%S")
    date2 = datetime.fromisoformat(
        ticker.news[1]["content"]["pubDate"].replace("Z", "+00:00")
    )
    dt2 = date2.strftime("%Y-%m-%d %H:%M:%S")
    date3 = datetime.fromisoformat(
        ticker.news[2]["content"]["pubDate"].replace("Z", "+00:00")
    )
    dt3 = date3.strftime("%Y-%m-%d %H:%M:%S")

    links = []
    for i in range(3):
        try:
            links.append(ticker.news[i]["content"]["clickThroughUrl"]["url"])
        except TypeError:
            links.append(ticker.news[i]["content"]["canonicalUrl"]["url"])

    msg = (
        f"News for {ticker.info['longName']}:\n\n"
        f"Title: {ticker.news[0]['content']['title']}\n\n"
        f"Summary: {ticker.news[0]['content']['summary']}\n\n"
        f"Time published: {dt1}\n"
        f"Link: {links[0]}\n"
        "----------------------------------------\n"
        f"Title: {ticker.news[1]['content']['title']}\n\n"
        f"Summary: {ticker.news[1]['content']['summary']}\n\n"
        f"Time published: {dt2}\n"
        f"Link: {links[1]}\n"
        "----------------------------------------\n"
        f"Title: {ticker.news[2]['content']['title']}\n\n"
        f"Summary: {ticker.news[2]['content']['summary']}\n\n"
        f"Time published: {dt3}\n"
        f"Link: {links[2]}"
    )
    await query.answer()

    reply_markup = build_keybord(symbol)

    await query.edit_message_text(text=msg)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=query.message.message_thread_id,
        text="Company news. Pick another one",
        reply_markup=reply_markup,
    )

    return BUTTONS


async def momentum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # logger.info("User %s started the conversation.", update)
    query = update.callback_query
    symbol = query.message.reply_markup.inline_keyboard[0][0].text.split()[1][1:]
    ticker = yf.Ticker(symbol)

    hist_1mo = ticker.history(period="1mo").iloc[0]["Open"].round(2)
    hist_3mo = ticker.history(period="3mo").iloc[0]["Open"].round(2)
    hist_6mo = ticker.history(period="6mo").iloc[0]["Open"].round(2)
    hist_12mo = ticker.history(period="1y").iloc[0]["Open"].round(2)
    hist_YTD = ticker.history(period="ytd").iloc[0]["Open"].round(2)
    current_price = ticker.info["currentPrice"]
    msg = f"""{ticker.info['longName']} ${current_price}\nMomentum\n
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
        message_thread_id=query.message.message_thread_id,
        text="Momentum. Pick another one",
        reply_markup=reply_markup,
    )
    return BUTTONS


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")

    return ConversationHandler.END


# prints buttons /t
async def ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User %s started the conversation.", update)
    chat_type = update.message.chat.type
    chat_id = update.message.chat.id
    thread_id = update.message.message_thread_id

    with open("selected_room.json", "r+") as f:
        data = json.load(f)
    if (
        chat_type == "private"
        or str(chat_id) in data
        and thread_id == data[str(chat_id)]
    ):

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
                chat_id=update.effective_chat.id,
                message_thread_id=update.message.message_thread_id,
                text=basic_info,
            )

            await update.message.reply_text(
                text="Basic info. Pick one", reply_markup=reply_markup
            )

            return BUTTONS
        except KeyError:
            await update.message.reply_text("Bad ticker. Try again")


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
        fallbacks=[CommandHandler("start", start), CommandHandler("t", ticker_command)],
        conversation_timeout=40,
    )
    application.add_handler(conv_handler)

    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
