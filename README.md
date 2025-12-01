# Claybird

A lightweight web framework with entity modeling and repository pattern for Python.

## Features

- 🚀 FastAPI-based web framework
- 📦 Entity modeling with field validation
- 🔌 Repository pattern for data access
- 🎯 Decorator-based controllers and route mapping
- 💉 Dependency injection support
- 🗄️ MySQL adapter with async support

## Installation

```bash
pip install claybird
```

Or install from source:

```bash
git clone https://github.com/yourusername/claybird.git
cd claybird
pip install -e .
```

## Quick Start

### Define an Entity

```python
from claybird import Entity, Field, field

class User(Entity):
    id = field(type=int, primary_key=True)
    name = field(type=str, required=True)
    email = field(type=str, required=True)
    age = field(type=int, default=0)
```

### Create a Controller

```python
from claybird import Controller, GetMapping, PostMapping, Claybird

@Controller("/users")
class UserController:
    
    @GetMapping("/")
    def get_users(self):
        return {"users": []}
    
    @PostMapping("/")
    def create_user(self, user_data: dict):
        return {"message": "User created", "data": user_data}
```

### Run the Application

```python
from claybird import Claybird

# Register your controllers
# Claybird will automatically register them via decorators

Claybird.run()
```

## Usage

### Entity Definition

```python
from claybird import Entity, field

class Product(Entity):
    id = field(type=int, primary_key=True)
    name = field(type=str, required=True)
    price = field(type=float, required=True)
    description = field(type=str, default="")
```

### Repository Pattern

```python
from claybird import CrudRepositoryPort, MysqlCrudRepository
from claybird.domain import Connection
import aiomysql

# Create connection pool
async def create_pool():
    return await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='user',
        password='password',
        db='database'
    )

# Create repository
pool = await create_pool()
repository = MysqlCrudRepository[Product](pool)
```

## Project Structure

```
claybird/
├── domain/          # Domain entities and value objects
├── application/     # Application services and ports
├── infrastructure/  # Infrastructure adapters
└── decorator/       # Decorators for controllers and mappings
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- aiomysql (for MySQL adapter)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
