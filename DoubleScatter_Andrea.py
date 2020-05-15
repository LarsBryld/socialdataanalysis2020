
# import required packages 
import pandas as pd
import numpy as np
import urllib.request as urllib2
from datetime import datetime, timedelta, date
 
from bokeh.models import Slider, ColumnDataSource, Paragraph, HoverTool, DateRangeSlider, DateSlider
from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.layouts import row, gridplot, column, widgetbox
from bokeh.plotting import figure 
from bokeh.transform import factor_cmap, factor_mark
from bokeh.resources import INLINE
output_notebook(INLINE)


# ## Data manipulation

# Import Oxford data and enrich columns for future merging needs
df = pd.read_csv('https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv')
df['Date'] = pd.to_datetime(df['Date'], format="%Y%m%d")
df['DateString'] = df['Date'].apply(lambda x: datetime.strftime(x, "%Y%m%d"))
df['Index'] = df['CountryCode'] + df['DateString']

# Calculate Death Rates
df['DeathRate'] = df['ConfirmedDeaths'] / df['ConfirmedCases']

stocks = pd.read_excel('https://raw.githubusercontent.com/LarsBryld/socialdataanalysis2020/master/data/Markets.xlsx')
stocks = stocks.groupby('CountryCode',sort=False).sum()
#stocks = stocks.rename({'United Kingdom': 'United Kingdom'}, axis='index')

# Reference dates: 23rd and 24th March 2020
market0 = stocks[datetime(2020, 3, 23, 0, 0)]
for i in (8, 9, 10, 16, 17, 20, 21, 27, 29, 30, 31, 32):                            #range(1,len(stocks)):
    market0.iloc[i] = stocks[datetime(2020, 3, 24, 0, 0)][i]

# Market Performance
mkt_p = stocks.T/market0 -1
mkt_p = mkt_p.T
#mkt_p = mkt_p.reindex(focuscountries)

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

# Add Market Performance to Oxford file 
df = df.merge(mkt_p1, left_on = 'Index', right_on = 'Index', how = 'left')
df = df[df['MarketPerformance'].notna()]
df['Date_x'] = df['Date_x'].dt.date         # setting Date_xad datetime object


def make_dataset(day):
    subset = df[df['Date_x'] == day]
    subset = subset[subset['MarketPerformance'].notna()]
    mp = subset['MarketPerformance']
    si = subset['StringencyIndex']
    dr = subset['DeathRate']    
    src = ColumnDataSource(data={
        'x'       : si,
        'y'       : mp,
        'z'       : dr,
        'country' : subset['CountryName']})
    return src


# Startinng Plot
src = make_dataset(date(2020, 4, 15))

p1 = figure(x_axis_label='StringencyIndex', y_axis_label='MarketPerformance',
           plot_height=400, plot_width=700,  y_range=(0, 0.4),
           tools=[HoverTool(tooltips='@country')])
p1.circle(x='x', y='y', source=src)

p2 = figure(x_axis_label='StringencyIndex', y_axis_label='DeathRate',
           plot_height=400, plot_width=700,  y_range=(0, 0.2),
           tools=[HoverTool(tooltips='@country')])
p2.circle(x='x', y='z', source=src)

# update function
def update_plot(attr, old,new):
    day = datetime.utcfromtimestamp(slider.value//1000.0)
    day = day.date()
    new_src = make_dataset(day)
    src.data.update(new_src.data)
    p1.title.text = 'Markets VS Govs Stringency, {:%d %b %Y}'.format(day) #'CovIndex, %d' %day
    p2.title.text = 'Deaths VS Govs Stringency, {:%d %b %Y}'.format(day) #'CovIndex, %d' %day


slider = DateSlider(title="Date Range: ",
                         start=date(2020, 3, 25),
                         end=date(2020, 4, 15),
                         value=date(2020, 3, 25),
                         step= 86400000
                        )


slider.on_change('value', update_plot)

# Create a row layout
#plots = row(p, p)
#layout = column(plots, slider)
layout = column(row(p1,p2),column(slider))
#layout = column(p,column(date_slider))
curdoc().add_root(layout)


#Display plot inline in Jupyter notebook
#output_notebook()

#Display plot
#show(layout)

# Activate callback function with Bokeh Server 
# (run the command below on Anaconda Prompt, from the corect directory)
# (it will open a new browser page)
# bokeh serve --show DoubleScatter_Andrea.py





