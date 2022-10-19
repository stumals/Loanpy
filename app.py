#%%
#from crypt import methods
from flask import Flask, render_template, url_for, request
from loanpy import Loan
from econ_data import EconData as ed
import json
#%%

app = Flask(__name__)

@app.route('/') 
def home(): 
    mr = ed()
    mr.mortgage_rates()
    homepage_data = mr.df.iloc[:,0].reset_index().to_json(orient='records')
    return render_template('home.html', data=homepage_data)

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
    