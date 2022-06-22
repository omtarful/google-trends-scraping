# %% [markdown]
# # Scraping Project

# %% [markdown]
# ## Connecting to Google Trends
# This code connects to google trends and created a function to convert terms to topic ids to perform topic search when possible.

# %%
#This lines connect to Google Trends
from pytrends.request import TrendReq
import pandas as pd
import re
from itertools import product
import requests
import time
from datetime import datetime

#Sets up language to host language
pytrends = TrendReq(hl='en-US')
#function takes as input a keyword and returns topic id
def getTopicID(word):
    #get suggested searches for word
    suggs = []
    try:
        suggs = pytrends.suggestions(word)
    except requests.exceptions.Timeout:
        print("Timeout ocurred")
  

    #check each suggestion and see if contains a topic
    for s in range(len(suggs)):
        #if the type of suggestion is a topic, return the topic id
        pattern = suggs[s].get("title").lower() + "(s|es|os)"
        if suggs[s].get("type") == "Topic" and (suggs[s].get("title").lower() == word.lower() or re.match(pattern, word.lower() )): 
            return(suggs[s].get("mid"))
    #returns None if there is no topic id
    return word
     

# %% [markdown]
# Here we choose the payload parameters for the request to be sent to the server. There are 5 different inputs to the payload like the original platform. Wrapped it in a function to get table for all topics and comparisons.

# %%
#function to get interest over time depending on the region
def get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop):
    attempts, fetched = 0, False
    #converts kw to ids to do topic look up
    topicID_list = [getTopicID(kw) for kw in kw_list]
    comp_topicID = [getTopicID(kw) for kw in kw_comp_list] 
    #keyword dictionary used to rename columns
    #keys are ids, values are keywords
    kw_dict = dict(zip(topicID_list, kw_list))
    kw_dict.update(dict(zip(comp_topicID, kw_comp_list)))
    objective_df = pd.DataFrame()
    all_columns = topicID_list + [e for e in product(comp_topicID, topicID_list)]  
    for column in all_columns:
        term = [column] if isinstance(column, str) else column
        #catches exception when there is a timeout on google trends
        #it's useful to continue running after timeout
        try:
            pytrends.build_payload(
                kw_list= term,
                cat = 0,
                timeframe = timeframes,
                geo = geo,
                gprop = ""
                    )
           
            time.sleep(0) #wait some seconds before sending the next request
            #for a larger number of requests it should wait 60s
        except requests.exceptions.Timeout:
            print("Timeout ocurred")
       
        partial_data = pytrends.interest_over_time() #data per column
        #handle in case there are no results
        if(partial_data.empty):
            partial_data[term] = "" 
        else:
            partial_data = partial_data.drop("isPartial", axis = 1) #deletes column that has partial data
        #change column name 
        #2 cases
        #2 columns
        #if else statement to determine how to name columns
        if(len(partial_data.columns) > 1):
            #change column name to term_term2
            partial_data.rename(columns = kw_dict, inplace=True)
            new_col_names = {partial_data.columns[0]:(partial_data.columns[0] + "_" + partial_data.columns[1]),
                            partial_data.columns[1]:(partial_data.columns[1] + "_" + partial_data.columns[0])}
            partial_data.rename(columns = new_col_names, inplace=True)
        if(len(partial_data.columns) == 1):
            #change column name to term2_term
            partial_data.rename(columns = kw_dict, inplace=True)
        #1 columns  
        objective_df = pd.concat([objective_df, partial_data], axis=1)
    return(objective_df)
#italy dataframe
#function accepts the following arguments
#list of keywords used in the search
kw_list = ["Global warming", "climate change", "greenhouse gas", "renewable energy", 
            "sustainability", "Climate disaster", "green energy", "green investment",
            "green production"]  
kw_comp_list = ["Job", "health", "education", "drugs"]
gprop = '' #web search
ct = 0 #means all categories


# %%
topicID_list = [getTopicID(kw) for kw in kw_list]
comp_topicID = [getTopicID(kw) for kw in kw_comp_list] 
#keyword dictionary used to rename columns
#keys are ids, values are keywords
kw_dict = dict(zip(topicID_list, kw_list))
kw_dict.update(dict(zip(comp_topicID, kw_comp_list)))
objective_df = pd.DataFrame()
all_columns = topicID_list + [e for e in product(comp_topicID, topicID_list)]  
print(getTopicID("health"))
print(all_columns)

# %% [markdown]
# ## Italy
# ### National 
# #### Monthly

# %%
#geographical location
geo = 'IT' #Italy
#time frame
timeframes = '2010-01-01 2021-12-31' 
italy_2010_monthly_df = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
#write to csv
italy_2010_monthly_df.to_csv("italy_2010_monthly_interest_over_time.csv")
#italy monthly 2011 - 2021
timeframes = '2011-01-01 2021-12-31' 
italy_2011_monthly_df = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
#write to csv file
italy_2011_monthly_df.to_csv("italy_2011_monthly_interest_over_time.csv")

# %% [markdown]
# #### Quarterly

# %%
def to_quartertly(df):
    grouper = df.groupby([pd.Grouper(freq='Q')])
    region_df_quarter = grouper.mean().reset_index()
    #format date to look decent
    return(region_df_quarter)
italy_2010_quarterly_df = to_quartertly(italy_2010_monthly_df)
italy_2010_quarterly_df.to_csv("italy_2010_quarterly_interest_over_time.csv", index=False)
italy_2011_quarterly_df = to_quartertly(italy_2011_monthly_df)
italy_2011_quarterly_df.to_csv("italy_2011_quarterly_interest_over_time.csv", index=False)


# %% [markdown]
# ### Regional

# %%
def get_regional_data(kw_list, kw_comp_list, timeframes, ct, geo, gprop):
    #get regions
    regions = []
    try:
        pytrends.build_payload(
            kw_list= [kw_list[0]],
            cat = 0,
            timeframe = timeframes,
            geo = geo,
            gprop = ""
            )
        #returns region ISO code
    except requests.exceptions.Timeout:
        print("Timeout ocurred")
    regions = pytrends.interest_by_region(inc_geo_code=True)
    #extract region ISO code from df
    geos = regions.geoCode
    #create regional data frame
    region_df = pd.DataFrame()
    #gets interest over time for each region and then appends them together
    for i in range(len(geos)):
        regions = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geos[i], gprop)
        regions.insert(loc=0, column="Region", value=geos.index[i])
        region_df = region_df.append(regions)
    region_df.insert(1, 'date', region_df.index)
    region_df.reset_index(drop = True)
    return(region_df)


# %% [markdown]
# #### Monthly

# %%
timeframes = '2010-01-01 2021-12-31' 
geo = "IT"
italy_region_2010_monthly_interest_over_time = get_regional_data(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
italy_region_2010_monthly_interest_over_time.to_csv("italy_region_2010_monthly_interest_over_time.csv", index=False)


# %%
timeframes = '2011-01-01 2021-12-31' 
italy_region_2011_monthly_interest_over_time = get_regional_data(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
italy_region_2011_monthly_interest_over_time.to_csv("italy_region_2011_monthly_interest_over_time.csv", index=False)

# %% [markdown]
# #### Quarterly

# %%
#converts data to quarter and writes in csv file
def to_quarter(df):
    df = df.fillna(-1)
    grouper = df.groupby(["Region", pd.Grouper(freq='Q')], dropna=False)
    region_df_quarter = grouper.mean().reset_index()
    region_df_quarter.level_1 = pd.DatetimeIndex(region_df_quarter.level_1).to_period('Q')
    region_df_quarter.rename(columns = {'level_1':'date'}, inplace = True)
    region_df_quarter = region_df_quarter.replace(-1, "")
    return(region_df_quarter)
to_quarter(italy_region_2010_monthly_interest_over_time).to_csv("italy_region_2010_quarterly_interest_over_time.csv", index=False)
to_quarter(italy_region_2011_monthly_interest_over_time).to_csv("italy_region_2011_quarterly_interest_over_time.csv", index=False)


# %%
for key in kw_dict:
    if(key == kw_dict[key]):
        print(key)

# %% [markdown]
# Topic search was done on these terms:

# %%
#UAE national (monthly) from Jan 2016 until December 2021
geo = "AE"
timeframes = '2016-01-01 2021-12-31'
uae_2016_monthly_df = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
uae_2016_monthly_df.index = pd.DatetimeIndex(uae_2016_monthly_df.index)
uae_2016_monthly_df.index.name = "date"
uae_2016_monthly_df.index = uae_2016_monthly_df.index.to_period("M")
uae_2016_monthly_df.to_csv("uae_2016_monthly_interest_over_time.csv")

# %% [markdown]
# ### Daily

# %%
#swap columns so date appears before region
uae_region_2016_monthly_df.to

# %%
#UAE regions (daily) from Jan 2016 until December 2021
geo = "AE"
timeframes = '2021-07-01 2021-12-31'
uae_2021_daily_df = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
uae_2021_daily_df.index = pd.DatetimeIndex(uae_2021_daily_df.index)
uae_2021_daily_df.index.name = "date"
uae_2021_daily_df.to_csv("uae_2021_daily_interest_over_time.csv")

# %% [markdown]
# ## US

# %%


# %% [markdown]
# ### Regional

# %%
#USA national (monthly) from Jan 2004 until December 2019
geo = "US"
timeframes = '2004-01-01 2019-12-31'
us_2004_monthly_df = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geo, gprop)
us_2004_monthly_df.to_csv("us_2004_monthly_interest_over_time.csv")

# %%
pd.value_counts(set(us_region_2004_monthly_1_df.Region))

# %%
us_region_2004_monthly_2_df = pd.DataFrame()
part_2 = range(math.ceil(len(geos)/2), len(geos))
for i in part_2:
    regions = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geos[i], gprop)
    regions.insert(loc=0, column="Region", value=geos.index[i])
    us_region_2004_monthly_2_df = us_region_2004_monthly_2_df.append(regions)

# %%
#code to join
us_region_2004_monthly_df = us_region_2004_monthly_1_df.append(us_region_2004_monthly_2_df)
us_region_2004_monthly_df.to_csv("us_region_2004_monthly_interest_over_time.csv")

# %% [markdown]
# # Notes

# %%
topicID_list = [getTopicID(kw) for kw in kw_list]
comp_topicID = [getTopicID(kw) for kw in kw_comp_list] 
#keyword dictionary used to rename columns
#keys are ids, values are keywords
kw_dict = dict(zip(topicID_list, kw_list))
kw_dict.update(dict(zip(comp_topicID, kw_comp_list)))



# %%
us_2004_monthly_df.to_csv("us_2004_monthly_interest_over_time.csv")

# %%
import math
regions = []
try:
    pytrends.build_payload(
        kw_list= [kw_list[0]],
        cat = 0,
        timeframe = timeframes,
        geo = geo,
        gprop = ""
        )
    #returns region ISO code
except requests.exceptions.Timeout:
    print("Timeout ocurred")
regions = pytrends.interest_by_region(inc_geo_code=True)
#extract region ISO code from df
geos = regions.geoCode
#create regional data frame
us_region_2004_monthly_1_df = pd.DataFrame()
#gets interest over time for each region and then appends them together
part_1 = range(math.ceil(len(geos)/2))

for i in part_1:
    regions = get_interest_over_time(kw_list, kw_comp_list, timeframes, ct, geos[i], gprop)
    regions.insert(loc=0, column="Region", value=geos.index[i])
    us_region_2004_monthly_1_df = us_region_2004_monthly_1_df.append(regions)

# %%
for key in kw_dict:
    if(key != kw_dict[key]):
        print(kw_dict[key])



