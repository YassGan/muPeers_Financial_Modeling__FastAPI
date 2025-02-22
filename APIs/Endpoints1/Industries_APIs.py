


from fastapi import APIRouter,Response
from models.Sector import Sector 

from config.db import get_database 
from schemas.Industry import serializeDict, serializeList

import os

import pandas as pd


import requests

import time


Industry=APIRouter()





def get_sector_collection():
    db = get_database()
    return db["sectors"]




def get_industry_collection():
    db = get_database()
    return db["industries"]

industriesCollection=get_industry_collection()



#find_industry_id_by_name
def find_industry_id_by_name(IndustryName):
    result = industriesCollection.find_one({
        'Industry': IndustryName
    })
    
    if result:
        return str(result['_id'])
    else:
        return "not found "




import pandas as pd

# Function that creates new industries from the dataframe that match the sectors' elements from the database
def create_new_industries(dataframe):
    # Fetch all sectors from the database
    sectors = serializeList(get_sector_collection().find())
    dataframe = dataframe.drop_duplicates(subset='industry').dropna(subset='industry')
    print("Nombre d'industries ",len(dataframe))


    # Read the DataFrame from your data CSV file

    sector_industry_data = []
    for index, row in dataframe.iterrows():
        sector_name = row['sector']
        for sector_obj in sectors:
            if sector_obj['name'] == sector_name:
                sector_industry_data.append({
                    "Industry": row['industry'],
                    "sector": sector_obj['name'],
                    "sectorId": sector_obj['_id']
                })
    df_sector_industry_data = pd.DataFrame(sector_industry_data)

    if not df_sector_industry_data.empty:
        new_industries = df_sector_industry_data.to_dict(orient='records')
        existing_industries = set(get_industry_collection().distinct("sectorId"))
        new_industries_to_create = [industry for industry in new_industries if industry.get("sectorId") not in existing_industries]

        if new_industries_to_create:
            get_industry_collection().insert_many(new_industries_to_create)
            return f"------------> {len(new_industries_to_create)} new industries created successfully."
        else:
            return "----------> No new industries to create."
    else:
        return "----------> No new industries to create."

# API that calls the function to create new industries
@Industry.get('/v1/CreateIndustries')
async def create_industries_api():
    dataframe = pd.read_csv(os.getenv("CSV_FILE"), encoding='utf-8')

    result = create_new_industries(dataframe)
    return result









#API to get all the industries from the database
@Industry.get('/v1/AllIndustries')
async def find_all_industries():
    return serializeList(get_industry_collection().find())










# # Function that creates new industries from the dataframe that matches the sectors elements from the databse 
# def create_new_dataframe_with_sector_industry_info():
#     sectors = serializeList(get_sector_collection().find())
#     # # Read the DataFrame from your data
#     dataframe = pd.read_csv(os.getenv("CSV_FILE"), encoding='utf-8')
#     sector_industry_data = []
#     print('the data frame ')
#     print(dataframe)
#     print('the sectors from the database  ')
#     print(sectors)

#     for index, row in dataframe.iterrows():
#         sector_name = row['sector']
#         for sector_obj in sectors:
#             if sector_obj['name'] == sector_name:
#                 sector_industry_data.append({
#                     "Industry": row['industry'],
#                     "sector": sector_obj['name'],
#                     "sectorId": sector_obj['_id']
#                 })
 
 
#     df_sector_industry_data = pd.DataFrame(sector_industry_data)
#     return(df_sector_industry_data)

 
# #API that calls the function that creates the new elements industry in the database
# @Industry.get('/CreateIndustries')
# async def create_dataframe_with_sector_info():
#     # Fetch all sectors from the database
#     sectors = serializeList(get_sector_collection().find())
#     # # Read the DataFrame from your data
#     DataFrame = pd.read_csv(os.getenv("CSV_FILE"), encoding='utf-8')
#     #print('The unique industries')
 

#     unique_industries_dataframe = DataFrame.drop_duplicates(subset=['industry'])

#     # # Create a new DataFrame with sector info
#     sector_dataframe = create_new_dataframe_with_sector_industry_info()
#     # print('The dataframe that contains the match between the csv file and the database sectors')
#     # print(sector_dataframe)
#     if not sector_dataframe.empty:
#             new_industries = sector_dataframe.to_dict(orient='records')
            
#             existing_industries = set(get_industry_collection().distinct("sectorId"))
#             new_industries_to_create = [industry for industry in new_industries if industry.get("sectorId") not in existing_industries]

#             if new_industries_to_create:
#                 get_industry_collection().insert_many(new_industries_to_create)
#                 return f"------------> {len(new_industries_to_create)} new industries created successfully."
#             else:
#                 return "----------> No new industries to create."
#     else:
#             return "----------> No new industries to create."








