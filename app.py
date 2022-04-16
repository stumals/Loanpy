from flask import Flask, render_template
  
app = Flask(__name__)   

@app.route('/') 
def index():  
    return render_template('home.html')

@app.route('/login') 
def login():  
    return '<h1>login<h1/>'
  
if __name__ =='__main__':  
    app.run(debug = True)  
    