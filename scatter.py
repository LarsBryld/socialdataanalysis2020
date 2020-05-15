# -*- coding: utf-8 -*-
"""scatter.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/LarsBryld/socialdataanalysis2020/blob/master/DoubleScatter.ipynb
"""

# import required packages 
import pandas as pd
import numpy as np
import urllib.request as urllib2
from datetime import datetime, timedelta, date
 
from bokeh.models import Slider, ColumnDataSource, Paragraph, HoverTool, DateRangeSlider, DateSlider, Panel, Paragraph
from bokeh.models.widgets import Tabs, Panel
from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.layouts import row, gridplot, column, widgetbox
from bokeh.plotting import figure 
from bokeh.transform import factor_cmap, factor_mark
from bokeh.resources import INLINE
output_notebook(INLINE)

"""## Data manipulation"""

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

df.head(5)

df['Date_x'] = df['Date_x'].dt.date         # setting Date_xad datetime object
df.head(5)

# ref link https://nbviewer.jupyter.org/github/billsanto/notebook_examples/blob/master/bokeh_hover_test.ipynb

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

src = make_dataset(date(2020, 4, 15))
#src.data

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


#from bokeh.models import Panel
#from bokeh.models.widgets import Tabs


# Create a row layout
#plots = row(p, p)
#layout = column(plots, slider)
layout = column(row(p1,p2),column(slider))
#layout = column(p,column(date_slider))
    
# Make a tab with the layout 
#tab = Panel(child=layout, title = 'Scatter')
#tabs = Tabs(tabs=[tab])

#Display plot inline in Jupyter notebook
output_notebook()



# Activate callback function with Bokeh Server 
# (run the command below on Anaconda Prompt, from the corect directory)
# (it will open a new browser page)
# bokeh serve --show DoubleScatter_Andrea.py

# Create text paragraph
welcome_message = 'This tab demonstrates the correlation between goverment responses (StringencyIndex) and stock market performance (MarketPerformance)\
The right plot demonstrates the correlation between goverment responses (StringencyIndex) and the death rate from Covid-19.     '
welcome_banner = Paragraph(text=welcome_message)

# Make a tab with the layout 
layout = gridplot([[column(slider), row(p1,p2)]], 
                   plot_width=250, plot_height=250)
tab = Panel(child=layout, title = 'Scatter Plot')
tabs = Tabs(tabs=[tab])

#Display plot
show(tabs) 

curdoc().add_root(tabs)