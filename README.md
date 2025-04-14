# 🚀 Mastering REST APIs with FastAPI

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.2-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Project from the "Mastering REST APIs with FastAPI" course by Packt, edited by David Toscano.

## 📋 Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Useful Commands](#useful-commands)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Requirements

- Python 3.11
- Redis (for background tasks)
- Docker and Docker Compose (optional)

## 💻 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Mastering-REST-APIs-with-FastAPI.git
   cd Mastering-REST-APIs-with-FastAPI
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

   ```bash
   # Alternative with Conda
   conda create --name fastapi python=3.11
   conda activate fastapi
   conda install --file requirements.txt
   conda install --file requirements-dev.txt
   ```

3. Start the server:
   ```bash
   uvicorn storeapi.main:app --reload
   ```

## 🛠️ Useful Commands

### 🧹 Code Cleaning and Formatting

```bash
# Ruff linter and automatic formatting
ruff check --select I --fix .
ruff format .

# Black formatting
black .

# Isort import sorting
isort .
```

### 🚀 Server Execution

```bash
uvicorn storeapi.main:app --reload
```

### 🔄 Redis Management

#### Windows (using Docker)

```bash
# Start Redis server
docker-compose up -d

# Check running containers
docker ps

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove containers and network
docker-compose down
```

#### Linux

```bash
# Start Redis server
sudo service redis-server start

# Check status
redis-cli ping
sudo service redis-server status

# Restart server
sudo service redis-server restart

# Stop server
sudo service redis-server stop
```

### 🔄 Celery for Background Tasks

```bash
celery -A storeapi.celery_app worker --pool=solo --loglevel=INFO
```

## 📂 Project Structure

```
storeapi/
├── database/     # Database configuration and models
├── models/       # Pydantic models for data validation
├── routers/      # API endpoints
├── security/     # Authentication and authorization
├── tasks/        # Background tasks with Celery
└── main.py       # Application entry point
```

## 📚 Documentation

The API documentation is available at the following routes once you start the server:

- 📝 **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📘 **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Documentation is also available in the project's `docs/` directory.

- 📄 **Project documentation in HTML**: [docs/build/html/index.html](docs/build/html/index.html)
- 📄 **Project documentation in PDF**: [docs/build/latex/StoreAPI.pdf](docs/build/latex/StoreAPI.pdf)

## 🤝 Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add an amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the terms of the MIT license. See the `LICENSE` file for more details.