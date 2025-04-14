# Configuration file for the Sphinx documentation builder.
import os
import sys

# Add path to storeapi
sys.path.insert(0, os.path.abspath("../../"))

html_baseurl = "/"
html_context = {"display_github": True}
latex_show_urls = 'footnote'

html_css_files = [
    'custom.css',
]

# -- Project information -----------------------------------------------------
project = "Store API"
copyright = "2025, David Toscano"
author = "David Toscano"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",    # Include documentation from docstrings
    "sphinx.ext.viewcode",   # Add links to source code
    "sphinx.ext.napoleon",   # Support for Google style docstrings
    "sphinx.ext.autosummary",    # Generate summary tables
    "sphinx.ext.intersphinx",    # Link to other projects' documentation
    "sphinx.ext.todo",           # Support for todo notes
    "sphinx_copybutton",         # Copy button for code blocks
    "myst_parser",           # Support for MyST Markdown
    "sphinxcontrib.mermaid", # Support for Mermaid diagrams
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    # LaTeX document options
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "htbp",
    'classoptions': ',openany,oneside',
    "fncychap": "\\usepackage[Bjarne]{fncychap}",
    "tableofcontents": "\\setcounter{tocdepth}{3}",
    "figure_align": "htbp",
}

autosummary_generate = True

# Document grouping for PDF
latex_documents = [
    (
        "index",            # source document
        "StoreAPI.tex",     # output filename
        "Store API Documentation",  # document title
        author,             # author
        "manual",           # document type
    ),
]