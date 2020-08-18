from flask import Flask, render_template, request

app = Flask(__name__)
#
#
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        req = request.form.to_dict()
        term = req['term']
        print(term)
        return render_template('home.html')


if __name__ == '__main__':
    app.run()
