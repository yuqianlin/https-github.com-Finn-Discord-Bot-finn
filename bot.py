from importlib.metadata import files
import discord
from discord.ext import commands
from discord import guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.model import GuildPermissionsData
from discord_slash.utils.manage_commands import create_choice, create_option
import json
import os
import asyncio

from finance_functions import *
from connect_database import *

TEST = True

try:
    conf = json.load(open("config/config.json"))
    if conf['token'] is None:
        raise Exception
    token = conf['token']
    if TEST:
        token = conf['token_test']
except Exception:
    print("Failed to open config, check it exists and is valid.")

bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
check_reaction = '✅'
guilds = []

def get_guilds():
    return [g.id for g in bot.guilds]

# Slash Commands

@slash.slash(name="lasttradingday", description="Displays the last completed trading day")
async def _Lasttradingday(ctx: SlashContext):
    await ctx.defer()
    last_trade_day = last_trading_day()
    embed = discord.Embed(
        title="Last Trading Day",
        description=last_trade_day,
        color = discord.Color.from_rgb(131, 214, 129))
    await ctx.send(embeds=[embed])

@slash.slash(name="help", description = "Provides a list of possible commands")
async def _Help(ctx: SlashContext):
    await ctx.defer()
    embed = discord.Embed(
        title = "Commands",
        description = 
        """
        You seem to need a bit of assistance! Don't worry, grab some milk and cookies, sit back and relax. What do you need help with? :) \n 
        ==========================================
        \n `/help` - Provides a list of possible commands \n """,
        color=discord.Color.from_rgb(235, 168, 96)
        )
    embed.add_field(name = 'Stock Commands', value = 
    """
    `/companyinfo` - Provides the location, industry, and market capitalization of a given stock \n
    `/stockinfo` - Displays an information preview of a specified ticker \n
    `/stockhistory` - Provides stock history of a given stock \n


    """, inline=True)

    embed.add_field(name = 'Finance Commands', value = 
    """
    `/lasttradingday` - Displays the last completed trading day \n 
    `/options` - Displays either put or call options of a stock \n 

    """, inline=False)

    embed.add_field(name ='Portfolio Commands', value = 
    """
    `/createportfolio` - Creates a portfolio \n 
    `/displayportfolio` - Displays a portfolio with its respective graph \n
    `/addstock` - Adds a stock into a portfolio or creates a new one \n
    `/cleartable` - Clears your current portfolio \n
    `/removestock` - Removes a stock from a portfolio and all of its shares \n

    """, inline=False)   

    embed.set_image(url='https://cdn.discordapp.com/attachments/846084093065953283/924129382090539038/IMG_0005.jpg') 
    await ctx.send(embeds=[embed])
        

# User Input

@slash.slash(
    name = "createPortfolio",
    description = "Command associated with portfolio creation",
    guild_ids = guilds,
    options=[
       
        create_option(
            name="portfoliotype",
            description="What type of portfolio would you like to create?",
            option_type=3,
            required=True,
            choices = [
                create_choice(
                    name = "Equally Weighted Portfolio",
                    value = "EQUAL WEIGHTED"
                ),
                create_choice(
                    name = "Price Weighted Portfolio",
                    value = "PRICE WEIGHTED"
                ),
                create_choice(
                    name = "Market-Capitalization Weighted Portfolio",
                    value = "MARKET WEIGHTED"
                ),
                create_choice(
                    name = "Risky Smart Weighted Portfolio",
                    value = "RISKY"
                ),
                create_choice(
                    name = "Safe Smart Weighted Portfolio",
                    value = "SAFE"
                )
            ]
        ),
        create_option(
            name="tickerlist",
            description="Enter a space-separated list of tickers.",
            option_type=3,
            required=True
        ),
        create_option(
            name="money",
            description="The total amount of money you want to invest (Dollars).",
            option_type=4,
            required=True
        )
    ]
)
async def _CreatePortfolio(ctx: SlashContext, portfoliotype: str, tickerlist: str, money: int): 
    await ctx.defer()
    user_id = ctx.author.id
    remove = remove_table(user_id)
    temp = []
    temp = tickerlist.split()
    new = valid_ticker_list(temp)
    if len(new) <= 1 or len(temp) == 1:
        response = discord.Embed(
            title = "ERROR",
            description = " Please make a portfolio with more than one valid ticker!",
            colour = discord.Color.from_rgb(210, 31, 60)  
        )
        response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png') 
        await ctx.send(embed = response)
    else:
        portfolio_maker(temp, portfoliotype, money, user_id)
        embed = discord.Embed(
                title = f'Portfolio Successfully Created',
                description = f"Here's your portfolio generated using the `{portfoliotype}` method!",
                color=discord.Color.from_rgb(156, 81, 182)
        )
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png') 
        await ctx.send(embed=embed, file=discord.File(f'process/{user_id}.csv'))
        os.remove(f'process/{user_id}.csv')
    
@slash.slash(
    name = "companyInfo",
    description = "Command that provides the location, industry, and market capitalization of a given stock",
    guild_ids = guilds,    
    options = [
        create_option(
            name = "ticker",
            description = "What Ticker would you like to search?",
            required = True,
            option_type = 3
        )
    ]   
)
async def _CompanyInfo(ctx: SlashContext, ticker: str):
    await ctx.defer()
    ticker = ticker.upper()
    comp_info = company_info(ticker)
    if type(comp_info) == str:
        embed = discord.Embed(
        title = f'{ticker} does not have enough data.',
        description = 'Please try another ticker.',
        color=discord.Color.from_rgb(255, 207, 233)
        )
        #embed.set_author(name = 'Finn Bot')
        embed.add_field(name = 'ERROR, sorry!', value = "Please try with a different ticker.", inline = True)
    else:
        location = comp_info[0]
        industry = comp_info[1]
        market_cap = comp_info[2]

        embed = discord.Embed(
            title = f'Company Information for {ticker}',
            description = 'The location of the company, industry of the company and its market capitalization.',
            color=discord.Color.from_rgb(255, 207, 233)
        )
        # embed.set_author(name = 'Finn Bot')
        embed.add_field(name = 'Company Location', value = location, inline=True)
        embed.add_field(name = 'Company Industry', value = industry, inline=True)
        embed.add_field(name = 'Market Capitalization', value = f'${market_cap:,.2f}', inline=True)

    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/846084093065953283/924432164139978772/IMG_0010.jpg') 
    await ctx.send(embeds=[embed])


@slash.slash(
    name = "displayPortfolio", 
    description = "Command associated with displaying portfolio",
    guild_ids = guilds
)
async def _DisplayPortfolio(ctx: SlashContext):
    await ctx.defer()
    user_id = ctx.author.id
    portfolio_dict = get_portfolio(user_id)
    if not portfolio_dict:
        response = discord.Embed(
            title = "ERROR",
            description = " You dont have a portfolio!",
            colour = discord.Color.from_rgb(210, 31, 60)  
        )
        response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png') 
        await ctx.send(embed = response)
    else:    
        data = portfolio_graphs(portfolio_dict, user_id)
        if portfolio_dict:
            (pd.DataFrame.from_dict(portfolio_dict, orient='index')).to_csv(f'process/{user_id}.csv', header=False)
        if data:
            initial_investment = data[0]
            current_value = data[1]
            net_return = current_value - initial_investment
            pct_return = 100 * current_value/initial_investment 
            color=discord.Color.from_rgb(255, 245, 189)
            
            
            embed = discord.Embed(
                title = "Portfolio Returns",
                description = "Here's your graph and investment information!",
                colour = discord.Color.from_rgb(187, 242, 229)    
            )
            # embed.set_author(name ='Finn Bot')
            embed.add_field(name ='Initial Investment', value = "$" + (f'{initial_investment:.2f}'), inline=True)
            embed.add_field(name ='Current Value', value = "$" + (f'{current_value:.2f}'), inline=True) 
            embed.add_field(name ='Net Return', value = "$" + (f'{net_return:.2f}'), inline=True)
            embed.add_field(name ='% Return', value = (f'{pct_return:.2f}') + "%", inline=True)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png') 
            await ctx.send(embeds=[embed], files=[discord.File(f'process/{user_id}.png'), discord.File(f'process/{user_id}.csv')])
            os.remove(f'process/{user_id}.png')
            os.remove(f'process/{user_id}.csv')
        else:
            embed = discord.Embed(
                title = "Oops!",
                description = "Please wait at least one more trading day to view your portfolio's graph!",
                colour = discord.Color.from_rgb(255, 204, 203)    
            )
            # embed.set_author(name ='Finn Bot')
            embed.add_field(name ='Initial Investment', value = "NA", inline=True)
            embed.add_field(name ='Current Value', value = "NA", inline=True) 
            embed.add_field(name ='Net Return', value = "NA", inline=True)
            embed.add_field(name ='% Return', value = "NA", inline=True)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png') 
            await ctx.send(embeds=[embed], file=discord.File(f'process/{user_id}.csv'))
            os.remove(f'process/{user_id}.csv')


# slash command for stock info
@slash.slash(
    name = "stockInfo",                                                     
    description = "Here is the preview of the specified ticker.",
    guild_ids = guilds,
    options = [
        create_option(
            name = "ticker",
            description = "What Ticker would you like to search?",
            required = True,
            option_type = 3
        )
    ]
)
async def _StockInfo(ctx:SlashContext, ticker: str):
    await ctx.defer()
    ticker = ticker.upper()
    data = stock_info(ticker)
    if data['Beta'] == "nan":
        response = discord.Embed(   
        title = "Your Ticker is not valid.",
        description = "Please enter a valid ticker",
        colour = discord.Color.from_rgb(235, 121, 96)    
    )
    else: 
        response = discord.Embed(
        title = f"{ticker} Info",
        colour = discord.Color.from_rgb(235, 121, 96)    
    )
        #response.set_author(name="Finn Bot")
        response.add_field(name='Beta', value=data['Beta'], inline=True)
        response.add_field(name='STD', value=data['STD'], inline=True)
        response.add_field(name='52Wk High', value=data['52Wk High'], inline=True)
        response.add_field(name='52Wk Low', value=data['52Wk Low'], inline=True)
        response.add_field(name='Last Trading Day Open', value=data['Last Trading Day Open'], inline=True)
        response.add_field(name='Last Trading Day Close', value=data['Last Trading Day Close'], inline=True)

    response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924485200421978153/IMG_0010.png')    
    await ctx.send(embed=response)

#slash command for stock history 
@slash.slash(
    name = 'stockHistory',
    description = "Here is your stock's history.",
    guild_ids = guilds,
    options = [
        create_option(
            name = "ticker",
            description = "What ticker would you like to search?",
            required = True,
            option_type = 3
        ),
        create_option(
            name = "start_date",
            description = "What is your start date? (YYYY-MM-DD)",
            required = True,
            option_type = 3
        ),
        create_option(
            name = "end_date",
            description = "What is your end date? (YYYY-MM-DD)",
            required = True,
            option_type = 3
        )
    ]
)
async def _StockHistory(ctx: SlashContext, ticker: str, start_date: str, end_date: str):
    await ctx.defer()
    ticker = ticker.upper() 
    data = stock_history(ticker, start_date, end_date) 

    if type(data) == str:
        embed = discord.Embed(
        title = f'{ticker} does not have enough data.',
        description = 'Please try another ticker.',
        color=discord.Color.from_rgb(255, 207, 233)
        )
        #embed.set_author(name = 'Finn Bot')
        embed.add_field(name = 'ERROR, sorry!', value = "Please try with a different ticker.", inline = True)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494261146243082/History.png')  

    else: 
        if "Dividends" in data.columns:
            embed = discord.Embed(
                title = f"{ticker} History",
                #description = "This is the history of ",
                colour = discord.Color.from_rgb(235, 121, 96)
            )

            #embed.set_author(name="Finn Bot")
            embed.add_field(name="Open", value=data["Open"].to_string(), inline=True)
            embed.add_field(name="Close", value=data["Close"].to_string(), inline=True)
            embed.add_field(name="High", value=data["High"].to_string(), inline=True)
            embed.add_field(name="Low", value=data["Low"].to_string(), inline=True)
            embed.add_field(name="Volume", value=data["Volume"].to_string(), inline=True)
            embed.add_field(name="Dividends", value=data["Dividends"].to_string(), inline=True)
            embed.add_field(name="Stock Splits", value=data["Stock Splits"].to_string(), inline=True)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494261146243082/History.png') 
        else:
            embed = discord.Embed(
                title = f"{ticker} History",
                description = "Sorry, the dates you entered are invalid.",
                colour = discord.Color.from_rgb(235, 121, 96)
            )

            #embed.set_author(name = 'Finn Bot')
            embed.add_field(name = 'ERROR, sorry!', value = "Please try with another set of dates.", inline = True)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494261146243082/History.png') 
    
    await ctx.send(embeds=[embed])




# slash command for options (HAVEN'T BEEN TESTED YET)
@slash.slash(
    name = "options",
    description = "Here is the preview of the options available for your stock",
    guild_ids = guilds,
    options = [
        create_option(
            name = "ticker",
            description = "What Ticker would you like to search?",
            required = True,
            option_type = 3
        ),

        create_option(
            name = "range_length",
            description = "What range are you looking in?",
            required = True,
            option_type = 4
        ),
        create_option(
            name = "put_or_call",
            description = "Are you looking for a put or call option?",
            required = True,
            option_type = 3,
            choices = [
                create_choice(
                    name = "put",
                    value = "put"
                ),
                create_choice(
                    name = "call",
                    value = "call"
                )        
            ]
        )
    ]
)
async def _Options(ctx:SlashContext, ticker: str, range_length: int, put_or_call: str):
    await ctx.defer()
    ticker = ticker.upper()
    embed = discord.Embed(
        title = f"{ticker} Option Info",
        colour = discord.Color.from_rgb(235, 121, 96)    
    )
    
    data = options(ticker, range_length, put_or_call)
    if type(data) == str:
        #embed.set_author(name = 'Finn Bot')
        embed.add_field(name = 'ERROR, sorry!', value = "Please try with a different ticker.", inline = True)
        
    else:
        
        #embed.set_author(name="Finn Bot")
        embed.add_field(name='Last Trade Date', value=data['lastTradeDate'].to_string(), inline=True)
        embed.add_field(name='Strike', value=data['strike'].to_string(), inline=True)
        embed.add_field(name='Last Price', value=data['lastPrice'].to_string(), inline=True)
        embed.add_field(name='Bid', value=data['bid'].to_string(), inline=True)
        embed.add_field(name='Ask', value=data['ask'].to_string(), inline=True)
        embed.add_field(name='Change', value=data['change'].to_string(), inline=True)
        embed.add_field(name='Pct Change', value=data['percentChange'].to_string(), inline=True)
        embed.add_field(name='Volume', value=data['volume'].to_string(), inline=True)
        embed.add_field(name='Open Interest', value=data['openInterest'].to_string(), inline=True)
        embed.add_field(name='Implied Volatility', value=data['impliedVolatility'].to_string(), inline=True)
        embed.add_field(name='In the money?', value=data['inTheMoney'].to_string(), inline=True)
        embed.add_field(name='Contract Symbol', value=data['contractSymbol'].to_string(), inline=False)
        
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924485200421978153/IMG_0010.png')    
    await ctx.send(embeds=[embed])



# # slash command for sharpe ratio (not tested)
# @slash.slash(
#     name = "sharpeRatio",
#     description = "Command that provides the sharpe ratio of a stock",
#     guild_ids = guilds,
#     options = [
#         create_option(
#             name = "ticker",
#             description = "What Ticker would you like to search?",
#             required = True,
#             option_type = 3
#         )
#     ]
# )
# async def _SharpeRatio(ctx:SlashContext, ticker:str, start_date:str, end_date:str):
#     await ctx.defer()
#     ticker = ticker.upper()
#     response = discord.Embed(
#         title = f"{ticker} Sharpe Ratio",
#         description = "Command that provides the sharpe ratio of a stock",
#         colour = discord.Color.from_rgb(235, 121, 96)
#     )
#     ratio = sharpe_ratio(ticker, start_date, end_date)
#     response.set_author(name='Finn Bot')
#     response.add_field(name='Sharpe Ratio', value = ratio)
#     await ctx.send(embed=response)


@slash.slash(
    name = "addstock", 
    description = "Command to add a stock to your portfolio",
    guild_ids = guilds,
    options = [
        create_option(
            name = "ticker",
            description = "What Ticker would you like to add?",
            required = True,
            option_type = 3
        ),
        create_option(
            name = "qnty",
            description = "Number of shares to purchase",
            required = True,
            option_type = 3
        )
    ]
)
async def _Addstock(ctx:SlashContext, ticker:str, qnty: str):
    await ctx.defer()
    ticker = ticker.upper()
    user_id = ctx.author.id
    current_portfolio = get_portfolio(user_id)
    filter_tickerlist = valid_ticker_list([ticker])
    if not current_portfolio:
        reply = add_stock(user_id, ticker, float(qnty), last_trading_day())
        response = discord.Embed(
            title = "Success",
            description = f'{qnty} shares of {reply} successfully added to portfolio',
            colour = discord.Color.from_rgb(0, 168, 107)
        )
    elif ticker not in current_portfolio and filter_tickerlist:
        reply = add_stock(user_id, ticker, float(qnty), last_trading_day())
        response = discord.Embed(
            title = "Success",
            description = f'{qnty} shares of {reply} successfully added to portfolio',
            colour = discord.Color.from_rgb(0, 168, 107)
        )
    else:
        response = discord.Embed(
            title = "Error",
            description = f"Ticker: {ticker} - The ticker you have chosen is invalid or already exists in your portfolio",    # MAKE THIS PRETTY
            colour = discord.Color.from_rgb(210, 31, 60)
        )
    #response.set_author(name='Finn Bot')
    response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png')
    await ctx.send(embed=response)
    
    
    
@slash.slash(
    name = "removeStock",
    description = "Command to remove a stock to your portfolio",
    guild_ids = guilds,
    options = [
        create_option(
            name = "ticker",
            description = "What Ticker would you like to remove?",
            required = True,
            option_type = 3
        )
    ]
)
async def _RemoveStock(ctx:SlashContext, ticker:str):
    await ctx.defer()
    ticker = ticker.upper()
    user_id = ctx.author.id
    current_portfolio = get_portfolio(user_id)
    if not current_portfolio:
        response = discord.Embed(
            title = "Error",
            description = " You dont have a portfolio!",
            colour = discord.Color.from_rgb(210, 31, 60)  
        )
    elif ticker in current_portfolio:
        reply = remove_stock(user_id, ticker)
        response = discord.Embed(
            title = "Success",
            description = f'{reply} has been successfully removed from the portfolio',
            colour = discord.Color.from_rgb(0, 168, 107)
        )
    else:
        response = discord.Embed(
            title = "Error",
            description = f"Ticker: {ticker} - The ticker you have chosen to remove is invalid or does not exist in your portfolio",
            colour = discord.Color.from_rgb(210, 31, 60)  
        )
    #response.set_author(name='Finn Bot')
    response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png')
    await ctx.send(embed=response)

@slash.slash(
    name = "clearTable",
    description = "Command to remove your current table",
    guild_ids = guilds
)

async def _ClearTable (ctx: SlashContext):
    await ctx.defer()
    user_id = ctx.author.id
    temp = remove_table(user_id)
    response = discord.Embed(
        title = "Success!",
        description = "Your portfolio has been removed!",
        colour = discord.Color.from_rgb(210, 31, 60)
    )
    response.set_thumbnail(url='https://cdn.discordapp.com/attachments/908565324390080572/924494257740468285/Display_Portfolio.png')
    await ctx.send(embed = response)


# # slash command for correlation (not tested)
# @slash.slash(
#    name = "correlation",
#    description = "Command that returns the correlation of two stocks",
#    guild_ids = guilds,
#    options = [
#        create_option(
#            name = "ticker1",
#            description = "What Ticker would you like to search?",
#            required = True,
#            option_type = 3
#       ),
#        create_option(
#            name = "ticker2",
#            description = "What Ticker would you like to search?",
#            required=True,
#            option_type = 3
#         )
#     ]
# )
# async def _Correlation(ctx:SlashContext, ticker1: str, ticker2: str):
#    ticker1 = ticker1.upper()
#    ticker2 = ticker2.upper()
#    temp = 
#    response = discord.Embed(
#        title = f"{ticker1} and {ticker2} Correlation",
#        description = "Correlation between your two tickers are: {}"
#    )

# Events
@bot.event
async def on_ready():
    if not os.path.exists('process'):
        os.mkdir('process')
    await bot.change_presence(activity=discord.Game('Listening for holiday STOCKings | prefix: /'), status="dnd")
    print('Bot Initialized')


@bot.event
async def on_guild_join(guild):
    if guild.id not in guilds:
        guilds.append(guild.id)
    print(guilds)
        

@bot.listen()
async def on_message(message):
    message_content = message.content
    try:
        if message_content == "Hello" and not message.author.bot: 
            await message.channel.send("Hello")
    except TypeError:
        return None


def start_bot():
    bot.run(token)







    