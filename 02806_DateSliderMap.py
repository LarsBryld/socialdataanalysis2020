import pandas as pd
import numpy as np
from datetime import datetime, date
import geopandas as gpd
import json

from urllib.request import urlopen
from zipfile import ZipFile
from io import StringIO, BytesIO

from bokeh.io import output_notebook, show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, Slider, HoverTool
from bokeh.models.widgets import DateSlider
from bokeh.palettes import brewer, Turbo256
from bokeh.layouts import widgetbox, row, column
import bokeh.io
from bokeh.resources import INLINE
bokeh.io.output_notebook(INLINE)


# Import Oxford Government Respost Tracker and enrich columns for future merging needs
df = pd.read_csv('https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv')
df['Date'] = pd.to_datetime(df['Date'], format="%Y%m%d")
df['DateString'] = df['Date'].apply(lambda x: datetime.strftime(x, "%Y%m%d"))
df['Index'] = df['CountryCode'] + df['DateString']

# Calculate Death Rates
df['DeathRate'] = df['ConfirmedDeaths'] / df['ConfirmedCases'] * 100

# Import Stock Markets data and manipulate them
stocks = pd.read_csv('https://raw.githubusercontent.com/LarsBryld/socialdataanalysis2020/master/data/Markets.csv',
                     encoding= 'unicode_escape'
                    )
stocks = stocks.groupby('CountryCode',sort=False).sum()
#stocks = stocks.rename({'United Kingdom': 'United Kingdom'}, axis='index')
#stocks = stocks.drop(columns=['Index ', 'Country/Region'])

columns_new = np.array(stocks.columns)
for i in range(len(columns_new)):
    columns_new[i] = datetime.strptime(columns_new[i],'%d/%m/%Y')

stocks.columns = columns_new

# Reference dates: 23rd and 24th March 2020
market0 = stocks[datetime(2020, 3, 23, 0, 0)]
for i in (8, 9, 10, 16, 17, 20, 21, 27, 29, 30, 31, 32):                            #range(1,len(stocks)):
    market0.iloc[i] = stocks[datetime(2020, 3, 24, 0, 0)][i]
    
# Calculating Market Performance
mkt_p = stocks.T/market0 -1
mkt_p = mkt_p.T * 100

# Converting Market Performances data from rows to columns
mkt_p1 = pd.DataFrame(mkt_p[mkt_p.columns[0]])
mkt_p1['Date'] = mkt_p1.columns.repeat(len(mkt_p1))
mkt_p1.rename(columns={mkt_p1.columns[0]:'MarketPerformance', 'Date':'Date'}, inplace=True)

for i in range(1, len(mkt_p.columns)):
    mkt_p_new = pd.DataFrame(mkt_p[mkt_p.columns[i]])
    mkt_p_new['Date'] = mkt_p_new.columns.repeat(len(mkt_p))
    mkt_p_new.rename(columns={mkt_p_new.columns[0]:'MarketPerformance', 'Date':'Date'}, inplace=True)
    mkt_p1 = pd.concat([mkt_p1, mkt_p_new], axis=0)

# Adding columns needed for merging with Oxford data
mkt_p1['DateString'] = mkt_p1['Date'].apply(lambda x: datetime.strftime(x, "%Y%m%d"))
mkt_p1['Index'] = mkt_p1.index + mkt_p1['DateString']

# Merge Oxford data and Market Performance
df = df.merge(mkt_p1, left_on = 'Index', right_on = 'Index', how = 'left')
df = df.rename({'Date_x': 'Date',
                'DateString_x': 'DateString'}, axis='columns')
df = df.drop(columns=['Date_y', 'DateString_y'])

# Calculate our CovIndex plus cleaning all N/As
df['CovIndex'] = (df['MarketPerformance'] - df['DeathRate']) #* 100
df = df[df['CovIndex'].notna()]

# Import shapefiles needed for Map plotting
county_file_url = 'https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip'
zipfile = ZipFile(BytesIO(urlopen(county_file_url).read()))
filenames = [y for y in sorted(zipfile.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)] 

shapefile = filenames[2] #'ne_110m_admin_0_countries.shp'                #
gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
gdf.columns = ['country', 'country_code', 'geometry']
gdf = gdf.drop(gdf.index[159])


#Define a function that returns json_data for year selected by user.
def json_data(selectedDay):   #(selectedYear):
    day = selectedDay         #selectedYear
    df_day = df[df['Date'] == day]
    merged = gdf.merge(df_day, left_on = 'country_code', right_on = 'CountryCode', how = 'left')
    merged.fillna('No data', inplace = True)
    merged = merged.drop(columns=['Date'])    
    merged_json = json.loads(merged.to_json())
    json_data = json.dumps(merged_json)
#    json_data = df_day
    return json_data


#Input GeoJSON source that contains features for plotting.
geosource = GeoJSONDataSource(geojson = json_data(datetime(2020, 3, 25, 0, 0)))

#Define a sequential multi-hue color palette.
palette = Turbo256#.reverse() #brewer['YlGnBu'][8]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors. Input nan_color.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40, nan_color = '#d9d9d9')

#Define custom tick labels for color bar.
tick_labels = {'0': '0%', '5': '5%', '10':'10%', '15':'15%', '20':'20%', '25':'25%', '30':'30%','35':'35%', '40': '>40%'}

#Add hover tool
hover = HoverTool(tooltips = [('Covid19 Index','@CovIndex'),
                              ('Market Performance','@MarketPerformance'),
                              ('Death Rate', '@DeathRate')])
#hover = HoverTool(tooltips = [ ('Country/region','@country'),('% obesity', '@per_cent_obesity')])

#Create color bar. 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal', major_label_overrides = tick_labels)


#Create figure object.
p = figure(title = 'CovIndex, April 15th, 2020', plot_height = 600 , plot_width = 950, toolbar_location = None, 
           tools = [hover]
          )
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

#Add patch renderer to figure. 
p.patches('xs','ys', source = geosource,fill_color = {'field' :'CovIndex', #'per_cent_obesity',
                                                      'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)

p.add_layout(color_bar, 'below')

# Define the callback function: update_plot
def update_plot(attr, old, new):
    day = datetime.utcfromtimestamp(date_slider.value//1000.0) #date_slider.value   #slider.value
    new_data = json_data(day)
    geosource.geojson = new_data
    p.title.text = 'CovIndex, {:%d %b %Y}'.format(day) #'CovIndex, %d' %day



date_slider = DateSlider(title="Date Range: ",
                         start=date(2020, 3, 25),
                         end=date(2020, 5, 14),
                         value=date(2020, 3, 25),
                         step= 86400000
                        )      # https://discourse.bokeh.org/t/bokeh-dateslider-still-broken/2466

date_slider.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(p,column(date_slider))
curdoc().add_root(layout)

#Display plot inline in Jupyter notebook
#output_notebook()

#Display plot
#show(layout)

# Activate callback function with Bokeh Server 
# (run the command below on Anaconda Prompt, from the corect directory)
# (it will open a new browser page)
# bokeh serve --show 02806_DateSliderMap.py

