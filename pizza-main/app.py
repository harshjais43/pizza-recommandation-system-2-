from flask import Flask, render_template, session, request, redirect
import sqlite3 as sql
from sklearn.cluster import KMeans
from apyori import apriori

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = b'poornima123456789'

con = sql.connect('pizzas.db')
cursor = con.cursor()
con.execute('CREATE TABLE IF NOT EXISTS users (username varchar unique, password varchar);')
con.execute('CREATE TABLE IF NOT EXISTS orders (username varchar, pizza_id integer);')
con.execute('CREATE TABLE IF NOT EXISTS pizzas (id integer primary key, name varchar, toppings text);')
ret_piz = """INSERT INTO pizzas (name, toppings) VALUES
    ('Margherita', 'Tomato, Mozzarella, Basil'),
    ('Pepperoni', 'Tomato, Mozzarella, Pepperoni'),
    ('Vegetarian', 'Tomato, Mozzarella, Mushrooms, Bell Peppers, Onions'),
    ('Hawaiian', 'Tomato, Mozzarella, Ham, Pineapple'),
    ('Meat Lovers', 'Tomato, Mozzarella, Pepperoni, Sausage, Bacon'),
    ('BBQ Chicken', 'BBQ Sauce, Mozzarella, Chicken, Red Onions, Cilantro'),
    ('Mediterranean', 'Tomato, Mozzarella, Feta Cheese, Kalamata Olives, Spinach, Red Onions'),
    ('Supreme', 'Tomato, Mozzarella, Pepperoni, Sausage, Mushrooms, Bell Peppers, Onions, Black Olives');"""
con.execute(ret_piz)

#@app.route('/')
#def index():
#    if 'username' not in session:
#        return redirect('/login')
#    pizzas = get_all_pizzas()
#    recommendations = get_recommendations(session['username'])
#    return render_template('index.html', username=session['username'], pizzas=pizzas, recommendations=recommendations)
#

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = con.execute("SELECT * FROM users WHERE username=? AND password=?;", (username, password)).fetchone()
        if user is not None:
            session['username'] = username
            return redirect('/')
        else:
            return render_template("login.html", error="Invalid Username or Password")
    return render_template("login.html")

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        cpassword = request.form['cpassword']
        if password==cpassword:
            con.execute("INSERT INTO users VALUES (?,?);", (username, password))
            session['username'] = username
            return redirect('/')
        else:
            return render_template("register.html", error="Password and Confirm Password don't match")
    return render_template("register.html")

@app.route('/pizzas')
def pizzas():
    return render_template("pizzas.html")

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

def get_all_pizzas():
    return con.execute('SELECT * FROM pizzas;').fetchall()

def get_user_orders(username):
    return con.execute('SELECT * FROM orders WHERE username=?;', (username,)).fetchall()

def create_order(username, pizza_id):
    con.execute('INSERT INTO orders VALUES (?, ?);', (username, pizza_id))
    con.commit()

def get_recommendations(username):
    user_orders = get_user_orders(username)
    user_pizza_ids = [order[1] for order in user_orders]
    all_pizzas = get_all_pizzas()
    pizza_toppings = [pizza[2].split(', ') for pizza in all_pizzas]

    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(pizza_toppings)
    pizza_clusters = kmeans.labels_
    transactions = [[str(pizza_id) for pizza_id in all_pizzas[i][0] if pizza_clusters[i] == kmeans.cluster_label] for i in range(len(all_pizzas))]
    association_rules = apriori(transactions, min_support=0.2, min_confidence=0.2)
    recommendations = []

    for rule in association_rules:
        if len(rule.items) == 2 and str(user_pizza_ids[-1]) in rule.items:
            recommended_pizza = con.execute('SELECT * FROM pizzas WHERE id=?;', (rule.items[1],)).fetchone()
            recommendations.append(recommended_pizza)

    return recommendations
