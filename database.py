from flask import request, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import json
import sys

sys.path.append("./UserTypes")
from UserTypes import *

def databaseInit(app):
    '''
    Initialize the database
    '''

    # Setup the mysql with information from config.json
    data = None
    try:
        with open("config.json", "r") as f:
            data = json.load(f)

    except FileNotFoundError:
        print("Config file cannot be found")
        exit(1)

    # configure db with your details
    app.config['SECRET_KEY'] = data["SECRET_KEY"]
    app.config['MYSQL_HOST'] = data['MYSQL_HOST']
    app.config['MYSQL_USER'] = data['MYSQL_USER']
    app.config['MYSQL_PASSWORD'] = data["MYSQL_PASSWORD"]
    app.config['MYSQL_DB'] = data["MYSQL_DB"]

    return MySQL(app)

def convertUser(account, acc_type):
    '''
    Convert raw query from the database and into a user object

    **THIS IS A HELPER FUNCTION, DO NOT USE IT BY ITSELF**
    '''
    if account["type"] == 'customer':
        return Customer(
            id=account["id"],          
            firstName=account["fname"],
            lastName=account["lname"],
            email=account["email"],
            username=account["username"],
            password=account["password"],
            phoneNumber=account["phone"],
            cardNumber=acc_type["cardnumber"],
            type="customer",
            wallet=acc_type["wallet"],
            address=acc_type["address"],
            num_orders=acc_type["num_orders"],
            total_spent=acc_type["total_spent"],
            warnings=acc_type["warnings"],
            isClosed=acc_type["isClosed"],
            isBlacklisted=acc_type["isBlacklisted"],
            isVIP=acc_type["isVIP"],
            free_deliveries=acc_type["free_deliveries"]
        )
    if account["type"] == 'manager':
        return Manager(
            id=account["id"],          
            firstName=account["fname"],
            lastName=account["lname"],
            email=account["email"],
            username=account["username"],
            password=account["password"],
            phoneNumber=account["phone"],
            type="manager"
        )
    if account["type"] == 'chef':
        return Staff(
            id=account["id"],
            firstName=account["fname"],
            lastName=account["lname"],
            email=account["email"],
            username=account["username"],
            password=account["password"],
            phoneNumber=account["phone"],
            salary=acc_type["salary"],
            compliments=acc_type["num_compliment"],
            complaints=acc_type["num_complaint"],
            warnings=acc_type["warnings"],
            demotions=acc_type["demotions"],
            type="chef"
        )
    if account["type"] == 'delivery':
        return Staff(
            id=account["id"],
            firstName=account["fname"],
            lastName=account["lname"],
            email=account["email"],
            username=account["username"],
            password=account["password"],
            phoneNumber=account["phone"],
            salary=acc_type["salary"],
            compliments=acc_type["num_compliment"],
            complaints=acc_type["num_complaint"],
            warnings=acc_type["warnings"],
            demotions=acc_type["demotions"],
            type="delivery"
        )

def getUserInDatabaseByLogin(db):
    '''
    Get a user from the database

    **USE THIS METHOD WHEN A USER IS ATTEMPTING TO LOG IN**

    return the user object if the account exist in the database 
    '''
    # fetch form data
    userDetails = request.form
    username = userDetails['username']
    password = userDetails['password']

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
        if account["type"] == 'customer':
            cursor.execute('SELECT * FROM customer WHERE customer_id = %s', (str(account["id"]),))
            customer = cursor.fetchone()
            if customer["isClosed"] == 1:
                flash('Account was recently closed.', category = 'error')
            elif customer["isBlacklisted"] == 1:
                flash('Account is blacklisted.', category = 'error')
            else:
                flash('Logged in successfully!', category = 'success')
                return convertUser(account, customer)
        if account["type"] == 'manager':
            cursor.execute('SELECT * FROM employee WHERE employee_id = %s', (str(account["id"]),))
            manager = cursor.fetchone()
            return convertUser(account, manager)
        if account["type"] == 'chef':
            cursor.execute('SELECT * FROM chef WHERE chef_id = %s', (str(account["id"]),))
            chef = cursor.fetchone()
            return convertUser(account, chef)
        if account["type"] == 'delivery':
            cursor.execute('SELECT * FROM delivery WHERE delivery_id = %s', (str(account["id"]),))
            delivery = cursor.fetchone()
            return convertUser(account, delivery)

    else:
        # account does not exist or username/password is incorrect
        flash('Username/password is incorrect.', category = 'error')
        return None

def getUserInDatabaseByID(db, id):
    '''
    Get a user from the database

    **USE THIS METHOD WHEN THE USER ID IS KNOWN**

    return the user object if the account exist in the database 
    '''
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (str(id)))
    account = cursor.fetchone()

    if account:
        if account["type"] == 'customer':
            cursor.execute('SELECT * FROM customer WHERE customer_id = %s', (str(id),))
            customer = cursor.fetchone()
            return convertUser(account, customer)
        if account["type"] == 'manager':
            cursor.execute('SELECT * FROM employee WHERE employee_id = %s', (str(id),))
            manager = cursor.fetchone()
            return convertUser(account, manager)
        if account["type"] == 'chef':
            cursor.execute('SELECT * FROM chef WHERE chef_id = %s', (str(id),))
            chef = cursor.fetchone()
            return convertUser(account, chef)
        if account["type"] == 'delivery':
            cursor.execute('SELECT * FROM delivery WHERE delivery_id = %s', (str(id),))
            delivery = cursor.fetchone()
            return convertUser(account, delivery)

    else: 
        return None


def verifyNewUser(db):
    '''
    Check to make sure that the new user creation is successful
    '''
    # fetch form data
    userDetails = request.form
    fname = userDetails['fname']
    lname = userDetails['lname']
    email = userDetails['email']
    username = userDetails['uname']
    password = userDetails['password']
    conpass = userDetails['conpass']
    phone = userDetails['phone']
    card = userDetails['cardnum']

    # checks requirements for registration
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
    account = cursor.fetchone()

    if account:
        if account["type"] == 'customer':
            cursor.execute('SELECT * FROM customer WHERE customer_id = %s', (str(account["id"]),))
            customer = cursor.fetchone()
            # customer is blacklisted
            if customer["isBlacklisted"] == 1:
                flash('Account was blacklisted. You can no longer register.', category = 'error')
        else:
            # username must be unique
            flash('Username already exists.', category = 'error')
            return False

    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        # email must be valid
        flash('Email address is invalid.', category = 'error')
    elif not re.search(r"[\d]+", password):
        # password must contain a digit
        flash('Password must contain at least 1 digit.', category = 'error')
    elif not re.search(r"[A-Z]+", password):
        # password must contain an uppercase letter
        flash('Password must contain at least 1 uppercase letter.', category = 'error')
    elif not re.search(r"[a-z]+", password):
        # password must contain a lowercase letter
        flash('Password must contain at least 1 lowercase letter.', category = 'error')
    elif len(password) < 8:
        # password must be at least 8 characters
        flash('Password must contain at least 8 characters.', category = 'error')
    elif password != conpass:
        # checks that password matches confirm password
        flash('Passwords do not match.', category = 'error')
    elif len(phone) != 10:
        # checks that phone number length is valid
        flash('Phone number is invalid. Must be 10 digits.', category = 'error')
    elif len(card) != 16:
        # checks that card number length is valid
        flash('Card number is invalid. Must be 16 digits.', category = 'error')
    else:
        # account pending creation. must be approved by manager to be added to database
        flash('Account successfully created!', category = 'success')
        # inserts new account into database after approval by manager
        cursor.execute("INSERT INTO accounts(fname, lname, email, username, password, phone) VALUES(%s, %s, %s, %s, %s, %s)", (fname, lname, email, username, password, phone))
        cursor.execute("INSERT INTO customer(customer_id) SELECT id FROM accounts WHERE lname = %s and email = %s and username = %s", (lname, email, username,))
        cursor.execute("UPDATE customer SET cardnumber = %s WHERE customer_id = (SELECT id FROM accounts WHERE username = %s)", (card, username,))
        db.connection.commit()
        cursor.close()

        return True

def forgotPassword(db):
    '''
    Updates password in database
    '''
    # fetch form data
    userDetails = request.form
    email = userDetails['email']
    username = userDetails['username']
    newpass = userDetails['newpass']
    conpass = userDetails['conpass']

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE email = %s AND username = %s', (email, username,))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
        if not re.search(r"[\d]+", newpass):
        # password must contain a digit
            flash('Password must contain at least 1 digit.', category = 'error')
        elif not re.search(r"[A-Z]+", newpass):
            # password must contain an uppercase letter
            flash('Password must contain at least 1 uppercase letter.', category = 'error')
        elif not re.search(r"[a-z]+", newpass):
            # password must contain a lowercase letter
            flash('Password must contain at least 1 lowercase letter.', category = 'error')
        elif len(newpass) < 8:
            # password must be at least 8 characters
            flash('Password must contain at least 8 characters.', category = 'error')
        elif newpass != conpass:
            # checks that password matches confirm password
            flash('Passwords do not match.', category = 'error')
        else:
            cursor.execute('UPDATE accounts SET password = %s WHERE email = %s AND username = %s', (newpass, email, username,))
            flash('Successfully changed password.', category = 'success')
            db.connection.commit()
            cursor.close()

            return True
    else:
        flash('Email/username does not exist.', category = 'error')

def changeAddress(db, user):
    '''
    Updates address in database
    '''
    # fetch form data
    userDetails = request.form
    address = userDetails['address']
    city = userDetails['city']
    state = userDetails['state']
    zipcode = userDetails['zipcode']

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (str(user.id),))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
            full_address = address + ", " + city + ", " + state + " " + zipcode
            if user.address == None:
                flash('Successfully set default address.', category = 'success')
            else:
                flash('Successfully changed address.', category = 'success')
            cursor.execute('UPDATE customer SET address = %s WHERE customer_id = %s', (full_address, str(user.id),))
            db.connection.commit()
            cursor.close()
            user.setAddress(user, full_address)

            return True
    else:
        flash('Email/username does not exist.', category = 'error')

def changeCard(db, user):
    '''
    Updates card number in database
    '''
    # fetch form data
    userDetails = request.form
    card = userDetails['card']

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (str(user.id),))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
        if len(card) != 16:
            # checks that card number length is valid
            flash('Card number is invalid. Must be 16 digits.', category = 'error')
        else:
            flash('Successfully changed payment method.', category = 'success')
            user.setCardNumber(db, card)
            
            return True
    else:
        flash('Email/username does not exist.', category = 'error')

    cursor.close()

def chargeFunds(db, user):
    '''
    Updates wallet in database
    '''
    # fetch form data
    userDetails = request.form
    funds = userDetails['funds']

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (str(user.id),))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
        if float(funds) <= 0:
            # checks that value to add is valid
            flash('Amount to be deposited must be $0.01 or more.', category = 'error')
        else:
            funds = float(funds) + user.wallet
            flash('Successfully deposited more funds.', category = 'success')
            user.setWallet(db, funds)

            return True
    else:
        flash('Email/username does not exist.', category = 'error')

    cursor.close()

def deleteAcc(db, user):
    '''
    Set account to closed in database
    '''

    # checks if user exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (str(user.id),))
    account = cursor.fetchone()

    # if account exists in the database
    if account:
        user.setisClosed(db, 1)
        # cursor.execute('DELETE FROM customer WHERE customer_id = %s', (str(user.id)))
        # cursor.execute('DELETE FROM accounts WHERE id = %s', (str(user.id)))
        db.connection.commit()
        cursor.close()

        return True

def updateQuantity(cart, index, action):
    '''
    Updates quantity in cart
    '''
    # decrease item quantity by 1
    if action == "minus":
        cart["quantity"][index] -= 1
    # increase item quantity by 1
    elif action == "plus":
        cart["quantity"][index] += 1
    return cart

def getCartItems(db, cart):
    '''
    Get cart items from database
    '''
    data = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    index = 0
    for item in cart["dish"]:
        cursor.execute('SELECT * FROM dish WHERE dish_id = %s', (str(item),))
        rawQuery = cursor.fetchone()
        rawQuery["quantity"] = cart["quantity"][index]
        index += 1
        data.append(rawQuery)

    return data

def getCartInfo(cart, vipStatus):
    '''
    Gets cart info based on customer's cart
    '''
    info = {}
    subtotal = 0
    num_items = 0
    for row in cart:
        subtotal += row["quantity"]*row["price"]
        num_items += row["quantity"]

    # Calculate the subtotal, tax, and total
    info["num_items"] = num_items
    info["subtotal"] = subtotal
    info["tax"] = round(subtotal*0.08875, 2)
    if vipStatus == 1:
        info["discount"] = round(subtotal*0.05, 2)
    else:
        info["discount"] = 0.00
    info["total"] = round(subtotal + info["tax"] - info["discount"], 2)

    return info

def getDishCount(db, dish_id):
    '''
    Gets dish count in database
    '''
    # checks if dish exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_id = %s', (str(dish_id),))
    dish = cursor.fetchone()
    cursor.close()

    if dish:
        return dish["count"]

def setDishCount(db, dish_id, num):
    '''
    Updates dish count in database
    '''
    # checks if dish exists in the database
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_id = %s', (str(dish_id),))
    dish = cursor.fetchone()

    if dish:
        cursor.execute('UPDATE dish SET count = %s WHERE dish_id = %s', (str(num), str(dish_id),))
        db.connection.commit()

    cursor.close()

def retrieveDispute(db):
    userDetails = request.form
    fname = userDetails['firstname']
    lname = userDetails['lastname']
    disputedescription = userDetails['deliverydispute']

    cursor = db.connection.cursor()
    #insert data into dispute table in database
    cursor.execute("INSERT INTO dispute (first_name, last_name, customer_id, dispute_content, dispute_date) VALUES(%s, %s, %s, %s, CURDATE())", (fname,lname,6,disputedescription))
    db.connection.commit()
    cursor.close()

    return True

def retrieveComplaint(db):
    print("test")
    userDetails = request.form
    fname = userDetails['firstname']
    lname = userDetails['lastname']
    complaintdescription = userDetails['complaintbox']

    cursor = db.connection.cursor()
    #insert data into dispute table in database
    cursor.execute("INSERT INTO complaint (first_name, last_name, customer_id, complaint_content, complaint_date) VALUES(%s, %s, %s, %s, CURDATE())", (fname,lname,6,complaintdescription))
    db.connection.commit()
    cursor.close()

    return True

def loadDisputes(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dispute')
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    cursor.close()
    return results

def loadPastDeliveries(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM PastDeliveries')
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    cursor.close()
    return results

def loadEntrees(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_type=%s', ['entree'])
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    print(results)
    cursor.close()
    return results

def loadAppt(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_type=%s', ['appetizer'])
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    print(results)
    cursor.close()
    return results

def loadDesserts(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_type=%s', ['dessert'])
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    print(results)
    cursor.close()
    return results

def loadDrinks(db):
    results = []
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM dish WHERE dish_type=%s', ['drink'])
    # for row in cursor.fetchall():
    #     print('row = %r' % (row,))
    # cursor.execute('SELECT COUNT(*) dispute')
    # print(cursor.execute('SELECT COUNT(*) dispute'))
    results = cursor.fetchall()
    print(results)
    cursor.close()
    return results

def edititem(db):
    itemDetails = request.form
    newimage = itemDetails['newimage']
    itemname = itemDetails['itemname']
    description = itemDetails['editdescription']
    editprice = itemDetails['editprice']
    dishid = itemDetails['dishid']

    print("deeznutz\n")
    print(dishid)
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('UPDATE dish SET img = %s, name = %s, description = %s,  price = %s WHERE dish_id = %s', (newimage,itemname,description,editprice,dishid))
    db.connection.commit()
    cursor.close()

def removeitem(db):
    itemDetails = request.form
    dishid = itemDetails['removeitem']
    print(dishid)
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('DELETE FROM dish WHERE dish_id=%s', [dishid] )
    db.connection.commit()
    cursor.close()

def additem(db):
    itemDetails = request.form
    chefid = itemDetails['chefid']
    itemtype = itemDetails['dishtype']
    itemimage = itemDetails['image']
    itemname = itemDetails['itemname']
    itemdescription = itemDetails['description']
    itemprice = itemDetails['price']
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('INSERT INTO dish (dish_type, name, price, description, img, chef) VALUES (%s, %s, %s, %s, %s, %s)', (itemtype, itemname, itemprice, itemdescription, itemimage, chefid))
    db.connection.commit()
    cursor.close()

def retrieveUsers(db):
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM chef INNER JOIN accounts WHERE chef_id = id')
    chef = cursor.fetchall()

    cursor.execute('SELECT * FROM delivery INNER JOIN accounts WHERE delivery_id = id')
    delivery = cursor.fetchall()

    cursor.execute('SELECT * FROM customer INNER JOIN accounts WHERE customer_id = id')
    customer = cursor.fetchall()

    # cursor.execute('SELECT * FROM customer WHERE isVIP = 1')
    # vip = cursor.fetchall()

    return chef, delivery, customer
