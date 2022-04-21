from flask import Flask, render_template, url_for, request
from loanpy import Loan

app = Flask(__name__)

@app.route('/') 
def home():  
    return render_template('home.html')

@app.route('/mortgage_analysis', methods=['GET', 'POST']) 
def mortgage_analysis():
    data = {}
    if request.method == 'POST':
        form_data = request.form
        l = Loan(float(form_data['amount']), float(form_data['rate']), int(form_data['num_years']), pmt_freq=int(form_data['pmt_freq']),
                down_pmt=float(form_data['down_pmt']), closing_cost=float(form_data['closing_cost']), 
                prop_tax_rate=float(form_data['prop_tax_rate']), pmi_rate=float(form_data['pmi_rate']), 
                maint_rate=float(form_data['maint_rate']), home_value_appreciation=float(form_data['home_value_appreciation']),
                home_sale_percent=float(form_data['home_sale_percent']))
                
        data['pmt'] = l.pmt
        data['amt'] = l.amt
        data['rate'] = l.rate_annual
        data['num_years'] = l.num_years
        data['pmt_matrix'] = l.pmt_matrix(variance=True)
        if form_data['amort_table_detail'] == 'Yes':
            data['amort_table'] = l.amort_table_detail()
        elif form_data['amort_table_detail'] == 'No':
            data['amort_table'] = l.amort_table()

    return render_template('mortgage_analysis.html', data=data)

@app.route('/mortgage_comparison') 
def mortgage_comparison():  
    return render_template('mortgage_comparison.html')

@app.route('/data_analysis') 
def data_analysis():  
    return render_template('data_analysis.html')
  
if __name__ =='__main__':  
    app.run(debug = True)  
    