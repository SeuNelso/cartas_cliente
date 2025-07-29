from setuptools import setup, find_packages

setup(
    name="carta-automatica",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==2.3.3",
        "pandas==2.1.4",
        "openpyxl==3.1.2",
        "cairosvg==2.8.0",
        "PyPDF2==3.0.1",
        "Werkzeug==2.3.7",
        "gunicorn==21.2.0",
    ],
    python_requires=">=3.8",
) 