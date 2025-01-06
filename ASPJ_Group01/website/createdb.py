import bcrypt
import pymysql

mydb = None
my_cursor = None

try:
    mydb = pymysql.connect(
        host="localhost",
        user="root",
        passwd="Ilovec0ding_",
        )

    my_cursor = mydb.cursor()

    #Drop the database if it exists
    my_cursor.execute("DROP DATABASE IF EXISTS website")

    #Create the database
    my_cursor.execute("CREATE DATABASE website")

    my_cursor.execute("USE website")

    my_cursor.execute('''
    CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fname VARCHAR(255) NOT NULL,
    lname VARCHAR(255) NOT NULL,
    user_type ENUM('customer', 'staff') NOT NULL,
    failed_login_attempts INT DEFAULT 0 NOT NULL,
    lockout_time DATETIME DEFAULT NULL, 
    security_answer VARCHAR(255) DEFAULT NULL
    );
    ''')

    my_cursor.execute('''
    CREATE TABLE customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE);
    ''')

    my_cursor.execute('''
    CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    role ENUM('admin', 'moderator', 'employee') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE);
    ''')

    my_cursor.execute('''
        CREATE TABLE logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(255) NOT NULL,
        timestamp DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id));
    ''')

    my_cursor.execute('''
        CREATE TABLE products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(120) NOT NULL,
        product_desc VARCHAR(255) NOT NULL,
        product_cat VARCHAR(120) NOT NULL,
        product_price FLOAT(5, 2) NOT NULL );''')

    my_cursor.execute('''
    CREATE PROCEDURE create_user (
    IN p_email VARCHAR(120),
    IN p_password VARCHAR(120),
    IN p_fname VARCHAR(50),
    IN p_lname VARCHAR(50),
    IN p_user_type ENUM('customer', 'staff'),
    IN p_role ENUM('admin', 'moderator', 'employee')
)
BEGIN
    DECLARE v_user_id INT;

    -- Insert the new user
    INSERT INTO user (email, password, fname, lname, user_type)
    VALUES (p_email, p_password, p_fname, p_lname, p_user_type);
    
    SET v_user_id = LAST_INSERT_ID();
    
    -- If the user type is staff, insert into the staff table
    IF p_user_type = 'staff' THEN
        INSERT INTO staff (user_id, role)
        VALUES (v_user_id, p_role);
	ELSEIF p_user_type = 'customer' THEN
		INSERT INTO customer(user_id)
        VALUES (v_user_id);
    END IF;
END
''')

    password = 'aA123456!'
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    values1 = ('staff1@gmail.com', hashed_password, 'Staff', 'Account', 'staff', 'employee')
    values3 = ('staff2@gmail.com', hashed_password, 'Staff', 'Account', 'staff', 'employee')
    values4 = ('staff3@gmail.com', hashed_password, 'Staff', 'Account', 'staff', 'employee')
    value5 = ('staff4@gmail.com', hashed_password, 'Staff', 'Account', 'staff', 'employee')
    my_cursor.callproc('create_user', values1)
    my_cursor.callproc('create_user', values3)
    my_cursor.callproc('create_user', values4)
    my_cursor.callproc('create_user', value5)
    values2 = ('kadenng06@gmail.com', hashed_password, 'Kaden', 'Ng', 'customer', None)
    my_cursor.callproc('create_user', values2)

    mydb.commit()

    my_cursor.execute("SHOW TABLES")
    for db in my_cursor:
        print(db)

    my_cursor.execute("SHOW DATABASES")
    for db in my_cursor:
        print(db)
finally:
    if my_cursor:
        my_cursor.close()
    if mydb:
        mydb.close()