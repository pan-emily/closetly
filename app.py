"""
Python app to interface with Closetly MySQL database
"""
import sys  # to print error messages to sys.stderr
import mysql.connector
# To get error codes from the connector, useful for user-friendly
# error-handling
import mysql.connector.errorcode as errorcode
import pandas as pd

# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client. Set to False when done testing.
DEBUG = True # MAKE FALSE WHEN SUBMITTING  

def get_conn():
    """"
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        conn = mysql.connector.connect(
          host='localhost',
          user='appadmin',
          # Find port in MAMP or MySQL Workbench GUI or with
          # SHOW VARIABLES WHERE variable_name LIKE 'port';
          port='8889',
          password='adminpw',
          database='closetly'
        )
        if DEBUG:
            print('Successfully connected.')
        return conn
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in your
        # simulated program. Their user information would be in a users table
        # specific to your database.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr('Incorrect username or password when connecting to DB.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr('Database does not exist.')
        elif DEBUG:
            sys.stderr(err)
        else:
            sys.stderr('An error occurred, please contact the administrator.')
        sys.exit(1)

# ----------------------------------------------------------------------
# Functions for Logging Users In
# ----------------------------------------------------------------------
def check_username(username):
    # access user_info to obtain the set of all usernames available
    sql = "SELECT COUNT(*) FROM (SELECT username FROM user_info WHERE username='" + username + "') as matches;"
    cursor = conn.cursor()
    cursor.execute(sql, )
    # check if the given username exists in the username table
    # return true if it does exist and false if not
    return bool(cursor.fetchone()[0])

def authenticate_login(username, password):
    sql = 'SELECT authenticate (%s, %s);'
    cursor = conn.cursor()
    cursor.execute(sql, (username, password))
    return bool(cursor.fetchone()[0])

def add_user(name, username, password):
    cursor = conn.cursor()
    
    cursor.callproc('sp_add_user', args=(username, password))
    conn.commit()
    cursor.callproc('add_to_user', args=(name, username))
    conn.commit()
    return username

def login():
    username = input("Enter username: ")
    valid_username = check_username(username)
    if valid_username == True:
        # initiate password authentication & continue 
        password = input("Enter password: ")
        if authenticate_login(username, password): # authenticated 
            return username
        print("Incorrect login")
        quit_ui()
    else:
        # prompt to create new account
        create_new_acc = input("Would you like to create an account? [Y/N]\n")
        if create_new_acc.upper() == 'Y':
            name = input('What is your name (first and last)?\n')

            if len(username) > 20:
                username = input('Username is too long. Must be 20 characters or less.\n')
                return login()
    
            new_password = input("What would you like your password to be?\n")
            while len(new_password) > 20:
                new_password = input('Password is too long. Must be 20 characters or less:\n')
            add_user(name, username, new_password)
            return username
            
        elif create_new_acc.upper() == 'N':
            print('Have a nice day!')
            quit_ui()
        else:
            print('Sorry, this is not a valid response :( Please try again.')
            login()
        # if yes: add to user_info and login 
        # if no: quit

# ----------------------------------------------------------------------
# Functions for Command-Line Options/Query Execution
# ----------------------------------------------------------------------

def show_all_clothes():
    """
    Shows a list of all the clothing in the database. Includes all clothes
    from every personal, collaborative, and store closet.
    """
    print('This is all the clothing items in the personal, collaborative,\
          and store closets:\n')
    sql = 'SELECT * FROM clothes;'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','clothing_type','size','gender',\
                                     'color','brand','description','image_url',\
                                     'aesthetic','store_name'])
    print(df)

def show_personal_clothes(user_id):
    """
    Shows a list of all the clothing in the user's personal closet.
    """
    print('This is all the clothing items in your personal closet:\n')
    sql = """SELECT clothing_id, clothing_type, size, gender, color, brand,
           description, image_url, aesthetic, clean, shared, num_wears
           FROM clothes NATURAL JOIN personal_closet 
           WHERE user_id = """ + user_id + ';'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','clothing_type','size','gender',\
                                     'color','brand','description','image_url',\
                                     'aesthetic','clean', 'shared', 'num_wears'])
    print(df)

def borrow_from_collab_closet(user_id):
    """
    Lets a user borrow a clothing item from the collaborative closet
    if they are not the original owner and it is not currently being 
    borrowed by someone else.
    """
    clothing_id = input("What is the clothing ID of the item you \
                        would like to borrow?\n")
    sql = 'CALL borrow_item(' + user_id + ', ' + clothing_id + ');'
    cursor = conn.cursor()
    cursor.execute(sql)
    if bool(cursor.fetchone()[0]) == 1:
        print('Item successfully borrowed!')
    else:
        print('Sorry, you cannot borrow this item :(')

def show_collaborative_clothes():
    """
    Shows a list of all the clothing in the collaborative closet.
    """
    print('This is all the clothing items you can borrow from the colaborative closet:\n')
    sql = """SELECT user_id, clothing_id, clothing_type, size, gender, color, brand,
           description, image_url, aesthetic, curr_condition, is_available, curr_borrower
           FROM collab_closet NATURAL JOIN clothes;"""
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['user_id','clothing_id','clothing_type','size','gender',\
                                     'color','brand','description','image_url','aesthetic',
                                     'curr_condition','is_available','curr_borrower'])
    print(df)

def show_user_in_collab(user_id):
    """
    Shows all the clothing a specific user is loaning in the collaborative closet.
    """
    print('This is all the clothing items ' + user_id + ' has in the colaborative closet:\n')
    sql = """SELECT clothing_id, clothing_type, size, gender, color, brand, description,
           image_url, aesthetic, curr_condition, is_available, curr_borrower
           FROM collab_closet NATURAL JOIN clothes 
           WHERE user_id = """ + user_id + ';'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','clothing_type','size','gender',\
                                     'color','brand','description','image_url','aesthetic',
                                     'curr_condition','is_available','curr_borrower'])
    print(df)

def show_store_inventory(store_name):
    """
    Shows a list of all the clothing in the given store's inventory.
    """
    print('This is all the clothing items currently being sold at' + store_name + ':\n')
    sql = """SELECT clothing_id, price, discount, clothing_type, size, 
           color, brand, description, image_url, aesthetic 
           FROM store_closet NATURAL JOIN clothes
           WHERE store_name = """ + store_name + ';'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','price', 'discount','clothing_type',\
                                     'size','gender','color','brand','description',\
                                     'image_url','aesthetic'])
    print(df)

def filter_store_by_price(store_name, min_price, max_price):
    """
    Shows a list of all the clothing being sold in the provided price range
    in a given store.
    """
    print('This is all the clothing items currently being sold at' + store_name + \
          'for under $' + max_price + ':\n')
    sql = """SELECT clothing_id, price, discount, clothing_type, size, color, brand, 
           description, image_url, aesthetic 
           FROM store_closet NATURAL JOIN clothes
           WHERE store_name = """ + store_name + ' AND price <= ' + max_price + \
           'AND price >=' + min_price + 'ORDER BY price;'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','price', 'discount','clothing_type',\
                                     'size','gender','color','brand','description',\
                                     'image_url','aesthetic'])
    print(df)

def filter_store_by_type(store_name, clothing_type):
    """
    Shows a list of all the clothing of a certain type (sweatshirt, dress, etc.)
    in a given store.
    """
    print('This is all the clothing items of the type (' + clothing_type + \
          ') currently being sold at' + store_name + ':\n')
    sql = """SELECT clothing_id, price, discount, clothing_type, size, color, brand, 
           description, image_url, aesthetic 
           FROM store_closet NATURAL JOIN clothes
           WHERE clothing_type = """ + clothing_type + ';'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','price', 'discount','clothing_type',\
                                     'size','gender','color','brand','description',\
                                     'image_url','aesthetic'])
    print(df)

def filter_store_by_discount(store_name, min_discount, max_discount):
    """
    Shows a list of all the clothing items being solid within a given discount
    range in a given store.
    """
    print('This is all the clothing items currently being sold in the \
           designated discount range at ' + store_name + ':\n')
    sql = """SELECT clothing_id, price, discount, clothing_type, size, color, brand, 
           description, image_url, aesthetic 
           FROM store_closet NATURAL JOIN clothes
           WHERE discount >= """ + min_discount + 'AND discount <= ' + max_discount \
            + 'ORDER BY discount;'
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['clothing_id','price', 'discount','clothing_type',\
                                     'size','gender','color','brand','description',\
                                     'image_url','aesthetic'])
    print(df)               

# ----------------------------------------------------------------------
# Command-Line Functionality
# ----------------------------------------------------------------------

def show_options(username):
    print('Admin options: ')
    print('    (a) show all clothes')
    print('  (q) - quit')

    while True: 
        action = input('Enter an option: ')[0].lower()
        if action == 'a':
            show_all_clothes()
        else:
            quit_ui()

def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    print('Good bye!')
    conn.close()
    exit()

def main():
    """
    Main function for starting things up.
    """

    username = login()
    show_options(username)

if __name__ == '__main__':
    conn = get_conn()
    main()
