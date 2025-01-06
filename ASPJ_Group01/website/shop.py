import shelve
import os
import io
import logging
from logging.handlers import RotatingFileHandler
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, g, make_response
from .Product import Product, Cart
from .Forms import ProductForm
from flask_login import current_user
from cryptography.fernet import Fernet
from . import db
import base64
import pymysql
import json
from .models import Product

shop = Blueprint('shop', __name__)

UPLOAD_FOLDERS = os.path.abspath('website/static/uploads/products')
DECRYPTED_FOLDER = os.path.abspath('website/static/uploads/decrypted_images')
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
ALLOWED_FILESIZE = (2 * 1024 * 1024)
os.makedirs(UPLOAD_FOLDERS, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)

key_directory = 'website/secret_key'
os.makedirs(key_directory, exist_ok=True)
key_path = os.path.join(key_directory, 'key')

# Load or generate encryption key
if os.path.exists(key_path):
    with open(key_path, 'rb') as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(key_path, 'wb') as key_file:
        key_file.write(key)

cipher_suite = Fernet(key)


@shop.context_processor
def inject_user():
    return dict(user=current_user)


log_file = 'website/logs.log'
file_handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


# cookie encryption
def encrypt_cart_data(cart_data):
    cart_json = json.dumps(cart_data).encode('utf-8')
    encrypted_data = cipher_suite.encrypt(cart_json)
    # Encode the encrypted data into base64 to ensure it's safe for cookies
    return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')


def decrypt_cart_data(encrypted_data):
    """Decrypt cart data using Fernet symmetric encryption."""
    try:
        # Decode from base64
        encrypted_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        # Decrypt using the cipher suite
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        # Convert back to dictionary
        return json.loads(decrypted_data)
    except Exception as e:
        print(f"Decryption error: {e}")
        return {}


@shop.teardown_request
def logging(exception=None):
    log_message = f"Request: {request.method} {request.path}"
    logger.info(log_message)


@shop.route('/shopNow')
def list_product():
    try:
        with g.mydb.cursor(pymysql.cursors.DictCursor) as my_cursor:
            sql1 = "SELECT product_id, product_name, product_desc, product_cat, product_price FROM products"
            my_cursor.execute(sql1)
            products = my_cursor.fetchall()
            print("Fetched products:", products)  # Debugging: Print the fetched products
            if my_cursor:
                my_cursor.close()
            return render_template('shopNow.html', products=products, user=current_user, csrf_token=g.csrf_token)
    except Exception as e:
        flash("Error retrieving products. Please try again later.", category='error')
        return render_template('shopNow.html', products=[], csrf_token=g.csrf_token)


def allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def encrypt_image(image_path: str, key: bytes) -> bytes:
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(image_data)
        return encrypted_data
    except Exception as e:
        flash(f'Error encrypting image: {str(e)}', category='error')


def decrypt_image(encrypted_data: bytes, key: bytes) -> bytes:
    try:
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        flash(f'Error decrypting image: {str(e)}', category='error')


@shop.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if current_user.is_authenticated and current_user.user_type == 'staff':
        form = ProductForm(request.form)
        if request.method == 'POST' and form.validate():
            try:
                product_name = form.product_name.data
                product_desc = form.product_desc.data
                product_cat = form.product_cat.data
                product_price = form.product_price.data
                f = request.files[form.product_image.name]

                # Ensure the file is allowed
                if not allowed_file(f.filename):
                    flash("Please upload file in .png, .jpg, or .jpeg format", category='error')
                    return render_template('addProduct.html', form=form)

                # Save the product information
                try:
                    my_cursor = g.mydb.cursor()
                    sql1 = ("INSERT INTO products (product_name, product_desc, product_cat, product_price) "
                            "VALUES (%s, %s, %s, %s)")
                    values = (product_name, product_desc, product_cat, product_price)
                    my_cursor.execute(sql1, values)
                    product_id = my_cursor.lastrowid  # Get the ID of the newly created product
                    g.mydb.commit()

                    # Save the image file
                    original_extension = os.path.splitext(f.filename)[1].lower()
                    filename = str(product_id) + original_extension
                    file_path = os.path.join(UPLOAD_FOLDERS, filename)
                    f.save(file_path)

                    # Check file size
                    file_size = os.path.getsize(file_path)
                    print(f'File Size in Bytes is {file_size}')
                    filesize_mb = file_size / (1024 * 1024)
                    print(f'File Size in MegaBytes is {filesize_mb}')
                    if filesize_mb > ALLOWED_FILESIZE:
                        flash("Please upload images less than 2MB.", category='error')
                        return render_template('addProduct.html', form=form)

                    # Encrypt the image
                    encrypted_data = encrypt_image(file_path, key)
                    encrypted_path = file_path + '.enc'
                    with open(encrypted_path, 'wb') as enc_file:
                        enc_file.write(encrypted_data)

                    os.remove(file_path)  # Remove the original file

                    flash('Product created!', category='success')
                    return redirect(url_for('shop.list_product'))

                except Exception as e:
                    g.mydb.rollback()
                    flash('Error creating product', category='error')

            except Exception as e:
                flash('Error in processing the product', category='error')
        return render_template('addProduct.html', form=form, csrf_token=g.csrf_token)
    else:
        return redirect(url_for('shop.list_product'))


@shop.route('/get-image/<filename>', methods=['GET', 'POST'])
def get_image(filename):
    # Handle .jpg, .png, and .jpeg extensions
    possible_extensions = ['.jpg', '.jpeg', '.png']
    encrypted_path = None
    for ext in possible_extensions:
        potential_path = os.path.join(UPLOAD_FOLDERS, filename + ext + '.enc')  # checking for img type
        if os.path.exists(potential_path):
            encrypted_path = potential_path
            break

    if not encrypted_path:
        flash(f'Encrypted file for {filename} not found.', category='error')
        return redirect(url_for('shop.list_product'))

    decrypted_path = os.path.join(DECRYPTED_FOLDER, filename + os.path.splitext(encrypted_path)[1])

    try:
        print(f"Encrypted path: {encrypted_path}")  # Print encrypted path
        print(f"Decrypted path: {decrypted_path}")  # Print decrypted path

        with open(encrypted_path, 'rb') as enc_file:
            encrypted_data = enc_file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        with open(decrypted_path, 'wb') as dec_file:
            dec_file.write(decrypted_data)
        image_io = io.BytesIO(decrypted_data)
        mimetype = 'image/jpeg' if '.jpg' in decrypted_path or '.jpeg' in decrypted_path else 'image/png'
        return send_file(image_io, mimetype=mimetype)  # return image if file type is jpeg, jpg or png
    except Exception as e:
        print(f"Error decrypting file: {str(e)}")  # if error decrypt file, return ExceptionError
        return redirect(url_for('shop.list_product'))


@shop.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    form = ProductForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            product_name = form.product_name.data
            product_desc = form.product_desc.data
            product_cat = form.product_cat.data
            product_price = form.product_price.data
            f = request.files.get(form.product_image.name)

            if not allowed_file(f.filename):
                flash('Please upload images in JPEG, PNG, or JPG format.', category='error')
                return render_template('updateProduct.html', form=form, csrf_token=g.csrf_token)

            # Execute SQL Update
            my_cursor = g.mydb.cursor(pymysql.cursors.DictCursor)
            sql1 = """
                UPDATE products
                SET product_name=%s, product_desc=%s, product_cat=%s, product_price=%s
                WHERE product_id=%s
            """
            values = (product_name, product_desc, product_cat, product_price, product_id)
            my_cursor.execute(sql1, values)
            g.mydb.commit()

            # Save the uploaded file
            filename = str(product_id) + os.path.splitext(f.filename)[1].lower()
            f.save(os.path.join(UPLOAD_FOLDERS, filename))

            flash('Product updated!', category='success')
            return redirect(url_for('shop.list_product'))

        except Exception as e:
            flash(f'Error updating product: {str(e)}', category='error')
            print(f'Exception occurred: {e}')

    else:
        my_cursor = g.mydb.cursor(pymysql.cursors.DictCursor)
        my_cursor.execute(
            "SELECT product_name, product_desc, product_cat, product_price FROM products WHERE product_id=%s",
            (product_id,))
        product = my_cursor.fetchone()
        my_cursor.close()

        if product:
            form.product_name.data = product['product_name']
            form.product_desc.data = product['product_desc']
            form.product_cat.data = product['product_cat']
            form.product_price.data = product['product_price']
            return render_template('updateProduct.html', form=form, product=product, csrf_token=g.csrf_token)
        else:
            flash('No product with matching id found', category='error')
            return redirect(url_for('shop.list_product'))

    return render_template('updateProduct.html', form=form, csrf_token=g.csrf_token)


@shop.route('/retrieve-product')
def retrieve_product():
    try:
        products = []
        with g.mydb.cursor(pymysql.cursors.DictCursor) as my_cursor:
            my_cursor.execute('SELECT product_id, product_name, product_price, product_cat FROM products')
            products = my_cursor.fetchall()
            if my_cursor:
                my_cursor.close()
    except:
        flash("Error in retrieving products from database", category='error')
    return render_template('retrieveProducts.html', products=products)


@shop.route('/delete-product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    try:
        with g.mydb.cursor() as my_cursor:
            sql = "DELETE FROM products WHERE product_id=%s"
            my_cursor.execute(sql, (product_id,))
            g.mydb.commit()
            flash("Product deleted from database", category='success')
    except Exception as e:
        flash(f'Error deleting product: {e}', category='error')
    return redirect(url_for('shop.retrieve_product'))


@shop.route('/cart')
def cart():
    cart_cookie = request.cookies.get('cart', '{}')
    try:
        # Decrypt the cart cookie
        cart = decrypt_cart_data(cart_cookie)
    except json.JSONDecodeError:
        cart = {}

    products = []
    total = 0.00

    my_cursor = g.mydb.cursor(pymysql.cursors.DictCursor)
    for product_id, quantity in cart.items():
        my_cursor.execute('SELECT * FROM products WHERE product_id = %s', (product_id,))
        product = my_cursor.fetchone()
        if product:
            product['quantity'] = quantity
            product['total'] = product['product_price'] * quantity
            products.append(product)
            total += product['total']
    my_cursor.close()

    return render_template('cart.html', products=products, total=total)


@shop.route('/add_quantity/<product_id>', methods=['GET'])
def add_quantity(product_id):
    cart_cookie = request.cookies.get('cart', '{}')
    cart = decrypt_cart_data(cart_cookie)

    cart[product_id] = cart.get(product_id, 0) + 1
    cart_cookie = encrypt_cart_data(cart)

    response = make_response(redirect(url_for('shop.cart')))
    response.set_cookie('cart', cart_cookie, max_age=60, secure=True, httponly=True, samesite='Lax')
    return response


@shop.route('/minus_quantity/<product_id>', methods=['GET'])
def minus_quantity(product_id):
    cart_cookie = request.cookies.get('cart', '{}')
    cart = decrypt_cart_data(cart_cookie)

    if cart.get(product_id, 0) > 1:
        cart[product_id] -= 1
    else:
        cart.pop(product_id, None)
    cart_cookie = encrypt_cart_data(cart)

    response = make_response(redirect(url_for('shop.cart')))
    response.set_cookie('cart', cart_cookie, max_age=60, secure=True, httponly=True, samesite='Lax')
    return response


@shop.route('/delete_from_cart/<product_id>', methods=['POST'])
def delete_from_cart(product_id):
    cart_cookie = request.cookies.get('cart', '{}')
    cart = decrypt_cart_data(cart_cookie)

    if str(product_id) in cart:
        del cart[str(product_id)]
        cart_cookie = encrypt_cart_data(cart)
        response = make_response(redirect(url_for('shop.cart')))
        response.set_cookie('cart', cart_cookie, max_age=60, secure=True, httponly=True, samesite='Lax')
        flash(f"Deleted product {product_id} from the cart", category='success')
    else:
        flash('Product not found in cart.', category='error')
        response = make_response(redirect(url_for('shop.cart')))

    return response


@shop.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart_cookie = request.cookies.get('cart', '{}')

    try:
        cart = decrypt_cart_data(cart_cookie)
        if not isinstance(cart, dict):
            cart = {}
    except (json.JSONDecodeError, TypeError):
        cart = {}

    cart[product_id] = cart.get(product_id, 0) + 1
    cart_cookie = encrypt_cart_data(cart)

    response = make_response(redirect(url_for('shop.list_product')))
    response.set_cookie('cart', cart_cookie, max_age=60, secure=True, httponly=True, samesite='Lax')

    flash("Added to cart!", category="success")
    return response


@shop.route('/clear_cart', methods=['POST'])
def clear_cart():
    response = make_response(redirect(url_for('views.home')))
    response.delete_cookie('cart')
    flash("Cart has been cleared!", category='success')
    return response


@shop.route('/payment', methods=['POST','GET'])
def payment():
    try:
        # Retrieve cart information from cookies
        cart_cookie = request.cookies.get('cart', '{}')
        # Decrypt and load the cart data
        cart = decrypt_cart_data(cart_cookie)

        # Calculate the total price of the cart
        total = 0.00
        my_cursor = g.mydb.cursor(pymysql.cursors.DictCursor)
        products = []
        for product_id, quantity in cart.items():
            my_cursor.execute('SELECT * FROM products WHERE product_id = %s', (product_id,))
            product = my_cursor.fetchone()
            if product:
                product['quantity'] = quantity
                product['total'] = product['product_price'] * quantity
                products.append(product)
                total += product['total']
        my_cursor.close()

        # Pass cart and total to the template
        return render_template('payment.html', products=products, total=total, cart=cart)
    except Exception as e:
        flash(f'Error proceeding to payment: {e}', category='error')
        return redirect(url_for('shop.cart'))


@shop.route('/paymentComplete', methods=['POST'])
def paymentComplete():
    return render_template('paymentComplete.html')
