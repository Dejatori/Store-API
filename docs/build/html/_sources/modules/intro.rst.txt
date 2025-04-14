Introduction
============

Store API is an application that allows users to create posts, upload images, register and authenticate users, and more.

Project Architecture
--------------------

The Store API is built with FastAPI and follows a modular architecture:

* **Routers**: Handle HTTP requests and responses
* **Models**: Define data structures
* **Database**: Manages database connections and operations
* **Security**: Handles authentication and authorization
* **Tasks**: Manages background tasks with Celery

Architecture Diagram
--------------------
.. only:: html

   .. mermaid::

      flowchart TD
      Client[Client Applications] <--> API[FastAPI Application]

      subgraph "FastAPI Components"
         API --> Routers[Routers]
         API --> Security[Security & Auth]
         API --> Config[Configuration]

         Routers --> Models[Data Models]
         Routers --> DB[Database]

         Security --> JWT[JWT Auth]
         Security --> DB
      end

      subgraph "Background Processing"
         API --> Tasks[Tasks API]
         Tasks --> Celery[Celery Worker]
         Celery --> Email[Email Service]
         Celery --> Storage[B2 Storage]
      end

      subgraph "Data Layer"
         DB --> SQLite[(SQLite Database)]
      end

      class Client,API,Routers,Security,Config,Models,DB,JWT,Tasks,Celery,Email,Storage,SQLite nodeStyle

      classDef nodeStyle fill:#f9f9f9,stroke:#333,stroke-width:1px

.. only:: latex

   .. image:: /_static/images/architecture-diagram.png
      :alt: Architecture Diagram
      :width: 100%
      :align: center