# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 16:49:42 2020

@author: Satish
"""

import os
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import pydeck as pdk
import statsmodels.api as sm
import matplotlib as mpl
#from config import toll_dict, DATA_DIR, MODEL_DIR, GEOJSON_URL
from config import config
import sys 
#sys.path.append('<directory path of FileA.py>')



# Get data
@st.cache(persist=True, suppress_st_warning=True, allow_output_mutation=True)
def get_data():
    # Read toll location and toll collection data
    toll_location = pd.read_csv(os.path.join(config.DATA_DIR, 'toll_locations.csv'))
    toll_collection = pd.read_csv(os.path.join(config.DATA_DIR, 'ahdt.csv'))
    hourly_data = pd.read_csv(os.path.join(config.DATA_DIR, 'tollwise_final.csv'))
    
    # Merge dataframe to include data into a single dataframe
    df_merge = pd.merge(toll_collection, toll_location, left_on='plaza_id', right_on='toll_id')
    
    # Drop column containing common data
    df_merge = df_merge.drop(columns=['plaza_id'])
    return toll_location, df_merge, hourly_data

@st.cache(persist=True, suppress_st_warning=True, allow_output_mutation=True)
def get_weekly_data(data):
    dates = pd.to_datetime(data.date, cache=True)
    times = pd.to_timedelta(data.hour, unit='h')
    data['datetimes']  = dates + times
    data = data.drop(columns=['date', 'hour', 'toll_id', 'longitude', 'latitude'])
    weekly_data = data.groupby(['datetimes','direction']).agg({'vehicles_etc_e_zpass':'sum',
                                              'vehicles_cash_vtoll': 'sum'}).reset_index()
    weekly_data = weekly_data.set_index("datetimes")
    return weekly_data[:168]

@st.cache(persist=True, suppress_st_warning=True, allow_output_mutation=True)
def get_model():
    model = sm.load(os.path.join(config.MODEL_DIR, 'toll_tsmodel.pkl'))
    return model
    
def get_key(name):
   for key, value in config.toll_dict.items():
      if name == value:
         return key    
    
def main():
    st.title('Toll collection forecast')
    df, _, _ = get_data()
    
    # Add dropdown to filter toll data
    _, df_merge, _ = get_data()
    toll = df_merge['toll_id'].unique()
    toll.sort()
    
    toll_tuple = tuple(config.toll_dict.values())
    
    toll_name_selected = st.sidebar.selectbox('Select toll', toll_tuple)
    toll_selected = get_key(toll_name_selected)
    
    data_selected = df_merge[df_merge.toll_id == int(toll_selected)]
    
    # Display few rows of data
    if st.sidebar.checkbox('Show first few rows of the data:'):
        st.subheader('Daily toll collection data')
        st.dataframe(data_selected.head())
        
    # Display radio button for forecast plot
    forecast = st.sidebar.radio("Select forecast", ('Daily', 'Weekly'))
    if forecast == 'Daily':
        period = 24
    else:
        period = 24*7    
    
    # Disply forecast plot
    _, _, hourly_data = get_data()
    hourly_data = hourly_data[hourly_data.toll_id == int(toll_selected)]
    
    hourly_data = hourly_data.set_index('time')
    hourly_data.index = pd.to_datetime(hourly_data.index)
    hourly_data = hourly_data.resample('H').sum()

    start_date = hourly_data.tail(1).index.item()
    end_date = pd.to_datetime(start_date) + pd.to_timedelta(period, unit = 'h' )
    
    # Create forecast
    y_predict = get_model().predict(start= start_date, end= end_date)
    # Create a similar date range equal to future periods.
    dt_forecast = pd.date_range(start=start_date, end= end_date, freq='H')
    # Create a dataframe to index as dt_forecast and data as y_predict
    df_y_predict = pd.DataFrame(index=dt_forecast, data=y_predict)
    df_y_predict.columns = ['vehicular_total']

    if st.sidebar.checkbox('Show forecast plot:'):
        # Plot the results
        mpl.style.use('seaborn')
        plt.figure(figsize=(10,8))
        plt.plot(hourly_data.iloc[-400:, 0:1], 'b', label='Vehicular Traffic')
        plt.plot(df_y_predict.index, df_y_predict.vehicular_total, 'g-', label='Predicted Traffic')
        plt.legend(loc='upper right', frameon=True)
        plt.title('Vehicle Traffic Forecast')
        st.pyplot()
    
    # Display forecast revenue
    st.write('Revenue forecast:', int(df_y_predict.sum()*50), ("$"))
     
    
    # Display weekply plot
    st.subheader('Daily toll collection at toll:')
    plot_data = get_weekly_data(data_selected)
    sns.lineplot(x=plot_data.index, y="vehicles_etc_e_zpass", hue="direction", data=plot_data, palette="Set2")
    st.pyplot()
    
    # Display map
    st.subheader('Toll location map')
    if st.button('Full Extents'):
        st.map(df)
    else:
        long = data_selected['longitude'].head(1).values
        lat = data_selected['latitude'].head(1).values
        
        LAND_COVER = [[[73.733470,19.935080], [73.718670,19.983620], [73.716270,20.029560], 
                       [73.758070,20.053070]]]
     
                
        INITIAL_VIEW_STATE = pdk.ViewState(latitude=lat[0], longitude=long[0], zoom=11, max_zoom=16)
        
        
        selection = pdk.Layer('ScatterplotLayer', data=df[df.toll_id == int(toll_selected)], get_position='[longitude, latitude]', 
                           get_color='[0, 255, 0, 160]', get_radius=300)
        
        label = pdk.Layer("TextLayer", df, pickable=True, get_position='[longitude, latitude]',
                         get_text="toll_id", get_size=16, get_color=[255, 255, 255], get_angle=0,
                          # Note that string constants in pydeck are explicitly passed as strings
                          # This distinguishes them from columns in a data set
                          get_text_anchor="'middle'", get_alignment_baseline="'center'")
        
        point = pdk.Layer('ScatterplotLayer', data=df, get_position='[longitude, latitude]', 
                           get_color='[255, 0, 0, 160]', get_radius=200)
        
        polygon = pdk.Layer('PolygonLayer', LAND_COVER, stroked=False, 
                               # processes the data as a flat longitude-latitude pair
                               get_polygon='-', get_fill_color=[0, 0, 0, 20])
        
        geojson = pdk.Layer('GeoJsonLayer', config.GEOJSON_URL, opacity=0.8, stroked=False,filled=True,
                               extruded=True, wireframe=True, get_elevation='properties.Ward_No / 20',
                               get_fill_color='[255, 255, properties.Ward_No]',
                               get_line_color=[0, 0, 0], pickable=True)
        
        r = pdk.Deck(map_style='mapbox://styles/mapbox/light-v9',
                     layers=[selection, label, point, polygon, geojson], initial_view_state=INITIAL_VIEW_STATE)

        r.to_html()
    
        st.pydeck_chart(r)
        
   
if __name__ == '__main__':
    main()