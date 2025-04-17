# api-simulacion-hipoteca
API RESTful en Flask para gestionar clientes y simular hipotecas, con documentación Swagger incluida

## 🚀 Tecnologías usadas

- Python 3
- Flask
- SQLAlchemy
- Swagger (via Flasgger)

## 📦 Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/api-clientes-flask.git
cd api-clientes-flask
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## ▶️ Ejecución

```bash
python app.py
```

La API estará disponible en:  
`http://localhost:5000`

La documentación Swagger en:  
📄 `http://localhost:5000/apidocs`

## 🧪 Endpoints disponibles

- `POST /clientes` – Crear cliente  
- `GET /clientes/<dni>` – Consultar cliente  
- `PUT /clientes/<dni>` – Modificar cliente  
- `DELETE /clientes/<dni>` – Eliminar cliente  
- `POST /simulacion` – Simular hipoteca
