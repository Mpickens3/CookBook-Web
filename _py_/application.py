from flask import Flask, redirect, render_template, request, session, url_for
import requests
import json
import bcrypt
import secrets
from jinja2 import Environment, FileSystemLoader

from model import cleanhtml

from flask_mysqldb import MySQL
import MySQLdb.cursors
import re


app = Flask(__name__)
# 8ab81808358c443ea76599f43aad0582
# 521c6cc3130f4396b970e4b5c2aeb98a
# 13880dee2bf04507982cfdff92631f6b
API_KEY = "13880dee2bf04507982cfdff92631f6b"

mysql = MySQL(app)

app.config['MYSQL_HOST'] = 'database.cc7ets5jy5vi.us-west-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'csc481'
app.config['MYSQL_PASSWORD'] = 'drinkwtr753'
app.config['MYSQL_DB'] = 'cook_book_data'


class result:
    def __init__(self, id, image, title, ):
        self.id = id
        self.image = image
        self.title = title

class recipe:
    def __init__(self, title, image, ingredients, summary, instructions):
        self.title = title
        self.ingredients = ingredients
        self.summary = summary
        self.instructions = instructions 
        self.image = image   

@app.route("/")
@app.route('/index/<msg>')
@app.route('/index')
def index():
    return render_template("index.html")


# user login in sequence
@app.route('/Login/<msg>', methods =['GET', 'POST'])
@app.route('/Login', methods =['GET', 'POST'])
def login(msg = None):
    # pre checks, this branch is the validation branch
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # retrieves the user inputs from the web form
        username = request.form['username']
        password = request.form['password']
        # initializes the database pointer and executes a serach with given paramaters
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM userprofile WHERE username = % s AND pword = % s', (username, password, ))
        account = cursor.fetchone()
        # account found branch, renders with welcome back prompt
        if account:
            msg = 'welcome back'
            return render_template('login.html' , msg=msg)
        
        #no account found brnach 
        msg = 'Invalid credentials, Try again'
        return render_template('login.html', msg = msg)
    # no user inpu branch
    return render_template('login.html')


@app.route("/Signup")
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'address' in request.form and 'city' in request.form and 'country' in request.form and 'postalcode' in request.form and 'organisation' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # future use code
        # address = request.form['address']
        # city = request.form['city']
        # state = request.form['state']
        
        # this block of code was modified from https://www.geeksforgeeks.org/profile-application-using-python-flask-and-mysql/
        # which was found when researching MYSQL and flask examples
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        # if an account is returned, one already exists
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        # validation checks for inputs
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        # if inputs are acceptable, add to database
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template(url_for('index'), msg = msg)


# user search to search protein ingredient and send request to API then returns JSON data.
@app.route("/searchRecipes")
def searching():
        return render_template('searchRecipes.html')

@app.route('/results')
def order():
        temp = request.args.get('ingredient')
    # Temporary workaround with using checkboxes
        temp2 = request.args.getlist('options')
        theList = temp
        for i in temp2:
            theList = theList + ", " + i

        query = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={theList}&number=3&apiKey={API_KEY}"

        # veggies = request.args('options', )
        # print(veggies)
        response = requests.get(query)
        results = json.loads(response.text)

        theList = []
        content = False

        for item in results:
            for entry in item:
                if "id" in entry:
                    id = item[entry]
                    content = True
                if "title" in entry:
                    title = item[entry]
                    content = True

                if "image" in entry:
                    img = item[entry]
                    content = True
                    break
                else:
                    content = False
            if content:
                theList.append(result(id, img, title))
                content = False
        print(theList)
        return render_template("results.html", results = theList)

@app.route("/recipe")
def instructions():
    
    info = request.args.get('recipeId')
    query = f"https://api.spoonacular.com/recipes/{info}/information?&apiKey={API_KEY}"

    data = requests.get(query)
    results = json.loads(data.text)
    
    theRecipe = []
    content = False
    ingredients = ""

    for item in results:
        if item == "extendedIngredients":
            for stuff in results[item]:
                for da in stuff:
                    if "nameClean" in da:
                        if ingredients == "":
                            ingredients = ingredients + "" + stuff[da] + "\n"
                        else:
                            ingredients = ingredients + ", "+ stuff[da] + "\n"
                        content = True
        # These are good!!!
        if item == "summary":
            summary = results[item]
            content = True
        if item == "instructions":
           instructions = results[item]
           content = True

        if item == "title":
            title= (results[item])
            content = True
        if item == "image":
            image = results[item]
            content = True


    placeHolder = cleanhtml(summary)
    place = placeHolder.rfind("If you like this recipe")
    summary = placeHolder[:place]

    # instructions_list = instructions.split("<li>")
    # print(instructions_list)
    # # Remove the first item which is the opening <ol> tag
    # instructions_list.pop(0)
    # # Loop through the list and remove the closing </li> tags
    # for i in range(len(instructions_list)):
    #     instructions_list[i] = instructions_list[i].split("</li>")[0]

    # print(instructions_list)
    if content:
        theRecipe.append(recipe(title, image, ingredients, summary, instructions))
        content = False

    return render_template("recipe.html", information = theRecipe)


@app.route("/about")
def about():
    return render_template("about.html")