import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

# Create Flask app instance
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath('__file__')), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# Create a database engine
DATABASE_USERNAME = "wz2632"
DATABASE_PASSWRD = "6464"
DATABASE_HOST = "34.148.107.47"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"
engine = create_engine(DATABASEURI)
conn = engine.connect()
cursor = conn.execute('select 1') 

@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.
    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass

@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)

    # example of a database query
    select_query = "SELECT name from test"
    cursor = g.conn.execute(text(select_query))
    names = []
    for result in cursor:
        names.append(result[0])
    cursor.close()
    
    context = dict(data = names)
    return render_template("index.html", **context)

# Create an account/Login to account
@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        # Check if the user wants to create a new account
        if 'create_account' in request.form:
            # Get the user's information from the form
            username = request.form['username']
            password = request.form['password']
            account_type = request.form['account_type']

            # Check if the username is already taken
            cur = conn.cursor()
            cur.execute("SELECT * FROM %s WHERE username = %s", (account_type.upper(), username,))
            existing_user = cur.fetchone()
            if existing_user:
                flash('Username already taken!')
                return redirect(url_for('account'))

            # Insert the new user into the database
            if account_type == 'seller':
                cur.execute("INSERT INTO SELLER (username, password, email, address) VALUES (%s, %s, %s, %s)",
                        (username, password, email, address))
            else:
                cur.execute("INSERT INTO BUYER (username, password, email, address) VALUES (%s, %s, %s, %s)",
                        (username, password, email, address))

            conn.commit()
            cur.close()

            flash('Account created successfully!')
            return redirect(url_for('account'))

        # Check if the user wants to log in
        elif 'log_in' in request.form:
            # Get the user's information from the form
            username = request.form['username']
            password = request.form['password']
            account_type = request.form['account_type']

            # Check if the user exists in the database
            cur = conn.cursor()
            cur.execute("SELECT * FROM %s WHERE username = %s AND password = %s", 
                        (account_type.upper(), username, password))
            user = cur.fetchone()
            if not user:
                flash('Incorrect username or password!')
                return redirect(url_for('account'))

            # Store the user's information in the session
            session['username'] = user['username']
            session['account_type'] = account_type.upper()

            flash('Logged in successfully!')
            return redirect(url_for('home'))

    # If the request method is GET, render the account page
    return render_template('account.html')

@app.route("/buyers")
def list_buyers():
    """Display a list of all buyers"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM BUYER")
    buyers = cur.fetchall()
    cur.close()
    return render_template("list_buyers.html", buyers=buyers)

@app.route("/sellers")
def list_sellers():
    """Display a list of all sellers"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM SELLER")
    sellers = cur.fetchall()
    cur.close()
    return render_template("list_sellers.html", sellers=sellers)

@app.route("/products")
def list_products():
    """Display a list of all products"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM PRODUCT")
    products = cur.fetchall()
    cur.close()
    return render_template("list_products.html", products=products)

@app.route("/reviews")
def list_reviews():
    """Display a list of all reviews"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM REVIEW")
    reviews = cur.fetchall()
    cur.close()
    return render_template("list_reviews.html", reviews=reviews)

@app.route("/orders")
def list_orders():
    """Display a list of all orders"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM ORDERS")
    orders = cur.fetchall()
    cur.close()
    return render_template("list_orders.html", orders=orders)

# Buyer: order history
@app.route('/order_history')
def order_history():
    # Check if the user is logged in as a buyer
    if session.get('account_type') == 'BUYER':
        # Get the orders associated with the current user
        cur = conn.cursor()
        cur.execute("SELECT * FROM ORDERS WHERE username = %s", (session['username'],))
        orders = cur.fetchall()
        cur.close()

        # Render the order history page with the user's orders
        return render_template('order_history.html', orders=orders)
    else:
        # If the user is not a buyer, redirect them to the home page
        return redirect(url_for('home'))
    

# Seller: product selling
@app.route('/product_list')
def product_list():
    # Check if the user is logged in as a seller
    if session.get('account_type') == 'SELLER':
        # Get the products associated with the current user
        cur = conn.cursor()
        cur.execute("SELECT * FROM PRODUCTS WHERE seller_username = %s", (session['username'],))
        products = cur.fetchall()
        cur.close()

        # Render the product list page with the user's products
        return render_template('product_list.html', products=products)
    else:
        # If the user is not a seller, redirect them to the home page
        return redirect(url_for('home'))

# Search for a product
@app.route('/search')
def search():
    search_query = request.args.get('q')
    cur = conn.cursor()
    cur.execute("SELECT * FROM PRODUCT WHERE name ILIKE %s", ('%' + search_query + '%',))
    products = cur.fetchall()
    return render_template('search_results.html', products=products)

# View for product details
@app.route('/product/<int:product_id>')
def product_details(product_id):
    # Query the database for product details
    cur = conn.cursor()
    cur.execute("SELECT * FROM PRODUCT WHERE id = %s", (product_id,))
    product = cur.fetchone()

    # Query the database for the seller's details
    cur.execute("SELECT * FROM SELLER WHERE id = %s", (product['seller_id'],))
    seller = cur.fetchone()

    # Render the product details page
    return render_template('product_details.html', product=product, seller=seller)

# View for reviews
@app.route('/product/<int:product_id>/reviews')
def reviews(product_id):
    # Query the database for the reviews for the given product
    cur = conn.cursor()
    cur.execute("SELECT * FROM REVIEWS WHERE product_id = %s", (product_id,))
    reviews = cur.fetchall()

    # Render the reviews page
    return render_template('reviews.html', reviews=reviews)

# Buyer: place an order
@app.route('/product/<int:product_id>/order', methods=['POST'])
def create_order(product_id):
    # Get the user's information from the session
    username = session.get('username')
    account_type = session.get('account_type')

    # Get the order details from the form
    quantity = request.form['quantity']

    # Insert the order into the database
    cur = conn.cursor()
    cur.execute("(product_id, buyer_id, seller_id, quantity, total_price, order_date,payment_method, payment_status, shipping_method, shipping_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (product_id, username, account_type, quantity, shipping_address))
    conn.commit()
    cur.close()

    flash('Order created successfully!')
    return redirect(url_for('product_details', product_id=product_id))

# Seller: post a product
@app.route('/post_product', methods=['GET', 'POST'])
def post_product():
    if request.method == 'POST':
        # Get the product information from the form
        name = request.form['name']
        price = request.form['price']
        status = request.form['status']
        seller_id = session['seller_id']  # Get the seller's ID from the session

        # Insert the new product into the database
        cur = conn.cursor()
        cur.execute("INSERT INTO PRODUCT (name, description, price, quantity, seller_id) VALUES (%s, %s, %s, %s, %s)", (name, description, price, quantity, seller_id))
        conn.commit()
        cur.close()

        flash('Product posted successfully!')
        return redirect(url_for('home'))

    # If the request method is GET, render the post product page
    return render_template('post_product.html')

# Seller: delete a product
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Check if the user is a seller
    if 'username' not in session or session['account_type'] != 'SELLER':
        flash('You do not have permission to perform this action!')
        return redirect(url_for('account'))

    # Delete the product from the database
    cur = conn.cursor()
    cur.execute("DELETE FROM PRODUCT WHERE id = %s AND seller_id = %s", (product_id, session['seller_id'],))
    conn.commit()
    cur.close()

    flash('Product deleted successfully!')
    return redirect(url_for('my_products'))

# Buyer: write a review
def write_review():
    """Write a new review in the database"""
    if request.method == "POST":
        product_id = request.form["product_id"]
        buyer_id = request.form["buyer_id"]
        rating = request.form["rating"]
        comment = request.form["comment"]
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO REVIEW (product_id, buyer_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (product_id, buyer_id, rating, comment),
        )
        conn.commit()
        cur.close()
        return "Review added successfully"
    else:
        return render_template("write_review.html")

if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:
        
            python server.py

        Show the help text using:

            python server.py --help

        """
        
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()