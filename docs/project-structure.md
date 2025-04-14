# Store API project structure

```plaintext
project/
├── docs/
│   ├── Makefile
│   └── source/
│       ├── conf.py
│       ├── index.rst
│       ├── _static/
│       ├── _templates/
│       └── modules/
│           ├── intro.rst
├── storapi/
│   ├── libs/
│   │   └── b2/
│   │       └── __init__.py
│   ├── models/
│   │   ├── post.py
│   │   └── user.py
│   ├── routers/
│   │   ├── post.py
│   │   ├── upload.py
│   │   └── user.py
│   ├── tests/
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── test_post.py
│   │   │   ├── test_upload.py
│   │   │   └── test_user.py
│   │   ├── __init__.py 
│   │   ├── conftest.py
│   │   ├── test_security.py
│   │   └── test_tasks.py
│   ├── __init__.py
│   ├── celery_app.py
│   ├── config.py
│   ├── database.py
│   ├── logging_conf.py
│   ├── main.py
│   ├── security.py
│   └── tasks.py
├── .env
├── .env.example
├── .gitignore
├── .pylintrc
├── .python-version
├── docker-compose.yml
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
└── requirements-dev.txt
```