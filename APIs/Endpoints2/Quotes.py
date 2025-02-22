
from fastapi import HTTPException, FastAPI, Response, status, APIRouter
from fastapi.responses import JSONResponse

import pandas as pd

from config.db import get_database 
from APIs.Endpoints1.companies_APIs import get_company_symbols 


from APIs.Endpoints5.googleSheetAPI import read_data_from_sheets
from APIs.Endpoints5.googleSheetAPI import update_googleSheet_data_in


import os
import asyncio
import aiohttp  
import time
import datetime

Quotes = APIRouter()
api_key = os.getenv("API_KEY")




def get_Quotes_collection():
    db = get_database()
    Quotes=db["Quotes"]
    Quotes.create_index([("_id", 1)])
    return Quotes

QuotesCollection=get_Quotes_collection()





def get_date_for_symbol(dataframe, symbol):
    # print("working with this dataframe")
    # print(dataframe)
    print("Treating the symbol  ", symbol)
    filtered_df = dataframe[dataframe['symbol'] == symbol]

    if not filtered_df.empty:
        return filtered_df['date'].iloc[0]
    else:
        return None




def update_csv_with_symbol_and_date(csv_url, symbol, date):
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        print(f"Error loading the .csv file: {e}")
        return

    if symbol in df['symbol'].values:
        df.loc[df['symbol'] == symbol, 'date'] = date
    else:
        new_entry = {'symbol': symbol, 'date': date}
        new_df = pd.DataFrame([new_entry]) 
        df = pd.concat([df, new_df], ignore_index=True)  

    try:
        df.to_csv(csv_url, index=False)
        print("CSV file updated successfully.")
    except Exception as e:
        print(f"Error saving the .csv file: {e}")



async def Quotes_Creation(symbol, dataframe):
    print("Company with symbol '", symbol, "' made Quotes API call ")
    creation_Order=False
    start_date = "1950-01-01"


    # Getting today's date
    current_date = datetime.datetime.now()
    formatted_todayDate = current_date.strftime("%Y-%m-%d")

    symbol_to_check = symbol

    # Check if we have already treated the company before in the quotes or not
    symbolDate_if_Exists_in_the_DataFrame = get_date_for_symbol(dataframe, symbol_to_check)
    print("The extracted date with the symbol ", symbolDate_if_Exists_in_the_DataFrame)

    if symbolDate_if_Exists_in_the_DataFrame != formatted_todayDate:
        if(symbolDate_if_Exists_in_the_DataFrame==None):
            print(f"-->>{symbol_to_check} does not exist in the csv and we are going to add quotes for the first time  ")
            creation_Order=True

        else:
            print(f"-->>{symbol_to_check} exists in the csv and we are going to add new quotes and update the last date in the csv ")
            start_date = symbolDate_if_Exists_in_the_DataFrame
            creation_Order=True
    else:
        print(f"-->>{symbol_to_check}  exist in the csv and it's up to date ")

    # The end_date is always today's date
    end_date = formatted_todayDate

    # print("start_date ", start_date)
    # print("end_date ", end_date)

    api_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={api_key}"
    #print("The api url ", api_url)
    
    if creation_Order==True:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                # Check if data is not empty before accessing its elements
                if data and len(data.get("historical", [])) > 0:
                    for obj in data.get("historical", []):
                        obj["symbol"] = symbol
                        
                    QuotesCollection.insert_many(data["historical"])
                    # ## when working locally 
                    # Symbol_Date_Quotes_CSV_FileName = "HistoriqueCSV/Quotes_CSV_file/Quotes_CSV_file.csv"
                    # update_csv_with_symbol_and_date(Symbol_Date_Quotes_CSV_FileName, symbol, formatted_todayDate)



                    ### When working with csv online google sheet
                    Quotes_CSV_file_googleSheetID = "18fv1_nvo2WW9jgC5hzjrZpgqIf4PZbgPX2Sxc1_nt5c"
                    update_googleSheet_data_in(Quotes_CSV_file_googleSheetID, symbol, formatted_todayDate)


                    print(f"The compnay ' {symbol}' has Quotes data inserted into the database and updating the CSV quotes file ")
                else:
                    print(f"No data returned for symbol {symbol}")






@Quotes.get('/v1/Quotes_Creation_API')
async def Insert_Quotes_Creation_API():

    allCompaniesSymobls = get_company_symbols()
    allCompaniesSymbolsList = list(allCompaniesSymobls)
    print("-- All the companies symbols list ")
    print(allCompaniesSymobls)



    #To work with only two symbols for testing purposes
    allCompaniesSymbolsList = allCompaniesSymbolsList[:1000]

    print("Number of all the symbols ")
    print(len(allCompaniesSymbolsList))

    # allCompaniesSymbolsList=["MLIFC.PA", "AJINF", "AGGRU", "MTGRF", "RGBD", "TVTY", "RAC.AX", "4248.T", "REXR", "600936.SS", "CAMLINFINE.NS", "FINGF", "CPFXF", "AGTT", "CNNA", "LMNR", "JPFA.JK", "300368.SZ", "CPD.WA", "090350.KS", "002223.SZ", "ARYN.SW", "FROTO.IS", "GPIL.NS", "SOFT", "LSTR", "MTX", "FBVA", "TVPC", "USCTU", "LIVK", "GQMLF", "QELL", "AMIN.JK", "BRAC", "GBGPF", "ICGUF", "GRVI", "OTLKW", "PIPP", "EXRO.TO", "UMGNF", "PRU.DE", "FDUSZ", "CNBN", "STEELCAS.NS", "ICDSLTD.NS", "RATCH-R.BK", "SHMAY", "BRLIU", "CAMS.NS", "MNGG", "RFLFF", "RVVTF", "EXPI", "CKISF", "WRTBF", "1370.HK", "PHN.MI", "300546.SZ", "PGPEF", "LOV.AX", "STBI", "NTST", "LLKKF", "DMPZF", "605296.SS", "0HDK.L", "FDY.TO", "OBSN.SW", "ELK.OL", "MLLOI.PA", "MGYOY", "BNP.WA", "GZPHF", "300252.SZ", "SWTF.F", "ALSO3.SA", "2764.T", "TAINWALCHM.NS", "JSDA", "MUNJALSHOW.NS", "000856.SZ", "ASHTF", "MSON-A.ST", "WIB.CN", "9428.T", "0856.HK", "BBB.L", "601865.SS", "TSPG", "5658.T", "1982.T", "600748.SS", "IMPAL.NS", "4044.T", "GMAB.CO", "2379.TW", "TTE.PA", "6901.T", "WINE.L", "BXMT", "KARE.AT", "RGEN", "CAKE", "600612.SS", "6748.T", "MGA", "WFC", "0IV3.L", "DND.TO", "CIBUS.ST", "CYBERMEDIA.NS", "002273.SZ", "LEN-B", "DEC.PA", "NAVNETEDUL.NS", "4118.T", "EXC", "ELLKF", "3699.HK", "CTPTY", "LEVL", "LMN.SW", "THYROCARE.NS", "3056.TW", "ALQ.AX", "ELUXY", "301007.SZ", "MCPH", "REPH", "603918.SS", "002901.SZ", "ELMN.SW", "GWRE", "1447.TW", "023530.KS", "NSTS", "VSYD.ME", "603085.SS", "LAC", "GCEI", "F3C.DE", "002341.SZ", "FBTT", "IVAC", "HELN.SW", "STRNW", "SQSP", "CI.BK", "603212.SS", "0HFB.L", "601928.SS", "APO", "8289.T", "8096.T", "FLWS", "MXC.L", "PGOL.CN", "SKKRF", "PORBF", "SEMR", "603027.SS", "YPB.AX", "SREV", "PNV.AX", "CHWAW", "MBHCF", "GL.CN", "0QZ4.L", "0KYZ.L", "HO7.DE", "PREM.L", "MNIN.TA", "JIM.L", "SBGSF", "WNNR-UN", "CBY.AX", "BRSYF", "ASB-PE", "KIDS", "NCPL", "AKO-B", "3101.T", "9932.T", "1515.T", "FME.L", "GPOR", "KROS", "SCHAND.NS", "603703.SS", "03473K.KS", "MMTS", "0992.HK", "000021.SZ", "MFT.MI", "AKSHAR.NS", "ISOLF", "300689.SZ", "SKUE.OL", "SFT.F", "EMA.TO", "000413.SZ", "8387.T", "600099.SS", "TOOL","OG.V", "300790.SZ", "SHMUF", "AXE.V", "BUD.V", "ECPN", "TELIA1.HE", "PIER.L", "MSLH.L", "6032.T", "FKWL", "HAR.DE", "HITECHCORP.NS", "2590.T", "9322.T", "ONEXF", "0688.HK", "KBH", "CRWD", "FTOCU", "BYRG", "BRGE12.SA", "0631.HK", "1813.HK", "APS.TO", "5406.T", "000903.SZ", "ZIN.L", "ENBI.CN", "CRSQ", "300261.SZ", "MGG.V", "002928.SZ", "HUM.AX", "FPIP.ST", "UNIP3.SA", "000048.SZ", "2376.HK", "AMAOU", "5GG.AX", "WEGOF", "AWTRF", "ROSE.SW", "CDSG", "TRII", "002555.SZ", "000055.SZ", "SASQ.CN", "NICU.V", "NZS.AX", "BCOMF", "000953.SZ", "AYAL.TA", "002692.SZ", "CLH.JO", "THEP.PA", "TPC", "LTMAQ", "ENUA.F", "0R2Y.L", "BGOPF", "KEN.TA", "TANGI.ST", "TEAM.CN", "0118.HK", "EDHN.SW", "RAUTE.HE", "GAPAW", "CBLNF", "PCOR", "49GP.L", "IVC.AX", "JMFINANCIL.NS", "ICLD", "SKA.WA", "7762.T", "GIL.TO", "SKHSF", "SRI.V", "ALWEC.PA", "BFINVEST.NS", "GZF.DE", "ECHO", "600271.SS", "ETG.TO", "IOSP", "CDXFF", "ABSOF", "SYHLF"]
    # allCompaniesSymbolsList=["AAPL"]

    allCompaniesSymbolsList=["MLIFC.PA", "AJINF","MTGRF"]


##working with local csv
    #Reading the quotes csv file that contains the symbol and the date information of the companies 
    # csv_file_path = 'HistoriqueCSV/Quotes_CSV_file/Quotes_CSV_file.csv'
    # SymbolDateQuotesDF = pd.read_csv(csv_file_path)

###working with google sheet
    quotesCSV_ID="18fv1_nvo2WW9jgC5hzjrZpgqIf4PZbgPX2Sxc1_nt5c"
    SymbolDateQuotesDF = read_data_from_sheets(quotesCSV_ID,"sheet1")


    batch_size = 10
    
    results = []
    
    ##To work with all the symbols for production purposes
    for i in range(0, len(allCompaniesSymbolsList), batch_size):


    # # To work with only few symbols for testing purposes we use only 30 symbol
    # for i in range(0, 30, batch_size):


        symbols_batch = allCompaniesSymbolsList[i:i + batch_size]
        awaitable_tasks = [Quotes_Creation(symbol, SymbolDateQuotesDF) for symbol in symbols_batch]
        batch_results = await asyncio.gather(*awaitable_tasks)
        results.extend(batch_results)
    
    return {"message": "Quotes creation process is complete"}






