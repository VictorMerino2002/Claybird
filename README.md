# Claybird

Claybird is a **lightweight REST framework for Python** designed to help you build **clean, testable, and scalable APIs** using **Hexagonal Architecture** principles — without forcing you to learn its internals.

Claybird focuses on **how you build your application**, not on hiding complexity behind magic.

---

## ✨ What Claybird Gives You

- 🚀 A ready-to-use REST application powered by **FastAPI**
- 🧩 Automatic dependency injection
- 🧱 Clear separation between controllers, use cases, and infrastructure
- 🗄️ Built-in support for database connections
- 🔌 Easy replacement of adapters (DB, logger, HTTP)
- 🧪 Test-friendly by default

You write **controllers and use cases**. Claybird handles wiring and bootstrapping.

---

## 📦 Installation

```bash
pip install claybird
```

---

## 🚀 Quick Start

This is a minimal but realistic example of how to use Claybird to build a REST API.

---

### 1️⃣ Define a controller

```python
from claybird.infrastructure.adapters.inbound.http.routing.controller import Controller
from claybird.infrastructure.adapters.inbound.http.routing.mappers import GetMapping, PostMapping
from repositories.user_repository import UserRepository
from dto.user_dto import UserDto
from models.user import User

@Controller("/users")
class UserController:

    user_repository: UserRepository

    @PostMapping("/create")
    async def create_user(self, user: UserDto):
        user = User(name=user.name)
        await self.user_repository.save(user)
        return user

    @GetMapping("/get-all")
    async def get_users(self):
        return await self.user_repository.get_all()

    @GetMapping("/get/{uuid}")
    async def get_user(self, uuid: str):
        return await self.user_repository.get(uuid)
```

Controllers are discovered automatically. Dependencies are injected using type annotations.

---

### 2️⃣ Define a domain model

```python
from claybird.domain.entities.entity import Entity
from claybird.domain.entities.field import field
from uuid import uuid4, UUID
from dataclasses import dataclass

@dataclass
class Position:
    lat: int
    lon: int

class User(Entity):
    id = field(primary_key=True, default=uuid4, type_=UUID)
    position = field(type_=Position)
    name = field()
```

Entities define your business data and rules. They are independent from HTTP and persistence.

---

### 3️⃣ Define a repository

```python
from claybird.application.proxies.crud_repository import CrudRepository
from models.user import User

class UserRepository(CrudRepository[User]):
    table_name = "users"
    connection = "mysql"
```

Claybird automatically resolves the correct database implementation.

---

### 3️⃣ Configure database connections

Create a `settings.py` file:

```python
CONNECTIONS = {
    "mysql": {
        "engine": "mysql",
        "schema": "claybird",
        "host": "127.0.0.1",
        "port": "3306",
        "user": "root",
        "password": "super"
    }
}
```

---

### 4️⃣ Run the application

```python
from claybird import Claybird
import asyncio

from controllers import user_controller  # Import controllers so they are discovered

async def main():
    app = Claybird()
    await app.run()

asyncio.run(main())
```

Your API will be available at:

```
http://127.0.0.1:8000/users
```

---

## 🧩 How It Feels to Use Claybird

- No manual wiring
- No router setup
- No dependency configuration per controller
- Controllers stay clean and readable

You focus on **what your API does**, not on how everything is connected.

---

## ✨ Final Words

Claybird helps you build REST APIs with **structure and clarity**, without sacrificing developer experience.

If you want control, explicitness, and clean boundaries — Claybird is a solid foundation.


Claybird helps you focus on **writing your application**, not fighting your framework.

If you value clean architecture and long-term maintainability, Claybird gives you a solid foundation to build on.

