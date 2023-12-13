import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create a sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    x_min = st.slider("X-axis minimum", 0, 100, 0)
    x_max = st.slider("X-axis maximum", 0, 100, 100)
    y_min = st.slider("Y-axis minimum", 0, 100, 0)
    y_max = st.slider("Y-axis maximum", 0, 100, 100)

# Create a container for the main body of the dashboard
main_container = st.container()

# Create four columns for the charts
col1, col2, col3, col4 = main_container.columns(4)

# Generate some sample data
x = np.random.randn(1000)
y = np.random.randn(1000)

# Create the first chart
with col1:
    st.line_chart(data=pd.DataFrame({"x": x, "y": y}), x_range=(x_min, x_max), y_range=(y_min, y_max))

# Create the second chart
with col2:
    st.area_chart(data=pd.DataFrame({"x": x, "y": y}), x_range=(x_min, x_max), y_range=(y_min, y_max))

# Create the third chart
with col3:
    st.bar_chart(data=pd.DataFrame({"x": x, "y": y}), x_range=(x_min, x_max), y_range=(y_min, y_max))

# Create the fourth chart
with col4:
    st.scatter_chart(data=pd.DataFrame({"x": x, "y": y}), x_range=(x_min, x_max), y_range=(y_min, y_max))

st.run()