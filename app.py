#%%
import re
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
    return render_template('home.html')

@app.route('/calculations', methods=['GET', 'POST']) 
def calculations():
    data = {}
    if request.method == 'POST':
        if request.form['start'] == '': start = 400000.0
        else: start = float(request.form['start']) 
        if request.form['end'] == '': end = 600000.0
        else: end = float(request.form['end']) 
        if request.form['years'] == '': years = 10.0
        else: years = float(request.form['years']) 
        cagr = ((end/start)**(1/years) - 1)*100
        
        data['cagr_data'] = []
        data['cagr_data'].append(['Start Value: ', '{:,.0f}'.format(start)])
        data['cagr_data'].append(['End Value: ', '{:,.0f}'.format(end)])
        data['cagr_data'].append(['Years: ', '{:,.0f}'.format(years)])
        data['cagr_data'].append(['CAGR: ', '{:,.3f}'.format(cagr)])

    return render_template('calculations.html', data=data)

@app.route('/mortgage_analysis', methods=['GET', 'POST']) 
def mortgage_analysis():
    data = {}
    if request.method == 'POST':
        #form_data = request.form
        form_data = {}

        if request.form['amount'] == '': form_data['amount'] = 400000
        else: form_data['amount'] = request.form['amount']
        if request.form['rate'] == '': form_data['rate'] = .05
        else: form_data['rate'] = request.form['rate']
        if request.form['num_years'] == '': form_data['num_years'] = 30
        else: form_data['num_years'] = request.form['num_years']
        if request.form['pmt_freq'] == '': form_data['pmt_freq'] = 12
        else: form_data['pmt_freq'] = request.form['pmt_freq']
        if request.form['down_pmt'] == '': form_data['down_pmt'] = 0
        else: form_data['down_pmt'] = request.form['down_pmt']
        if request.form['closing_cost'] == '': form_data['closing_cost'] = 0
        else: form_data['closing_cost'] = request.form['closing_cost']
        if request.form['maint_rate'] == '': form_data['maint_rate'] = .01
        else: form_data['maint_rate'] = request.form['maint_rate']
        if request.form['prop_tax_rate'] == '': form_data['prop_tax_rate'] = .01
        else: form_data['prop_tax_rate'] = request.form['prop_tax_rate']
        if request.form['pmi_rate'] == '': form_data['pmi_rate'] = .01
        else: form_data['pmi_rate'] = request.form['pmi_rate']
        if request.form['home_value_appreciation'] == '': form_data['home_value_appreciation'] = .03
        else: form_data['home_value_appreciation'] = request.form['home_value_appreciation']
        if request.form['home_sale_percent'] == '': form_data['home_sale_percent'] = .06
        else: form_data['home_sale_percent'] = request.form['home_sale_percent']

        if request.form['closing_cost_finance'] == 'Yes':
            closing_cost_finance = True
        else:
            closing_cost_finance = False
        l = Loan(float(form_data['amount']), float(form_data['rate']), int(form_data['num_years']), pmt_freq=int(form_data['pmt_freq']),
                down_pmt=float(form_data['down_pmt']), closing_cost=float(form_data['closing_cost']), closing_cost_finance=closing_cost_finance, 
                prop_tax_rate=float(form_data['prop_tax_rate']), pmi_rate=float(form_data['pmi_rate']), 
                maint_rate=float(form_data['maint_rate']), home_value_appreciation=float(form_data['home_value_appreciation']),
                home_sale_percent=float(form_data['home_sale_percent']))
        data['start_val'] = l.asset_start_value
        data['down_pmt'] = l.down_pmt * l.asset_start_value
        if l.closing_cost_finance:
            data['closing_cost'] = l.closing_cost
        else:
            data['closing_cost'] = 0
        data['pmt'] = l.pmt
        data['amt'] = l.amt
        data['rate'] = l.rate_annual
        data['num_years'] = l.num_years

        df_detail = l.amort_table_detail()

        data['summary_info'] = []
        data['summary_info'].append(['Asset Value:', '{:,.0f}'.format(l.asset_start_value), 'Property Tax Rate:', form_data['prop_tax_rate']])
        data['summary_info'].append(['Down Payment (-)', '{:,.0f}'.format(l.down_pmt * l.asset_start_value), 'PMI Rate:', form_data['pmi_rate']])
        data['summary_info'].append(['Closing Cost +', '{:,.0f}'.format(l.closing_cost), 'Maintenance Rate:', form_data['maint_rate']])
        data['summary_info'].append(['Loan Amount =', '{:,.0f}'.format(l.asset_start_value - l.down_pmt * l.asset_start_value + l.closing_cost), 'Home Appreciation Rate:', form_data['home_value_appreciation']])
        data['summary_info'].append(['Rate:', '{:.2f}'.format(l.rate_annual), 'Home Sale Percent:', form_data['home_sale_percent']])
        data['summary_info'].append(['Years:', '{:.0f}'.format(form_data['num_years']), '', ''])
        data['summary_info'].append(['Frequency:', '{:.0f}'.format(form_data['pmt_freq']), '', ''])
        data['summary_info'].append(['Mortgage Payment:', '{:,.0f}'.format(l.pmt), '', ''])

        df_detail['total'] = df_detail[['pmt', 'pmi', 'prop_tax', 'maint']].sum(axis=1)
        total = df_detail[['year', 'total']].groupby('year').mean().loc[:,'total'].to_list()
        total_pmt = [['Year ' + str(i+1), total[i]] for i in range(len(total))]
        data['total_pmt'] = total_pmt

        df_pmt = df_detail[['year', 'pmt', 'prop_tax', 'maint', 'pmi', 'total']]
        df_pmt = df_pmt.groupby('year').mean()
        d = df_pmt.transpose().values.tolist()
        for i in range(len(d)):
            for j in range(len(d[i])):
                d[i][j] = '{:,.0f}'.format(d[i][j])
        data['pmt_detail'] = d

        data['profit'] = l.profit_loss_summary(monthly=False, expand=True).iloc[:15,-1].to_list()

        num_years = 15
        row_headers = l.profit_loss_summary(monthly=False, expand=True).transpose().iloc[:,:num_years].index.tolist()
        data_values = l.profit_loss_summary(monthly=False, expand=True).transpose().iloc[:,:num_years].values.tolist()
        for i in range(len(data_values)):
            for j in range(len(data_values[i])):
                data_values[i][j] = '{:,.0f}'.format(data_values[i][j])
        for i in range(len(data_values)):
            data_values[i].insert(0, row_headers[i])
        data['profit_detail'] = data_values
        h = l.profit_loss_summary(monthly=False, expand=True).transpose().iloc[:,:num_years].columns.tolist()
        h_year = ['Year ' + str(i) for i in h]
        h_year.insert(0, 'Profit Detail')
        data['profit_detail_headers'] = h_year

    return render_template('mortgage_analysis.html', data=data)

@app.route('/mortgage_comparison') 
def mortgage_comparison():  
    return render_template('mortgage_comparison.html')

@app.route('/data_analysis') 
def data_analysis():
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

    d = ed.EconData(start_date='2012-01-01')
    d.stock_data()
    df = d.df.reset_index()
    df_sp500 = df.copy()
    df_sp500['date'] = df_sp500['date'].dt.strftime('%Y-%m-%d')
    df_sp500['date'] = df_sp500['date'].astype(str)
    df_sp500 = df_sp500.rename(columns={'SP500':'value'})
    data['sp500'] = df_sp500.to_json(orient='records')

    d = ed.EconData(start_date='2000-01-01')
    d.money_supply()
    df = d.df.reset_index()
    df_m2 = df.copy()
    df_m2['date'] = df_m2['date'].astype(str)
    df_m2 = df_m2.rename(columns={'M2SL':'value'})
    data['m2'] = df_m2.to_json(orient='records')

    return render_template('data_analysis.html', data=data)
  
if __name__ =='__main__':  
    app.run(debug = True)  
    
# %%
d = ed.EconData(start_date='2022-03-01')
d.ustreasury_rates()
d.df.head()
# %%
d = ed.EconData(start_date='2000-01-01')
d.money_supply()
d.df
# %%
