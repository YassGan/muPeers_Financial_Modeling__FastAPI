from fastapi import HTTPException, FastAPI, Response, status, APIRouter
from fastapi.responses import JSONResponse

import pandas as pd


import os
import asyncio
import aiohttp  
import time
import datetime


from APIs.Endpoints5.googleSheetAPI import read_data_from_sheets

from APIs.Endpoints5.googleSheetAPI import update_googleSheet_data_in



from APIs.Endpoints1.companiesFiltering import CompaniesCollection 
from config.db import get_database 

from APIs.Endpoints1.companies_APIs import get_company_symbols 



Financial_Info = APIRouter()
api_key = os.getenv("API_KEY")









#Function that gets the csv path of the file that contains companies symbols and the latest data of its balancesheet
def return_CompanyLatestBalanceSheet_Date_Symbol_Set(csv_file_path):
    try:
        ##working with local csv
        # df = pd.read_csv(csv_file_path)

        df = read_data_from_sheets(csv_file_path)
        symbol_date_set = set()  
        for index, row in df.iterrows():
            symbol_date_set.add((row['symbol'], row['date']))
        return symbol_date_set
    except Exception as e:
        print(f"An error occurred when  return_CompanyLatestBalanceSheet_Date_Symbol_Set: {str(e)}")
        return set()



def find_date_by_symbol(symbol, symbol_date_set):


    # how the function was before changing the logic to work with the dataframe
    # match_found = False
    
    # for s, date in symbol_date_set:
    #     if s == symbol:
    #         match_found = True
    #         return date
    
    # if not match_found:
    #     print(f">> Pas de date existante dans le csv pour le symbol '{symbol}'")
    #     return None




    set_to_list = list(symbol_date_set)
    df = pd.DataFrame(set_to_list, columns=["symbol","date"])


    # print(">> The symbol_date_set ")
    # print(symbol_date_set)
    # print(">> the symbol " + symbol)
    
    symbol_to_find = symbol

    # Check if the symbol exists in the DataFrame
    if symbol_to_find in df['symbol'].values:
        date = df[df['symbol'] == symbol_to_find]['date'].values[0]
        print(f"Date for symbol '{symbol_to_find}': {date}")
        return date
    else:
        print(f">> Pas de date existante dans le DataFrame pour le symbol '{symbol_to_find}'")
        return None


def update_csv_file(csv_file_path, symbol_to_update, newDate):
    try:
        df = pd.read_csv(csv_file_path)
        symbolDate_toChange = df['symbol'] == symbol_to_update

        if symbolDate_toChange.any():
            df.loc[symbolDate_toChange, 'date'] = newDate
            print(f"Updated date for symbol {symbol_to_update}")
        else:
            print(f"Symbol {symbol_to_update} not found in the DataFrame. Inserting a new row.")
            new_row = pd.DataFrame({'symbol': [symbol_to_update], 'date': [newDate]})
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(csv_file_path, index=False)

    except Exception as e:
        print(f"An error occurred when update_csv_file: {str(e)}")





# the second approach for creating balance sheet 
async def FinancialInformation_Creation(symbol,balanceSheet_URL,Symbol_Date_BalanceSheetDF_Set,DataBaseName,Symbol_Date_BalanceSheetDF_FileName,Period):
    
    print("Company with symbol '", symbol, "'made balance sheet API call ")
    CompanyBalanceSheet_UpdatingTreatement=False
    CompanyBalanceSheet_FirstTimeTreatement=False
    # api_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={api_key}"
    # https://financialmodelingprep.com/api/v3/balance-sheet-statement

    if Period=="annual":
        api_url = f"{balanceSheet_URL}/{symbol}?apikey={api_key}"
    if Period=="quarter":
        api_url = f"{balanceSheet_URL}/{symbol}?period=quarter&apikey={api_key}"
    # Tous_les_Symbols_list=get_company_symbols()
    # Tous_les_Symbols_list_set = set(Tous_les_Symbols_list)
    # travailler avec le set car c'est beaucoup plus pratique et rapide dans les tests de check d'existence d'un élément dans un set
    
    symbol_to_check = symbol

    #symbolExistence_in_the_csv is with type date
    symbolDate_if_Exists_in_the_csv= find_date_by_symbol(symbol,Symbol_Date_BalanceSheetDF_Set)

    if symbolDate_if_Exists_in_the_csv!=None:
       CompanyBalanceSheet_UpdatingTreatement =True
       CompanyBalanceSheet_FirstTimeTreatement=False
       print(f">>{symbol_to_check} exists in the set of csv and we are going to check if the data is up to date or not .")
    else:
        print(f">>{symbol_to_check} does not exist in the set of csv and we are going to create it for the first time .")
        CompanyBalanceSheet_UpdatingTreatement=False
        CompanyBalanceSheet_FirstTimeTreatement=True



    if CompanyBalanceSheet_FirstTimeTreatement:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                if data and isinstance(data, list) and len(data) > 0:

                    #data[0]['symbol'] = data[0]['symbol']
                    # print("Data globale response ")
                    # print(data)
                    DataBaseName.insert_many(data)
                    # DataBaseName.insert_one(data[0])
                    # DataBaseName.insert_one(data[0])

                    print(f"Inserted {symbol} balance sheet data into the database.")
                    update_googleSheet_data_in(Symbol_Date_BalanceSheetDF_FileName, symbol, data[0]['date'])

                    if '_id' in data[0]:
                        data[0]['_id'] = str(data[0]['_id'])




    if CompanyBalanceSheet_UpdatingTreatement:
        api_url = f"{balanceSheet_URL}/{symbol}?limit=1&apikey={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                    data = await response.json()
                    if data and isinstance(data, list) and len(data) > 0:

                        #print(data[0]['symbol'])
                        api_date = datetime.datetime.strptime(data[0]['date'], '%Y-%m-%d')
                        
                        company_csv_date = datetime.datetime.strptime(symbolDate_if_Exists_in_the_csv, '%Y-%m-%d')


                        if api_date > company_csv_date:
                            #DataBaseName.replace_one({"symbol": data[0]['symbol']}, data[0])
                            
                            # data[0]['symbol'] = data[0]['symbol']+"_"+company_csv_date.strftime("%Y-%m-%d")

                            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>")
                            print("")
                            print("Updating the symobol ,"+symbol+" ")
                            print("The new api date "+api_date.strftime("%Y-%m-%d"))
                            print("The csv date "+company_csv_date.strftime("%Y-%m-%d"))


                            DataBaseName.insert_one(data[0])
                            update_googleSheet_data_in(Symbol_Date_BalanceSheetDF_FileName, symbol, api_date.strftime("%Y-%m-%d"))

                            print(f">>Updated {symbol} balance sheet data in the database.")
                        else:
                            print(f"{symbol} balance sheet data in the database is up to date.")

                
                        if '_id' in data[0]:
                            data[0]['_id'] = str(data[0]['_id'])
    if data:
        return "good"
    else:
        return "error"








# Annual Balance Sheet
def get_companies_Annual_BalanceSheet():
    db = get_database()
    AnnualBalanceSheet=db["Annual_Balance_Sheet"]

    return AnnualBalanceSheet


companies_Annual_BalanceSheetCollection=get_companies_Annual_BalanceSheet()



@Financial_Info.get('/v1/Annual_BalanceSheetCreationAPI')
async def Insert_BS_Annual_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))
    


    #### Working with local csv
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/AnnualBalanceSheet_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/AnnualBalanceSheet_company_symbol_date.csv")
    

    ### Working with google
    Symbol_Date_BalanceSheetDF_IdSheet = "1OiODwDr9A9BhBhv_1lZdjeUZO8O2NzDOggx8YbMvEnQ"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_BalanceSheetDF_IdSheet)
    



    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 90  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/balance-sheet-statement', Symbol_Date_BalanceSheetDF_Set, companies_Annual_BalanceSheetCollection, Symbol_Date_BalanceSheetDF_IdSheet,"annual") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}





#Quarter Balance Sheet
def get_companies_Quarter_BalanceSheet():
    db = get_database()
    QuarterBalanceSheet=db["Quarter_Balance_Sheet"]

    return QuarterBalanceSheet

companies_Quarter_BalanceSheetCollection=get_companies_Quarter_BalanceSheet()


@Financial_Info.get('/v1/Quarter_BalanceSheetCreationAPI')
async def Insert_BS_Quarter_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))
    

    # ## Working with local csvs
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/QuarterBalanceSheet_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/QuarterBalanceSheet_company_symbol_date.csv")
    

        ### Working with google
    Symbol_Date_QuarterBalanceSheetDF_IdSheet = "12e1sE25Q9G6rBHbP6rKCzMudDRh_p43SqRUmER-Ea-E"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_QuarterBalanceSheetDF_IdSheet)
    





    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 90  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/balance-sheet-statement', Symbol_Date_BalanceSheetDF_Set, companies_Quarter_BalanceSheetCollection, Symbol_Date_QuarterBalanceSheetDF_IdSheet,"quarter") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}





#Annual Income Statement
def get_companies_Annual_IncomeStatement():
    db = get_database()
    AnnualIncomeStatement=db["Annual_Income_Statement"]

    return AnnualIncomeStatement

companies_Annual_IncomeStatementCollection=get_companies_Annual_IncomeStatement()


@Financial_Info.get('/v1/Annual_IncomeStatementCreationAPI')
async def Insert_IS_Annual_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))
    

    ## Working with local csv
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/AnnualIncomeStatement_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/AnnualIncomeStatement_company_symbol_date.csv")
    

    ## Working with google sheets
    Symbol_Date_Annual_IncomeStatementDF_id = "17EoOzl--dKJVwAbLD-VOCj0FR7JgPRbR3rR32--0YJg"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_Annual_IncomeStatementDF_id)
    


    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 90  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/income-statement', Symbol_Date_BalanceSheetDF_Set, companies_Annual_IncomeStatementCollection, Symbol_Date_Annual_IncomeStatementDF_id,"annual") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}





#Quarter Income Statement
def get_companies_Quarter_IncomeStatement():
    db = get_database()
    QuarterIncomeStatement=db["Quarter_Income_Statement"]

    return QuarterIncomeStatement

companies_Quarter_IncomeStatementCollection=get_companies_Quarter_IncomeStatement()


@Financial_Info.get('/v1/Quarter_IncomeStatementCreationAPI')
async def Insert_IS_Quarter_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))


   ### working with local csvs 
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/QuarterIncomeStatement_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/QuarterIncomeStatement_company_symbol_date.csv")
    

        ## Working with google sheets
    
    Symbol_Date_Quoter_IncomeStatementDF_id = "1bpKrlEaXaFgEPjr3lc3Hq9RyGQJ-Nt8q4ryecaidefU"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_Quoter_IncomeStatementDF_id)
    

    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 90  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/income-statement', Symbol_Date_BalanceSheetDF_Set, companies_Quarter_IncomeStatementCollection, Symbol_Date_Quoter_IncomeStatementDF_id,"quarter") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}




#Annual Cash Flow
def get_companies_Annual_CashFlow():
    db = get_database()
    AnnualCashFlow=db["Annual_Cash_Flow"]

    return AnnualCashFlow

companies_Annual_CashFlowCollection=get_companies_Annual_CashFlow()


@Financial_Info.get('/v1/Annual_CashFlowCreationAPI')
async def Insert_CF_Annual_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))
    

    ### working with local csv 
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/AnnualCashFlow_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/AnnualCashFlow_company_symbol_date.csv")
    

    Symbol_Date_BalanceSheetDF_FileName_id = "1PsCEtOqLffwdHDuWfACctDdmGs3GfqC5UkZy0VB4DWQ"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_BalanceSheetDF_FileName_id)
    


    

    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 90  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/cash-flow-statement', Symbol_Date_BalanceSheetDF_Set, companies_Annual_CashFlowCollection, Symbol_Date_BalanceSheetDF_FileName_id,"annual") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}










#Quarter Cash Flow
def get_companies_Quarter_CashFlow():
    db = get_database()
    QuarterCashFlow=db["Quarter_Cash_Flow"]

    return QuarterCashFlow

companies_Quarter_CashFlowCollection=get_companies_Quarter_CashFlow()


@Financial_Info.get('/v1/Quarter_CashFlowCreationAPI')
async def Insert_CF_Quarter_information():

    allCompaniesSymobls = get_company_symbols()
    print("Number of all the symbols ")
    print(len(allCompaniesSymobls))
    

    #### working with local csvs
    # Symbol_Date_BalanceSheetDF_FileName = "HistoriqueCSV/Financial_Information_CSV_files/QuarterCashFlow_company_symbol_date.csv"
    # Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set("HistoriqueCSV/Financial_Information_CSV_files/QuarterCashFlow_company_symbol_date.csv")
    

    Symbol_Date_BalanceSheetDF_FileName_id = "1p-6VQnyFMi1DQfz_nk_iwD3znbQuceGgh0aCID6MgdM"
    Symbol_Date_BalanceSheetDF_Set = return_CompanyLatestBalanceSheet_Date_Symbol_Set(Symbol_Date_BalanceSheetDF_FileName_id)
    


    Symbol_Date_BalanceSheetDF_Set = list(Symbol_Date_BalanceSheetDF_Set)    
    allCompaniesSymobls=list(allCompaniesSymobls)


    batch_size = 110  
    
    results = []
    
    for i in range(0, len(allCompaniesSymobls), batch_size):
        symbols_batch = allCompaniesSymobls[i:i + batch_size]
        awaitable_tasks = [FinancialInformation_Creation(symbol, 'https://financialmodelingprep.com/api/v3/cash-flow-statement', Symbol_Date_BalanceSheetDF_Set, companies_Quarter_CashFlowCollection, Symbol_Date_BalanceSheetDF_FileName_id,"quarter") for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Processing complete"}






























# Function that runs the online api that returns the balance sheet information
async def CompanyBalanceSheetInfo(symbol):
    print("Company with symbol", symbol, "made balance sheet API call")
    api_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            data = await response.json()
    return data




#API that launches the function CompanyBalanceSheetInfo
@Financial_Info.get('/v1/getBalanceSheet_company/{Symbol}')
async def create_BS_Annual_api(Symbol: str):
    result = await CompanyBalanceSheetInfo(Symbol)
    return result
























# The first approch  of creating balancesheet
# Function that gets the information of the balance sheet of the company and it compares the data with 
# the data in the database and the date data also if it exists and the date is older that the new one
# it adds the new information in the database otherwise it does nothing, if there is no data it creates a new
# element
async def CompanyAnnualBalanceSheetInfoComparisonInsertion(symbol):
    print("Company with symbol", symbol, "made balance sheet API call and is comparing the API data with the data in the database")
    
    api_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            data = await response.json()
            
            if not data:
                print("Data is empty")
                return JSONResponse(content={"message": "Data is empty"})

            if data and data[0].get('_id'):
                data[0]['_id'] = str(data[0]['_id'])

            # Check if data list is not empty before accessing its elements
            if data:
                existing_data = companies_Annual_BalanceSheetCollection.find_one({"symbol": data[0]['symbol']})
                
                if existing_data:
                    api_date = datetime.datetime.strptime(data[0]['date'], '%Y-%m-%d')
                    db_date = datetime.datetime.strptime(existing_data['date'], '%Y-%m-%d')
                    
                    if api_date > db_date:
                        data[0]['symbol'] = data[0]['symbol']
                        companies_Annual_BalanceSheetCollection.replace_one({"symbol": data[0]['symbol']}, data[0])
                        
                        data[0]['symbol'] = data[0]['symbol']+"_"+db_date.strftime("%Y-%m-%d")
                        data[0]['date'] = db_date.strftime("%Y-%m-%d")

                        companies_Annual_BalanceSheetCollection.insert_one(data[0])

                        print(f"Updated {symbol} balance sheet data in the database.")
                    else:
                        print(f"{symbol} balance sheet data in the database is up to date.")
                else:
                    data[0]['symbol'] = data[0]['symbol']
                    companies_Annual_BalanceSheetCollection.insert_one(data[0])
                    print(f"Inserted {symbol} balance sheet data into the database.")
            else:
                print("Data is empty")  # Handle the case where data is empty

    return "process completed "















# API that launches the function CompanyBalanceSheetInfoComparisonInsertion
@Financial_Info.get('/v1/getBalanceSheet_company_comparison_insertion/{Symbol}')
async def create_BS_Annual_api(Symbol: str):
    result = await CompanyAnnualBalanceSheetInfoComparisonInsertion(Symbol)
    return result









# API that launches the function CompanyBalanceSheetInfoComparisonInsertion and use it with many symbols
@Financial_Info.get('/v1/Insert_Annual_BalanceSheet_information_Comparison')
async def Insert_BS_Annual_information():

    allSymbols = get_company_symbols()
    allCompaniesSymbolsList = list(allSymbols)
    
    # For testing purposes
    # allCompaniesSymbolsList = ['AAPL', 'LMNR', 'GO']

    batch_size = 10  
    results = []

    for i in range(0, len(allCompaniesSymbolsList), batch_size):
        symbols_batch = allCompaniesSymbolsList[i:i + batch_size]
        awaitable_tasks = [CompanyAnnualBalanceSheetInfoComparisonInsertion(symbol) for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)

    return {"message": "Insertion process is complete", "results": results}




###Another logic to insert the balance sheet annual data
# async def fetch_balance_sheet_data(symbol):
#     api_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={api_key}"

#     async with aiohttp.ClientSession() as session:
#         async with session.get(api_url) as response:
#             if response.status != 200:
#                 raise HTTPException(status_code=response.status, detail="Failed to fetch data from API")

#             data = await response.json()
#             return data[0]

# async def update_or_insert_balance_sheet_data(data):
#     existing_data = companies_Annual_BalanceSheetCollection.find_one({"symbol": data['symbol']})

#     if existing_data:
#         api_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d')
#         db_date = datetime.datetime.strptime(existing_data['date'], '%Y-%m-%d')

#         if api_date > db_date:
#             data['symbol'] = data['symbol']
#             companies_Annual_BalanceSheetCollection.replace_one({"symbol": data['symbol']}, data)
#             return f"Updated {data['symbol']} balance sheet data in the database."
#         else:
#             return f"{data['symbol']} balance sheet data in the database is up to date."
#     else:
#         data['symbol'] = data['symbol']
#         companies_Annual_BalanceSheetCollection.insert_one(data)
#         return f"Inserted {data['symbol']} balance sheet data into the database."

# @BS_Annual.get('/getBalanceSheet_company_comparison_insertion/{Symbol}')
# async def create_BS_Annual_api(Symbol: str):
#     try:
#         data = await fetch_balance_sheet_data(Symbol)
#         result = await update_or_insert_balance_sheet_data(data)
#         return JSONResponse(content=data)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @BS_Annual.get('/Insertion_BalanceSheet_information_Comparison')
# async def Insert_BS_Annual_information():
#     dataframe = ['AAPL', 'LMNR', 'SU', 'LRCX', 'PBTS', 'AMAT', 'PLUG', 'AX', 'MET', 'HIBB', 'BLCO', 'F', 'BUSE']

#     try:
#         awaitable_tasks = [fetch_balance_sheet_data(symbol) for symbol in dataframe]
#         results = await asyncio.gather(*awaitable_tasks)
#         response_messages = [await update_or_insert_balance_sheet_data(data) for data in results]
#         return JSONResponse(content={"results": response_messages})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))