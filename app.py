from flask import Flask, render_template, url_for
  
app = Flask(__name__)

@app.route('/') 
def home():  
    return render_template('home.html')

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
    