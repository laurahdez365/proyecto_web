from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializamos DB
db = SQLAlchemy()

# Creamos app Flask
def create_app():
    app = Flask(__name__)
    # Conectamos Flask con db SQLAlchemy y damos ruta
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Conexion con DB "users"
    app.config['SECRET_KEY'] = "password" # Configuracion login

# Iniciamos SQLAlchemy con Flask
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

# Login - ruta
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Tablas DB
# Tabla para crear un producto
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.Text)
    category = db.Column(db.Text)

    def __repr__(self):
        return "Product {}".format(self.title)

# Tabla para crear un usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(30))
    rol = db.Column(db.Integer)
    name = db.Column(db.String(20))
    surnames = db.Column(db.String(100))
    address = db.Column(db.String(100))

# Tabla para crear un pedido (Carrito de compras)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.Text)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float)
    amount = db.Column(db.Float)
    total = db.Column(db.Numeric)


# Productos
@app.route("/products", methods=['GET', 'POST'])
@login_required
def create_product():
    """Función que crea un Producto nuevo en la tabla product de la DB"""

    if request.method == 'POST':
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        image = request.form.get("image")
        category = request.form.get("category")


        product = Product(title=title, description=description, price=price, image=image, category=category)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("admin"))
    return render_template("create_product.html")

@app.route("/delete-product/<id>")
@login_required
def delete(id):
    """Función que elimina un producto de la tabla product de la DB, por id"""

    product = Product.query.filter_by(id=int(id)) # Buscamos producto por id
    product.delete() #eliminamos el producto
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/edit<id>", methods=["POST", "GET"])
@login_required
def edit(id):
    """Función que modifica uno o varios datos de la tabla product de la DB, por id"""

    product = db.session.query(Product).filter_by(id=int(id)).first()

    if request.method == 'POST':  # Si la respuesta es crear informacion nueva (modificar)
        new_title = request.form.get('new_title')  # creamos el objeto
        product.title = new_title
        db.session.commit()

        if request.method == 'POST':
            new_category = request.form.get('new_category')  # creamos el objeto
            product.category = new_category
            db.session.commit()

            if request.method == 'POST':
                new_description = request.form.get('new_description')  # creamos el objeto
                product.description = new_description
                db.session.commit()

                if request.method == 'POST':
                    new_price = request.form.get('new_price')  # creamos el objeto
                    product.price = new_price
                    db.session.commit()

                    if request.method == 'POST':
                        new_image = request.form.get('new_image')  # creamos el objeto
                        product.image = new_image
                        db.session.commit()

                        return redirect(url_for("admin"))  # volvemos a ejecutar admin

    return render_template("edit.html", product=product)  # redirige a la pagina editar tarea


# Usuario
@login_manager.user_loader
def load_user(user_id):
    """Función que busca un usuario por id"""

    return User.query.get(int(user_id))

@app.route("/login", methods=['GET', 'POST'])
def login():
    """Función que realiza el login de un usuario"""

    if request.method == 'POST': # Si la respuesta es crear informacion nueva (modificar)
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        # Comprobamos que el usuario existe y que la contraseña es correcta
        if user and check_password_hash(user.password, password):
            log = login_user(user)

            # Comprobamos si el usuario es administrador (Administrado = 1, usuario = 2)
            if user.rol == 1: # si el rol de usuario es igual a 1 (Administrador)
                return redirect(url_for("admin",  log=log, username=username))

            else: # si es distinto de 1, es decir, 2 (Usuario)
                return redirect(url_for("home", log=log, username=username))

        return render_template("login.html", mensaje="Usuario Incorrecto, compruebe email de usuario y contraseña")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Función que desloga un usuario"""

    logout_user()
    return redirect(url_for("home"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Función que realiza el registro de los datos de un usuario nuevo.
        El registro de los datos se realiza a traves de un formulario"""

    if request.method == 'POST': # Si la respuesta es crear informacion nueva (modificar)
        username = request.form['username']
        password = request.form['password']
        rol = request.form['rol']
        name = request.form['name']
        surnames = request.form['surnames']
        address = request.form['address']
        hashed_password = generate_password_hash(password)

        # Se crea el nuevo usuario
        new_user = User(username=username, password=hashed_password, rol=rol, name=name, surnames=surnames, address=address)
        # Se añade el usuario a la tabla user de la DB.
        db.session.add(new_user)
        # Se guardan los cambios
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# Pedido

@app.route("/add-cart<id>", methods=['GET', 'POST'])
def add_cart(id):
    """Función que añade un producto nuevo a la tabla order de la DB."""

    if request.method == 'POST': # Si la respuesta es crear informacion nueva (modificar)
        image = request.form.get("image")
        title = request.form.get("title")
        price = request.form.get("price")
        amount = request.form.get("amount")
        total = float(price)*float(amount)

        # Se crea el nuevo registro de order
        order = Order(image=image, title=title, price=price, amount=amount, total=total)
        # Se añade el registro a la tabla order de la DB.
        db.session.add(order)
        # Se guardan los cambios
        db.session.commit()
        return redirect(url_for("snacks"))
    return render_template("snacks.html")

@app.route("/delete-order/<id>")
def delete_order(id):
    """Función que elimina un registro de la tabla order de la DB."""

    # Consultamos el producto por id
    product = Order.query.filter_by(id=int(id))
    # Eliminamos el producto de la tabla order de la Db.
    product.delete()
    # Se guardan los cambios
    db.session.commit()
    return redirect(url_for("cart"))

@app.route("/delete-cart", methods=['POST'])
def delete_cart():
    """Función que ejecuta el método delete_cart_order"""

    try:
        # Ejecutamos funcion para eliminar los registros de la tabla Order de la DB
        delete_cart_order()
        return redirect(url_for("cart"))

    except Exception as e:
        # Control de errores
        return 'Error al eliminar los registros' + str(e)


def delete_cart_order(): # Función que elimina todos los productos de la tabla Order de la DB. (Del carrito)
    """Método para eliminar todos los productos de la tabla order de la DB. (Vaciariamos el carrito de la compra)"""

    try:
        # Eliminamos todos los registros de la tabla Order de la BD y guardamos cambios
        Order.query.delete()
        db.session.commit()
        print("Se ha eliminado todo")

    except Exception as e:
        # En caso de error, deshacemos los cambios
        db.session.rollback()
        print("Error al eliminar los registros")

    finally:
        # Cerramos la sesion
        db.session.close()


def total_order():
    """Método que nos indica el importe total de la columna total de la tabla order de la DB.
        Nos da el resultado total de los productos que tenemos agregados al carrito de la compra"""

    try:
        # Hacemos consulta para obtener la suma de la columna price
        total = db.session.query(db.func.sum(Order.total)).scalar()

        # Si no hay registros
        if total is None:
            total = 0
        return total

    except Exception as e:
        # Control de errores
        print("Error al realizar la suma de los importes", str(e))
        return 0

    finally:
        # Cerramos la sesion
        db.session.close()



# Rutas Web

@app.route("/")
def home():
    """Funcion que muestra el inicio de la web"""

    return render_template("home.html")

@app.route("/admin")
@login_required
def admin():
    """Funcion que muestra el inicio de la web admin.
        Se muestran todos los productos de la tabla product de la DB"""

    products = Product.query.all()
    return render_template("admin.html", products=products)

@app.route("/nosotros")
def us():
    """Funcion que muestra el html nosotros"""

    return render_template("us.html")

@app.route("/contacto")
def contact():
    """Funcion que muestra el html contacto"""

    return render_template("contact.html")

@app.route("/snacks")
def snacks():
    """Funcion que muestra todos los productos de la db de la categoria snack"""

    products = Product.query.filter_by(category="snack")
    return render_template("snacks.html", products=products)

@app.route("/lifestyle")
def lifestyle():
    """Funcion que muestra todos los productos de la db de la categoria lifestyle"""

    products = Product.query.filter_by(category="lifestyle")
    return render_template("lifestyle.html", products=products)

@app.route("/complementos-naturales")
def complements():
    """Funcion que muestra todos los productos de la db de la categoria complementos"""

    products = Product.query.filter_by(category="complementos")
    return render_template("complements.html", products=products)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    """Función que consulta todos los registros de la tabla order en la DB y muestra el importe total del pedido
        Nos muestra todos los productos del carrito de la compra y el importe total del pedido"""

    # Consultamos los registros de la tabla order de la DB y lo guardamos en una variable.
    orders = Order.query.all()
    # Ejecutamos el metodo total_order para saber el importe total del carrito de la compra
    result = total_order()
    # Redondeamos el resultado del carrito a 2 decimales
    result = round(result, 2)

    return render_template("cart.html", orders=orders, result=result)


# Aplicacion Web
if __name__ == "__main__":
    app.run(debug=True)
