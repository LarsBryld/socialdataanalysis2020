# -*- coding: utf-8 -*-
"""Copy of Scatter2D.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MFZ1JwkxUbxApJbuz9EYrUNDMPF5z2a6
"""

# import required packages 
from bokeh.models import Slider, ColumnDataSource
from bokeh.io import curdoc
from bokeh.layouts import row 
from bokeh.plotting import figure

#create data for the plot 

from numpy.random import random

initial_points = 500 

data_points = ColumnDataSource(data = {'x' : random(initial_points), 'y' : random(initial_points)})

#create the actual plot

plot = figure(title = 'Scatter Plot with Slider')

plot.diamond(x = 'x', y = 'y', source= data_points, color = 'red' )

#create the slider widget 

slider_widget = Slider(start=0, end=10000, step=10, value=initial_points, title='Slide right to increase number of points')

#define call back function

def callback(attr, old, new):
  points = slider_widget.value
  data_points.data = ({'x' : random(points), 'y' : random(points)})
slider_widget.on_change('value', callback)

#create the actual secon plot

plot2 = figure(title = 'Scatter Plot with Slider')

plot2.diamond(x = 'x', y = 'y', source= data_points, color = 'red' )

#create layout for application

layout = row(slider_widget, plot, plot2)

#add layout to application

curdoc().add_root(layout)