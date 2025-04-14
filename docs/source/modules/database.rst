Database
========

This module defines database models, tables, and connection configuration.
It includes tables for users, posts, comments, and likes with their relationships.

Database Diagram
----------------

.. only:: html

   .. mermaid::

      erDiagram
          USERS ||--o{ POSTS : create
          USERS ||--o{ COMMENTS : write
          USERS ||--o{ LIKES : give
          POSTS ||--o{ COMMENTS : has
          POSTS ||--o{ LIKES : receive
    
          USERS {
              int id PK
              string email
              string password
              boolean confirmed
          }
          POSTS {
              int id PK
              string body
              int user_id FK
              string image_url
          }
          COMMENTS {
              int id PK
              string body
              int post_id FK
              int user_id FK
          }
          LIKES {
              int id PK
              int post_id FK
              int user_id FK
          }

.. only:: latex

   .. image:: /_static/images/database-diagram.png
      :width: 100%
      :align: center
      :alt: Database ER Diagram

API Documentation
-----------------

.. automodule:: storeapi.database
   :members:
   :undoc-members:
   :show-inheritance: