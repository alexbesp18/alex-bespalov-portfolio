
# --- imports

import yfinance as yf
import logging
import os
import json
from datetime import datetime
from yfinance.exceptions import YFRateLimitError
import traceback
import signal

# logger = logging.basicConfig()


console_handler = logging.StreamHandler()
file_handler    = logging.FileHandler('trading_scanner.log', mode='a', encoding='utf-8')

file_formatter    = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)

logger = logging.getLogger('trading_scanner')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

console_logger = logging.getLogger("trading_scanner.console")
console_logger.setLevel(logging.INFO)
console_logger.addHandler(console_handler)
console_logger.propagate = False

file_logger = logging.getLogger("trading_scanner.file")
file_logger.setLevel(logging.WARNING)
file_logger.addHandler(file_handler)
file_logger.propagate = False


# --- data

running = True

task_list       = []
config_prev     = None
config_curr     = None
config_filename = "stock_options_wx_v3.jsonl"
stocks         = {}



# --- functions

# task = {
#     "ticker"     : ticker,
#     "date"       : date,
#     "price"      : data_entry['price'],
#     "type"       : data_entry['type'],
#     "otm_min"    : data_entry['otm_min'],
#     "otm_max"    : data_entry['otm_max'],
#     "start_date" : data_entry['start_date'],
#     "end_date"   : data_entry['end_date'],
# }
def ProcessRequest(task):
    data = None
    
    # stock = task.get('ticker_object', None)
    stock = stocks[task['ticker']]
    if(stock):
        typ  = task['type']
        date = task['date']

        chain = stock.option_chain(date)
        if(typ == 'Call'):
            data = chain.calls
        elif(typ == 'Put'):
            data = chain.puts
        else:
            pass
    
    if(not data.empty):
        # filter for OTM
        data = data[data['inTheMoney']==False]

        # what's the nuance between price and strike? Add price to the task.
        price        = task['price']
        openInterest = task['open_interest']
        
        otm_min = task['otm_min']
        otm_max = task['otm_max']
        otm_min_coeff = 1 + otm_min/100
        otm_max_coeff = 1 + otm_max/100

        otm_strikes = data[(data['strike'] > (price * otm_min_coeff)) & (data['strike'] < (price * otm_max_coeff)) & (data['openInterest'] > openInterest)]
        return (otm_strikes.shape[0] > 0)
    else:
        return False
    


def CheckConfig():
    global config_prev, config_curr

    if(os.path.exists(config_filename)):
        config_prev = config_curr
        config_curr = os.path.getmtime(config_filename)

        if(config_prev and (config_prev != config_curr)):
            return True
        else:
            return False
    else:
        logger.critical("!!! Config file got deleted since last config read.")



def DateList(dates, date_start, date_end):
    res = []

    date_format = "%Y-%m-%d"
    dt_start = datetime.strptime(date_start, date_format)
    dt_end   = datetime.strptime(date_end,   date_format)

    for date in dates:
        dt = datetime.strptime(date, date_format)
        if((dt_start <= dt) and (dt < dt_end)): # which of these should be inclusive?
            res.append(date)
    
    return res


# jsonl -> data_list
# data_list -> task_list; ticker-date pairs, with the rest of parameters for postproc analysis
def ProcessConfig():
    global task_list, stocks
    
    task_list = []
    stocks    = {}
    
    # --- read the config file
    data_list = []
    try:
        with open(config_filename, 'r') as f:
            for line in f:
                try:
                    # Remove whitespace and load the JSON from the line
                    data_list.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping a malformed line: {line.strip()}")
    except FileNotFoundError:
        logger.critical("!!! Config file not found. Exiting")
        exit()

    if not data_list:
        print("Error: No valid JSON objects found in the file.")
    # -------------------------------------------

    
    


    # --- add a task per date
    for data_entry in data_list:
        if(data_entry['enabled']):
            ticker = data_entry['ticker']
            
            try:
                stock            = yf.Ticker(ticker)
                stocks[ticker] = stock
            except YFRateLimitError:
                logger.error("! YFinance rate limit")
            except Exception as e:
                logger.error(f"! Couldn't create ticker object; unprocessed error {e.__class__.__name__}")
            
                # task_list.append(data_entry)
            
            price = stock.info.get('currentPrice')

            # filter dates
            date_list = DateList(list(stock.options), data_entry['start_date'], data_entry['end_date'])
            for date in date_list:
                task = {
                    "ticker"        : ticker,
                    "date"          : date,
                    "price"         : price,
                    "strike"        : data_entry['strike'],
                    "type"          : data_entry['type'],
                    "otm_min"       : data_entry['otm_min'],
                    "otm_max"       : data_entry['otm_max'],
                    "open_interest" : data_entry['open_interest']
                    # "start_date" : data_entry['start_date'],
                    # "end_date"   : data_entry['end_date'],
                }
                task_list.append(task)
    
    logger.info(f"> Tickers loaded:  {len(stocks)}")
    logger.info(f"> Tasks generated: {len(task_list)}")
        



def SendNotification(task):
    ticker        = task['ticker']
    date          = task['date']
    typ           = task['type']
    strike        = task['strike']
    open_interest = task['open_interest']

    logger.info(f"> Found OTM options: {ticker}, {date}, {typ}, strike:{strike}, OI:{open_interest}")



def signal_handler(sig, frame):
    global running
    running = False
signal.signal(signal.SIGINT, signal_handler)

def main():
    global task_list

    try:
        ProcessConfig()
    except Exception as e:
        # logger.critical("! Config error")
        pass

    global running
    while(running):
        try:
            # process requests
            # process config, remake the tasks
            for task in task_list:
                if(ProcessRequest(task)):
                    SendNotification(task)

            if(CheckConfig()):
                ProcessConfig()
        except KeyboardInterrupt:
            logger.info(f". exiting upon Ctrl-C")
            break
        except Exception as e:
            logger.error(f"! {e.__class__.__name__}")
            file_logger.error(f"! {traceback.format_exc()}")
            break

if __name__ == "__main__":
    main()