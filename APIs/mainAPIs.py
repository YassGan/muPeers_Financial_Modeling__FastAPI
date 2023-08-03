
from fastapi import APIRouter,Response
from models.Industry import Industry 
from models.Sector import Sector 

from config.db import get_database 
from schemas.Industry import serializeDict, serializeList
from schemas.Sector import serializeDict2, serializeList2


import pandas as pd
import requests

import numpy as np



Main=APIRouter()


DataFrame=pd.DataFrame()


def get_industry_collection():
    db = get_database()
    return db["industries"]


def get_sector_collection():
    db = get_database()
    return db["sectors"]



def get_exchange_collection():
    db = get_database()
    return db["exchange"]


def get_countries_collection():
    db = get_database()
    return db["countries"]






@Main.get('/Hello_MainAPIs')
async def Hello_MainPage():
    return 'Hello Main Page'


@Main.get('/Read_CSV')
async def Read_CSV():
    #Reading the csv file 
    global DataFrame
    DataFrame = pd.read_csv("output_csv_file.csv", encoding='utf-8')
    print('Printing Data Frame ------------')
    print(DataFrame)
    print('Printing Data Frame ------------')



#function that downloads the csv file from an api 
def download_csv_from_url(url, file_path):
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()  

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) * 100
                    print(f"Download progress: {progress:.2f}%")

        print("File downloaded successfully.")
        return True
    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
        return False
    except IOError as e:
        print("File Error:", e)
        return False
    


#API that once is launched it downloads the csv file from the online api of the modeling website    
@Main.get('/download_csv')
async def download_csv():
    url = "https://financialmodelingprep.com/api/v4/profile/all?apikey=96051dba5181978c2f0ce23c1ef4014b"
    file_path = "data.csv"  

    success = download_csv_from_url(url, file_path)
    if success:
        return Response(content="File downloaded successfully.", media_type="text/plain")
    else:
        return Response(content="Failed to download the file.", media_type="text/plain")



# Function to fetch comany's data from the API by its symbol
def fetch_data_from_api_bySymbol(Symbol):
    api_url = f"https://financialmodelingprep.com/api/v3/profile/{Symbol}?apikey=96051dba5181978c2f0ce23c1ef4014b"
    response = requests.get(api_url)
    return response.json()


# Define the API route to fetch data from the API
@Main.get("/getCompanyBySymbol/{Symbol}")
def getCompanyBySymbol(Symbol: str):
    data = fetch_data_from_api_bySymbol(Symbol)
    return data








# Function to create new industries from the DataFrame 
def create_industries_from_dataframe(DataF):
    Industries_variables = DataF[['Symbol','sector', 'companyName']]  

    if not DataF.empty:
        new_industries = Industries_variables.to_dict(orient='records')
        
        existing_symbols = set(get_industry_collection().distinct("Symbol"))
        new_industries_to_create = [industry for industry in new_industries if industry["Symbol"] not in existing_symbols]

        if new_industries_to_create:
            get_industry_collection().insert_many(new_industries_to_create)
            return f"- {len(new_industries_to_create)} new industries created successfully."
        else:
            return "- No new industries to create."
    else:
        return "- No new industries to create."


# API to create new industries from the DataFrame 
@Main.post('/CreateIndustriesFromDataFrame')
async def create_industries_api():
    DataF = pd.read_csv("data_with_17.csv", encoding='utf-8')
    result = create_industries_from_dataframe(DataF)
    if "new industries created successfully" in result:
        return Response(status_code=201, content=result)
    else:
        return Response(status_code=200, content=result)



# API to create a new .csv file that has the first elements of the big dataframe file 
def create_csv_with_first_elements(Number,input_file_path, output_file_path):
    try:
        df = pd.read_csv(input_file_path)

        first_5_elements = df.head(Number)

        first_5_elements.to_csv(output_file_path, index=False)

        print("- File with new elements created successfully.")
        return True
    except pd.errors.EmptyDataError:
        print("Error: Input CSV file is empty.")
        return False
    except FileNotFoundError:
        print("Error: Input CSV file not found.")
        return False
    except Exception as e:
        print("Error:", e)
        return False

# create_csv_with_first_elements(15,'data.csv','data_with_17.csv')





# API that launches the create_csv_with_first_elements function
@Main.post('/create_csv_with_first_elements/{Number}')
async def create_csv_endpoint(Number: int):
    input_file_path = "data.csv"
    output_file_path = "data_with_17.csv"

    result = create_csv_with_first_elements(Number, input_file_path, output_file_path)

    if result:
        return Response(status_code=200, content="File with new elements created successfully.")
    else:
        return Response(status_code=400, content="Failed to create the file.")



# API that creates a json file from a dataframe, but the csv file should be read first
@Main.get('/DownloadFirstElemAsJson/{Number}')
async def download_first_10_as_json(Number: int):
    DataFrame = pd.read_csv("data.csv", encoding='utf-8')

    first_10_df = DataFrame.head(Number)  
    json_data = first_10_df.to_json(orient='records', lines=True) 

   
    filename = "firstlements.json"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(json_data)

    response = Response(content=json_data, media_type='application/json')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response





























import time



# Function that creates new sectors in the database from a dataFrame
def create_sectors_from_dataframe(DataF):
    start_time = time.time()
    DataF.dropna(subset=['sector'], inplace=True)

    # Get the unique values of the "Sector" column
    Sector_variables = DataF["sector"].unique()
    print("Time taken for creating DataFrame:", time.time() - start_time, "seconds")

    # Convert the NumPy array to a DataFrame
    sector_df = pd.DataFrame(Sector_variables, columns=["name"])
    print('The type of the sector_df variable is', type(sector_df))
    print(sector_df)

    if not DataF.empty:
        # Convert the DataFrame to a dictionary with "records" orientation
        sectors_to_dict = sector_df.to_dict(orient='records')

        existing_sectors = set(get_sector_collection().distinct("name"))
        new_sectors_to_create = [sector for sector in sectors_to_dict if sector["name"] not in existing_sectors]

        if new_sectors_to_create:
            get_sector_collection().insert_many(new_sectors_to_create)
            return f"- {len(new_sectors_to_create)} new sectors created successfully."
        else:
            return "- No new sectors to create."
    else:
        return "- No new sectors to create."


# API that creates new sectors from the DataFrame 
@Main.get('/CreateSectorsFromDataFrame')
async def create_sectors_api():
    DataF = pd.read_csv("data.csv", encoding='utf-8')
    result = create_sectors_from_dataframe(DataF)
    if "new sectors created successfully" in result:
        return Response(status_code=201, content=result)
    else:
        return Response(status_code=200, content=result)



#API to get all the sectors from the database
@Main.get('/AllSectors')
async def find_all_sectors():
    return serializeList(get_sector_collection().find())



# API that creates a sector manually in the database
@Main.post('/AddSector')
async def create_sector(sector: Sector):
    
    sector_dict = dict(sector)
    
    get_sector_collection().insert_one(sector_dict)
    return 'New Sector added successfully'












# Function that creates new industries from the dataframe that matches the sectors elements from the databse 
def create_new_dataframe_with_sector_industry_info(dataframe, sectors):
    sector_industry_data = []
    print('the data frame ')
    print(dataframe)
    print('the sectors from the database  ')
    print(sectors)
    # print('Type of the data from the database ')
    # print(type(sectors))
    # print('Type of the data of the datafram ')
    # print(type(dataframe))

    for index, row in dataframe.iterrows():
        sector_name = row['sector']
        for sector_obj in sectors:
            if sector_obj['name'] == sector_name:
                sector_industry_data.append({
                    "Industry": row['industry'],
                    "sector": sector_obj['name'],
                    "sectorId": sector_obj['_id']
                })
    # print('the match between the two sets of data is ')            
    # print(sector_industry_data)
    # print('The type of the set that contains the match between the two elements of data is ')
    # print(type(sector_industry_data))
    #converting from a list to a panda dataframe 
    df_sector_industry_data = pd.DataFrame(sector_industry_data)
    return(df_sector_industry_data)

 
#API that calls the function that creates the new elements industry in the database
@Main.get('/CreateDataFrameWithSectorInfo')
async def create_dataframe_with_sector_info():
    # Fetch all sectors from the database
    sectors = serializeList(get_sector_collection().find())
    # # Read the DataFrame from your data
    DataFrame = pd.read_csv("data.csv", encoding='utf-8')
    print('The unique industries')
 

    unique_industries_dataframe = DataFrame.drop_duplicates(subset=['industry'])

    # # Create a new DataFrame with sector info
    sector_dataframe = create_new_dataframe_with_sector_industry_info(unique_industries_dataframe, sectors)
    print('The dataframe that contains the match between the csv file and the database sectors')
    print(sector_dataframe)
    if not sector_dataframe.empty:
            new_industries = sector_dataframe.to_dict(orient='records')
            
            existing_industries = set(get_industry_collection().distinct("sectorId"))
            new_industries_to_create = [industry for industry in new_industries if industry.get("sectorId") not in existing_industries]

            if new_industries_to_create:
                get_industry_collection().insert_many(new_industries_to_create)
                return f"- {len(new_industries_to_create)} new industries created successfully."
            else:
                return "- No new industries to create."
    else:
            return "- No new industries to create."


# API that creates an Industry manually in the database
@Main.post('/AdddIndustry')
async def create_industry(industry: Industry):
    print("Received industry object:", industry)
    
    industry_dict = dict(industry)
    print("Converted industry to dictionary:", industry_dict)
    
    get_industry_collection().insert_one(industry_dict)
    return 'New industry added successfully'




#API to get all the industries from the database
@Main.get('/AllIndustries')
async def find_all_industries():
    return serializeList(get_industry_collection().find())












# Function that takes the ISO code of the country and returns the flag URL
def CountryFlag(isoCode):
    lowerIsoCode=isoCode.lower()
    return f'https://flagcdn.com/w320/{lowerIsoCode}.png'

# Endpoint to get the flag URL of a country by its ISO code
@Main.get("/flag/{isoCode}")
def get_flag(isoCode: str):
    flag_url = CountryFlag(isoCode)
    return flag_url





#function that returns the official name of a country by its isoCode
def get_country_name(iso_code):
    base_url = "https://restcountries.com/v3/alpha/"
    url = f"{base_url}{iso_code}"
    response = requests.get(url)
    
    if response.status_code == 200:
        country_data = response.json()
        return country_data[0]['name']['common']
    else:
        return "Country not found"

# Endpoint to get the name of a country by its ISO code
@Main.get("/countryName/{isoCode}")
def get_CountryOfficialName(isoCode: str):
    print( get_country_name(isoCode))
    return(get_country_name(isoCode))



#Function that gets all the countries of the dataframe and insert them in the database with a url of thier flag and their official name
def CreatingCountries():
    start_time = time.time()
    print("starting time")

    DataFrame = pd.read_csv("data.csv", encoding='utf-8')



    #cleaning the information of the countries (dropping duplicants, removing empty values) 
    Uniquecountries = DataFrame['country'].drop_duplicates()
    UniquecountriesDF=Uniquecountries.to_frame()
    UniquecountriesDF.dropna(inplace=True)
    print("CleanedCountriesInformation")
    print(UniquecountriesDF)




    # Adding the columns of the official name of the country as well as its flag
    UniquecountriesDF['official_name'] = UniquecountriesDF['country'].apply(get_country_name)
    UniquecountriesDF['flag']=UniquecountriesDF['country'].apply(get_flag)

    print(UniquecountriesDF)
    print(type(UniquecountriesDF))



    if not UniquecountriesDF.empty:
        new_countries = UniquecountriesDF.to_dict(orient='records')
        
        existing_countries = set(get_countries_collection().distinct("country"))
        new_countries_to_create = [country for country in new_countries if country["country"] not in existing_countries]

        if new_countries_to_create:
            get_countries_collection().insert_many(new_countries_to_create)
            print( f"- {len(new_countries_to_create)} new countries created successfully.")
        else:
            print( "- No new countries to create.")
    else:
        print( "- No new countries to create.")
    



#API that launches the function CreatingCountries 
@Main.get('/CreatingCountries')
async def CountriesListAPI():    
    CreatingCountries()
    return("CountriesListAPI")

















# Function that creates new exchanges in the collection of exchange 
def creatingExchanges():
    DataFrame = pd.read_csv("data.csv", encoding='utf-8')


    DataFrame_Exchange = DataFrame[['exchange','exchangeShortName']]  

    print(DataFrame_Exchange)

    # Cleaning the dataframe of exchanges, removing redundant elements and removing also null and empty values
    UniqueExchanges = DataFrame_Exchange.drop_duplicates()
    UniqueExchanges.dropna(inplace=True)


    print('The exchange elements')
    print(UniqueExchanges)

    if not UniqueExchanges.empty:
        new_exchanges = UniqueExchanges.to_dict(orient='records')
        
        existing_exhanges = set(get_exchange_collection().distinct("exchange"))
        new_exchanges_to_create = [exchange for exchange in new_exchanges if exchange["exchange"] not in existing_exhanges]

        if new_exchanges_to_create:
            get_exchange_collection().insert_many(new_exchanges_to_create)
            print( f"- {len(new_exchanges_to_create)} new exchanges created successfully.")
        else:
            print( "- No new exchanges to create.")
    else:
        print( "- No new exchanges to create.")














#Function to see more the dataframe of the csv file 
def csv_file():
    DataFrame = pd.read_csv("data.csv", encoding='utf-8')


    # cleaning the dataframe
    DataFrameCompanies=DataFrame
    print("Longueur de la dataframe avant de lui associer la drop duplicates ")
    print(len(DataFrameCompanies))

    #removing duplicate elements of the dataframe
    print("Longueur de la dataframe après la drop duplicates ")
    DataFrameCleaned=DataFrameCompanies.drop_duplicates(subset='companyName')
    print(len(DataFrameCleaned))

    # removing nan elements
    print("Longueur de la dataframe après le remove des nan et des empty elements ")
    DataFrameCleaned=DataFrameCleaned.dropna(subset='companyName')
    print(len(DataFrameCleaned))

    #removing elements that have false isEtf
    DataFrameCleaned = DataFrameCleaned[DataFrameCleaned['isEtf'] == True]
    print("Longueur de la dataframe après le remove de isEtf ")
    print(len(DataFrameCleaned))




    print(DataFrameCleaned.columns.tolist())



    return len(DataFrame)



# API that launches the function creatingExchanges
@Main.get('/csv_file_len')
async def CountriesListAPI():    
    csv_file()
    return("csv_file Len API ")














# API that launches the function creatingExchanges
@Main.get('/creatingExchanges')
async def CountriesListAPI():    
    creatingExchanges()
    return("creatingExchangesAPI")















































@Main.get('/PrintingDataFrame')
async def find_all_industries():
    DataFrame = pd.read_csv("data.csv", encoding='utf-8')
    # Si vous souhaitez compter le nombre de duplications
    count_duplicates = DataFrame.duplicated().sum()
    unique_combinations = DataFrame[['industry', 'sector']]
    print('unique_combinations ',unique_combinations)

    unique_sectors = DataFrame.drop_duplicates(subset=['industry'])

    print('Unique sectors ')
    print(unique_sectors)
    np.savetxt('Unique_sectors.csv', unique_sectors, delimiter=';', fmt='%s', encoding='utf-8')



    unique_industries = DataFrame["industry"].unique()
    print('unique_industries  ')
    print(unique_industries)
    np.savetxt('unique_industries.csv', unique_industries, delimiter=';', fmt='%s')

    return 'PrintingDataFrame'


# from apscheduler.schedulers.background import BackgroundScheduler

# def run_job():

#     creatingExchanges()
#     CreatingCountries()



# scheduler = BackgroundScheduler()

# scheduler.add_job(run_job, trigger='interval', seconds=180, max_instances=1)

# scheduler.start() 