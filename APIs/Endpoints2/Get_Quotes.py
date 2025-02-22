
from fastapi import HTTPException, FastAPI, Response, status, APIRouter,Query
from fastapi.responses import JSONResponse
from schemas.Sector import serializeList2

import pandas as pd

import time

from datetime import datetime



import os

from config.db import get_database 




Get_Quotes = APIRouter()
api_key = os.getenv("API_KEY")


def get_Quotes_collection():
    db = get_database()
    Quotes=db["Quotes"]
    Quotes.create_index([("_id", 1)])
    return Quotes

QuotesCollection=get_Quotes_collection()


def get_FOREX_Quotes_collection():
    db = get_database()
    FOREX_Quotes=db["FOREX_Quotes"]
    FOREX_Quotes.create_index([("_id", 1)])
    return FOREX_Quotes

FOREX_QuotesCollection=get_FOREX_Quotes_collection()



def get_STOCKIndexes_Quotes_collection():
    db = get_database()
    STOCKIndexes_Quotes=db["STOCKIndexes_Quotes"]
    STOCKIndexes_Quotes.create_index([("_id", 1)])
    return STOCKIndexes_Quotes

STOCKIndexes_QuotesCollection=get_STOCKIndexes_Quotes_collection()






import time
from datetime import datetime

def get_Quotes_Data(symbol,start_date, end_date,Frequency,Collection):
    try:

        if(start_date):
            print(f">>> symbol:{symbol}, start_date: {start_date}, end_date: {end_date}, Frequency: {Frequency}")

        if(not start_date):
            start_date="1950-01-01"

        if(not end_date):
            current_date = datetime.now()
            formatted_current_date = current_date.strftime("%Y-%m-%d")
            end_date=formatted_current_date
        

        if(not Frequency):
            raise HTTPException(status_code=404, detail="Frequency type required")



        if Collection=="QuotesCollection":
            CollectiontoWork=QuotesCollection

        if Collection=="FOREXQuotesCollection":
            CollectiontoWork=FOREX_QuotesCollection

        if Collection=="STOCKIndexesQuotesCollection":
            CollectiontoWork=STOCKIndexes_QuotesCollection

            

        ReturnedQuotes = CollectiontoWork.find({
            "$and": [
                {"date": {"$gte": start_date, "$lte": end_date}},
                {"symbol": symbol}  
            ]
        }).sort("date", 1)




        if Frequency=="D":
            daily_data = serializeList2(ReturnedQuotes)
            result=daily_data



        if Frequency=="W":
            print("type of ReturnedQuotes ",type(ReturnedQuotes))
            ReturnedQuotes_df = pd.DataFrame(list(ReturnedQuotes))
            print(">> ReturnedQuotes in a dataframe format ")
            print(ReturnedQuotes_df)


            ReturnedQuotes_df['date'] = pd.to_datetime(ReturnedQuotes_df['date'], format='%Y-%m-%d')


            # seting the date column to an index
            ReturnedQuotes_df.set_index('date', inplace=True)

            # Select only numeric columns for aggregation
            numeric_cols = ReturnedQuotes_df.select_dtypes(include=['number'])

            weekly_df = numeric_cols.resample('W').mean()
            # resetting the date column
            weekly_df.reset_index(inplace=True)

            weekly_df['symbol']=symbol
            # Print the resulting DataFrame
            print(weekly_df)
            print("weekly df")
            print(weekly_df)
            weekly_data = weekly_df.to_dict(orient="records")
            result=weekly_data




        if Frequency=="M":
            print("type of ReturnedQuotes ",type(ReturnedQuotes))
            ReturnedQuotes_df = pd.DataFrame(list(ReturnedQuotes))
            # print(">> ReturnedQuotes in a dataframe format ")
            # print(ReturnedQuotes_df)


            ReturnedQuotes_df['date'] = pd.to_datetime(ReturnedQuotes_df['date'], format='%Y-%m-%d') 

            # seting the date column to an index
            ReturnedQuotes_df.set_index('date', inplace=True)

            # Select only numeric columns for aggregation
            numeric_cols = ReturnedQuotes_df.select_dtypes(include=['number'])

            monthly_df = numeric_cols.resample('M').mean()

            # resetting the date column
            monthly_df.reset_index(inplace=True)

            monthly_df['symbol']=symbol


            # Print the resulting DataFrame
            print(monthly_df)
            print("monthly_df df")
            print(monthly_df)
            monthly_data = monthly_df.to_dict(orient="records")
            result=monthly_data



        if not ReturnedQuotes:
            return []

        start_time = time.time()
        # result = serializeList2(ReturnedQuotes)
        end_time = time.time()
        print(f"Elapsed Time: {end_time - start_time:.2f} seconds")

        reversed_data = result[::-1]
        result = serializeList2(reversed_data)

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail="Une erreur s'est produite lors de la récupération des données.")






#A curl example to this api 
#http://localhost:1001/quotes?symbol=LYFT&start_date=2018-01-05&end_date=2022-01-05&Frequency=W
@Get_Quotes.get('/v1/quotes')
def get_balance_sheet_annual(
    symbol: str = Query(None, title="symbol"),
    start_date: str = Query(None, title="start_date"),
    end_date: str = Query(None, title="end_date"),
    Frequency: str = Query(None, title="Frequency"),
):
    
    try:
        return get_Quotes_Data(symbol,start_date, end_date,Frequency,"QuotesCollection")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Une erreur s'est produite lors de la récupération des données.")
    


#http://localhost:1001/forex?symbol=LYFT&start_date=2018-01-05&end_date=2022-01-05&Frequency=W
@Get_Quotes.get('/v1/forex')
def get_balance_sheet_annual(
    symbol: str = Query(None, title="symbol"),
    start_date: str = Query(None, title="start_date"),
    end_date: str = Query(None, title="end_date"),
    Frequency: str = Query(None, title="Frequency"),
):
    
    try:
        return get_Quotes_Data(symbol,start_date, end_date,Frequency,"FOREXQuotesCollection")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Une erreur s'est produite lors de la récupération des données.")

#http://localhost:1001/stock?symbol=^OVX&start_date=2018-01-05&end_date=2022-01-05&Frequency=W
@Get_Quotes.get('/v1/stock')
def get_balance_sheet_annual(
    symbol: str = Query(None, title="symbol"),
    start_date: str = Query(None, title="start_date"),
    end_date: str = Query(None, title="end_date"),
    Frequency: str = Query(None, title="Frequency"),
):
    
    try:
        return get_Quotes_Data(symbol,start_date, end_date,Frequency,"STOCKIndexesQuotesCollection")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Une erreur s'est produite lors de la récupération des données.")
