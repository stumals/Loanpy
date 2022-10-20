#%%
#from crypt import methods
from flask import Flask, render_template, url_for, request
from loanpy import Loan
import econ_data as ed
import json
#%%

app = Flask(__name__)

#%%
d = ed.EconData(start_date='2000-01-01')
d.median_home_price()
df = d.df.reset_index().iloc[:,:2]
df['date'] = df['date'].astype(str)
df.to_json(orient='records')

#%%
@app.route('/') 
def home(): 
    data = {}
    d = ed.EconData(start_date='2012-01-01')
    d.mortgage_rates()
    df = d.df.reset_index().iloc[:,:2]
    df_rate = df.copy()
    df['date'] = df['date'].astype(str)
    df = df.rename(columns={'30yr_FRM':'value'})
    data['mort_rate'] = df.to_json(orient='records')

    d = ed.EconData(start_date='2012-01-01')
    d.home_price()
    df = d.df.reset_index().iloc[:,[0,-1]]
    df_price = df.copy()
    df['date'] = df['date'].astype(str)
    df = df.rename(columns={'price_adj':'value'})
    df['value'] = df['value'] / 1000
    data['home_price'] = df.to_json(orient='records')

    df_pmt = ed.pmt_df(df_price, df_rate)
    df_pmt['date'] = df_pmt['date'].astype(str)
    df_pmt = df_pmt.rename(columns={'pmt':'value'})
    data['pmt'] = df_pmt.to_json(orient='records')

    return render_template('home.html', data=data)

@app.route('/mortgage_analysis') 
def mortgage_analysis():
    return render_template('mortgage_analysis.html')

@app.route('/mortgage_comparison') 
def mortgage_comparison():  
    return render_template('mortgage_comparison.html')

@app.route('/data_analysis') 
def data_analysis():  
    return render_template('data_analysis.html')
  
if __name__ =='__main__':  
    app.run(debug = True)  
    