#-----------------------------------
# @author JULIO HERRERA RUIZ
# Prueba de desarrollo previa a entrevista con Roams Palencia
#----------------------------------

from flask import Flask, request, jsonify # Importa Flask y herramientas para manejar peticiones y respuestas JSON
from flask_sqlalchemy import SQLAlchemy  # Importa SQLAlchemy para manejar la base de datos
from flasgger import Swagger # Importa Swagger para documentar automáticamente la API con una interfaz interactiva
from marshmallow import Schema, fields, ValidationError #Importa clases para definir esquemas de validación de datos y para capturar errores de validación
from werkzeug.exceptions import BadRequest # Importa la excepción BadRequest para manejar errores cuando se envía un JSON mal formado o inválido
import re # Importa expresiones regulares para validar el formato del DNI

app = Flask(__name__) # Inicializa la aplicación Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db' # Configura la URI de la base de datos SQLite
db = SQLAlchemy(app) # Inicializa SQLAlchemy con la app de Flask

Swagger(app)

# Modelo de datos para representar a un cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(9), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    capital = db.Column(db.Float, nullable=False)

# Esquema de validación para los datos enviados en la simulación de hipoteca
class SimulacionSchema(Schema):
    capital = fields.Float(required=True, validate=lambda x: x > 0)
    tasa = fields.Float(required=True, validate=lambda x: x >= 0)
    plazo = fields.Int(required=True, validate=lambda x: x > 0)

# Esquema de validación para los datos de un cliente (al crear o modificar)
class ClienteSchema(Schema):
    nombre = fields.Str(required=True, validate=lambda x: len(x) > 0)
    dni = fields.Str(required=True, validate=lambda x: len(x) > 0)
    email = fields.Str(required=True, validate=lambda x: len(x) > 0)
    capital = fields.Float(required=True, validate=lambda x: x > 0)

# Maneja errores cuando el cliente envía un JSON mal formado (sintaxis incorrecta)
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": "JSON mal formado", "message": str(e)}), 400

# Maneja errores de validación de datos usando marshmallow (campos faltantes o incorrectos)
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": "Datos inválidos", "mensajes": e.messages}), 400

# Maneja errores internos inesperados del servidor (status 500)
@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({"error": "Error interno del servidor"}), 500

# Validación del DNI
def validar_dni(dni):
    patron = r'^\d{8}[A-HJ-NP-TV-Z]$'# Regex para validar el formato del DNI español
    if re.match(patron, dni):
        return True
    return False

#Ejemplo en Powershell:
#   curl.exe -X POST http://127.0.0.1:5000/clientes `                                                                                                   
#>>   -H "Content-Type: application/json" `
#>>   -d '{\"nombre\": \"Juan\", \"dni\": \"12345678Z\", \"email\": \"juan@example.com\", \"capital\": 200000.0}'
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
              example: "María Pérez"
            dni:
              type: string
              example: "12345678Z"
            email:
              type: string
              example: "maria.perez@example.com"
            capital:
              type: number
              example: 150000.0
    responses:
      201:
        description: Cliente creado exitosamente
      400:
        description: DNI inválido
    """
    data = request.get_json() # Obtiene los datos en formato JSON del cuerpo de la solicitud
    
    cliente_data = ClienteSchema().load(data) # Si algo falla, se capturará el ValidationError automáticamente y lo manejará con el handler global
    
    if not validar_dni(data['dni']):
        return jsonify({'error': 'DNI inválido'}), 400 # Devuelve error si el DNI no es válido
    
    # Verificar si el cliente con el mismo DNI ya existe
    cliente_existente = Cliente.query.filter_by(dni=cliente_data['dni']).first()
    if cliente_existente:
        return jsonify({'error': 'El cliente con ese DNI ya existe'}), 409  # Código de estado 409 para conflicto

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

#Ejemplo en Powershell:
#   curl.exe http://127.0.0.1:5000/clientes/12345678Z
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
        example: "12345678Z"
    responses:
      200:
        description: Datos del cliente
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "María Pérez"
            dni:
              type: string
              example: "12345678Z"
            email:
              type: string
              example: "maria.perez@example.com"
            capital:
              type: number
              example: 150000.0
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

#Ejemplo en Powershell:
#   curl.exe -X POST http://127.0.0.1:5000/simulacion `
#>> -H "Content-Type: application/json" `
#>> -d '{\"capital\": 100000, \"tasa\": 3.5, \"plazo\": 30}'
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
    data = SimulacionSchema().load(request.get_json()) # Si algo falla, se capturará el ValidationError automáticamente y lo manejará con el handler global
    
    capital = data['capital'] # Capital solicitado
    tasa = data['tasa'] / 100 / 12  # TAE (interés anual) convertido a interés mensual
    plazo = data['plazo'] * 12  # Plazo en años convertido a meses

    # Prevenir división por cero si la tasa es 0
    if tasa == 0:
        cuota = capital / plazo  # Si no hay interés, simplemente se divide el capital entre el plazo
    else:
        # Fórmula para calcular la cuota mensual con interés (sistema francés)
        cuota = capital * tasa / (1 - (1 + tasa) ** (-plazo))

    return jsonify({'cuota_mensual': cuota}) # Devuelve la cuota mensual

#Ejemplo en Powershell:
#   curl.exe -X PUT http://127.0.0.1:5000/clientes/12345678Z 
# -H "Content-Type: application/json" 
# -d '{\"nombre\": \"Juan Pérez\", \"email\": \"juan.perez@example.com\", \"capital\": 250000.0}'
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
        example: "12345678Z"
      - in: body
        name: body
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "María Pérez Actualizada"
            email:
              type: string
              example: "nuevocorreo@example.com"
            capital:
              type: number
              example: 200000.0
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

#Ejemplo en Powershell:
#   curl.exe -X DELETE http://127.0.0.1:5000/clientes/12345678Z
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
        example: "12345678Z"
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
    with app.app_context():  # Asegura que Flask sepa cuál es la app activa
        db.create_all()      # Crea las tablas si no existen
    app.run(debug=True)
