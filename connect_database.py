from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, DowngradingConsistencyRetryPolicy
from cassandra.query import tuple_factory
from time import strftime, localtime
import json


with open('config/config.json', 'r') as config:
    conf = json.load(config)
    
cloud_config = {'secure_connect_bundle': conf['secure_connect_bundle']}
auth_provider = PlainTextAuthProvider(conf["CLIENT_ID"], conf["CLIENT_SECRET"]) # authenticate
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect('portfolios')  # select keyspace

# Adds a dataframe straight to the portfolio
def add_portfolio(portfolio_df, uuid: int, settledate: str):
    for ticker in portfolio_df.index:
        add_stock(uuid, ticker, float(portfolio_df.loc[ticker]), settledate)
    portfolio_df.to_csv(f'process/{uuid}.csv')


# Adds a stock to a user's portfolio
def add_stock(uuid: int, ticker: str, qnty: float, settledate: str):
    session.execute(f"""
                    CREATE TABLE IF NOT EXISTS user{uuid} (
                        ticker text,
                        qnty decimal,
                        settledate text,
                        PRIMARY KEY (ticker, qnty, settledate)
                    )
                    """)
    session.execute(f"INSERT INTO user{uuid} (ticker, qnty, settledate) VALUES ('{ticker}', {qnty}, '{settledate}')")
    return ticker


# Remove a stock from a user's portfolio
def remove_stock(uuid: int, ticker: str):
    session.execute(f"""
                    DELETE FROM user{uuid}
                    WHERE ticker = '{ticker}'
                    """)
    return ticker


def remove_table(uuid: int):
    session.execute(f"""
                    DROP TABLE IF EXISTS user{uuid}
                    """)
    return "Removed"

# Pull Portfolio from user
def get_portfolio(uuid: int) -> dict:
    try:
        my_portfolio = session.execute(f'SELECT (ticker, qnty, settledate) FROM user{uuid}')
    except Exception:
        return None
    
    portfolio = {}
    for stock in my_portfolio:
        if stock:
            ticker = stock.ticker__qnty__settledate[0]
            qnty = stock.ticker__qnty__settledate[1]
            settledate = stock.ticker__qnty__settledate[2]
            portfolio[ticker] = [qnty, settledate]
    return portfolio
    

