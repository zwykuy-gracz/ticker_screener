import logging
import os
import yfinance as yf
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
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

BUTTONS = range(1)


def about_company(ticker):
    return ticker.info["longBusinessSummary"]


def momentum(ticker):
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
        """
    return msg


def news_company(ticker):
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
    return msg


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Type /t [ticker] to get info")


# await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await context.bot.set_chat_menu_button()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    await query.answer()
    # await query.edit_message_text(text=f"Selected option: {query.data}")
    ticker = yf.Ticker(query.data.split()[1])

    if query.data.startswith("News"):
        msg = news_company(ticker)
        await query.edit_message_text(text=msg)
    elif query.data.startswith("DVD"):
        now = datetime.fromtimestamp(ticker.info["lastDividendDate"])
        formatted = now.strftime("%Y-%m-%d")
        await query.edit_message_text(
            text=f"Last dvd: {ticker.info['lastDividendValue']}, {formatted}"
        )

    elif query.data.startswith("About"):
        await query.edit_message_text(text=about_company(ticker))

    elif query.data.startswith("Momentum"):
        msg = momentum(ticker)
        await query.edit_message_text(text=msg)


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")

    return ConversationHandler.END


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        keyboard = [
            [
                InlineKeyboardButton(f"News {symbol}", callback_data=f"News {symbol}"),
                InlineKeyboardButton(f"DVD {symbol}", callback_data=f"DVD {symbol}"),
            ],
            [
                InlineKeyboardButton(
                    f"About {symbol}", callback_data=f"About {symbol}"
                ),
                InlineKeyboardButton(
                    f"Momentum {symbol}", callback_data=f"Momentum {symbol}"
                ),
            ],
            [InlineKeyboardButton("Done", callback_data="Done")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(basic_info, reply_markup=reply_markup)
    except KeyError:
        await update.message.reply_text("ogarnij się!")


def main() -> None:
    """Run the bot."""

    application = Application.builder().token(os.getenv("TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[
            application.add_handler(CommandHandler("start", start)),
            application.add_handler(CommandHandler("help", help_command)),
            application.add_handler(CommandHandler("t", ticker_command)),
        ],
        states={BUTTONS: [CallbackQueryHandler]},
    )
    application.add_handler(conv_handler)
    # application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
