#-----------------------------------
# @author JULIO HERRERA RUIZ
# Prueba de desarrollo previa a entrevista con Roams Palencia
# TODO Valores negativos o no numéricos en capital, plazo, tasa
# TODO Campos vacíos o faltantes
# TODO No hay verificación previa de si el cliente con ese dni ya existe antes de crearlo
# TODO Si alguien manda un JSON mal formado, el servidor puede lanzar una excepción.
#       ✔️ Solución: Agregar un try/except o manejar errores con @app.errorhandler
# TODO Agregar ejemplos (example:) en todos los campos ayuda mucho al usar Swagger UI.
# TODO Prevenir division by zero En la fórmula de simulación de hipoteca no se controla si tasa == 0.
#----------------------------------

from flask import Flask, request, jsonify # Importa Flask y herramientas para manejar peticiones y respuestas JSON
from flask_sqlalchemy import SQLAlchemy  # Importa SQLAlchemy para manejar la base de datos
from flasgger import Swagger # Importa Swagger para documentar automáticamente la API con una interfaz interactiva
import re # Importa expresiones regulares para validar el formato del DNI

app = Flask(__name__) # Inicializa la aplicación Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db' # Configura la URI de la base de datos SQLite
db = SQLAlchemy(app) # Inicializa SQLAlchemy con la app de Flask

# Modelo de datos para representar a un cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(9), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    capital = db.Column(db.Float, nullable=False)

# Validación del DNI
def validar_dni(dni):
    patron = r'^\d{8}[A-HJ-NP-TV-Z]$'# Regex para validar el formato del DNI español
    if re.match(patron, dni):
        return True
    return False

@app.route('/clientes', methods=['POST']) # Endpoint para crear un nuevo cliente
def crear_cliente():
    """
    Crear un nuevo cliente
    ---
    tags:
      - Clientes
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - dni
            - email
            - capital
          properties:
            nombre:
              type: string
            dni:
              type: string
            email:
              type: string
            capital:
              type: number
    responses:
      201:
        description: Cliente creado exitosamente
      400:
        description: DNI inválido
    """
    data = request.get_json() # Obtiene los datos en formato JSON del cuerpo de la solicitud
    if not validar_dni(data['dni']):
        return jsonify({'error': 'DNI inválido'}), 400 # Devuelve error si el DNI no es válido

    # Crea un nuevo cliente con los datos recibidos
    nuevo_cliente = Cliente(
        nombre=data['nombre'],
        dni=data['dni'],
        email=data['email'],
        capital=data['capital']
    )
    # Guarda el cliente en la base de datos
    db.session.add(nuevo_cliente)
    db.session.commit()
    return jsonify({'message': 'Cliente creado exitosamente'}), 201

@app.route('/clientes/<dni>', methods=['GET']) # Endpoint para consultar los datos de un cliente por su DNI
def consultar_cliente(dni):
    """
    Consultar cliente por DNI
    ---
    tags:
      - Clientes
    parameters:
      - name: dni
        in: path
        required: true
        type: string
    responses:
      200:
        description: Datos del cliente
        schema:
          type: object
          properties:
            nombre:
              type: string
            dni:
              type: string
            email:
              type: string
            capital:
              type: number
      404:
        description: Cliente no encontrado
    """
    cliente = Cliente.query.filter_by(dni=dni).first() # Busca el cliente por su DNI
    if cliente is None:
        return jsonify({'error': 'Cliente no encontrado'}), 404 # Error si no existe
    # Devuelve los datos del cliente en formato JSON
    return jsonify({
        'nombre': cliente.nombre,
        'dni': cliente.dni,
        'email': cliente.email,
        'capital': cliente.capital
    })

@app.route('/simulacion', methods=['POST'])# Endpoint para simular una hipoteca mensual
def simulacion_hipoteca():
    """
    Simulación de hipoteca
    ---
    tags:
      - Simulación
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - capital
            - tase
            - plazo
          properties:
            capital:
              type: number
              example: 100000
            tase:
              type: number
              example: 3.5
            plazo:
              type: number
              example: 30
    responses:
      200:
        description: Cuota mensual calculada
        schema:
          type: object
          properties:
            cuota_mensual:
              type: number
              example: 449.04
    """
    data = request.get_json()
    capital = data['capital'] # Capital solicitado
    tase = data['tase'] / 100 / 12  # TAE (interés anual) convertido a interés mensual
    plazo = data['plazo'] * 12  # Plazo en años convertido a meses

    # Fórmula para calcular la cuota mensual de un préstamo (sistema francés)
    cuota = capital * tase / (1 - (1 + tase) ** (-plazo))

    return jsonify({'cuota_mensual': cuota}) # Devuelve la cuota mensual

@app.route('/clientes/<dni>', methods=['PUT']) # Endpoint para modificar los datos de un cliente
def modificar_cliente(dni):
    """
    Modificar datos de un cliente
    ---
    tags:
      - Clientes
    parameters:
      - name: dni
        in: path
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            nombre:
              type: string
            email:
              type: string
            capital:
              type: number
    responses:
      200:
        description: Cliente actualizado exitosamente
      404:
        description: Cliente no encontrado
    """
    cliente = Cliente.query.filter_by(dni=dni).first() # Busca el cliente
    if cliente is None:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    data = request.get_json()
    # Actualiza solo los campos proporcionados (si no vienen, mantiene los actuales)
    cliente.nombre = data.get('nombre', cliente.nombre)
    cliente.email = data.get('email', cliente.email)
    cliente.capital = data.get('capital', cliente.capital)

    db.session.commit()# Guarda los cambios
    return jsonify({'message': 'Cliente actualizado exitosamente'})

@app.route('/clientes/<dni>', methods=['DELETE']) # Endpoint para eliminar un cliente
def eliminar_cliente(dni):
    """
    Eliminar cliente
    ---
    tags:
      - Clientes
    parameters:
      - name: dni
        in: path
        required: true
        type: string
    responses:
      200:
        description: Cliente eliminado exitosamente
      404:
        description: Cliente no encontrado
    """
    cliente = Cliente.query.filter_by(dni=dni).first() # Busca el cliente
    if cliente is None:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    db.session.delete(cliente) # Elimina el cliente
    db.session.commit()
    return jsonify({'message': 'Cliente eliminado exitosamente'})

# Punto de entrada principal de la aplicación
if __name__ == '__main__':
    db.create_all()  # Crear las tablas si no existen
    app.run(debug=True)