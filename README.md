# 📊 NUAM - Sistema Automático de Calificaciones Tributarias

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-Robust_Web_Framework-092E20?style=flat-square&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_Database-316192?style=flat-square&logo=postgresql)
![Render](https://img.shields.io/badge/Render-Cloud_Deployment-000000?style=flat-square&logo=render)
![Status](https://img.shields.io/badge/Status-Producción-success?style=flat-square)

## 📑 Descripción del Proyecto

**NUAM** es una plataforma web (SaaS) diseñada para optimizar, centralizar y automatizar el mantenedor de calificaciones tributarias. Desarrollada bajo el patrón arquitectónico **MTV (Model-Template-View)** de Django, la aplicación elimina la carga operativa manual mediante el procesamiento dinámico de factores y cálculos en tiempo real. 

El sistema está preparado para entornos de alta disponibilidad, implementando un pipeline de despliegue continuo (CI/CD) en la nube a través de Render, garantizando escalabilidad, seguridad en la gestión de sesiones y persistencia de datos relacionales.

---

## 🚀 Características Principales

* **⚙️ Motor de Cálculo Automatizado:** Algoritmos internos para la validación de perfiles tributarios, carga por factor y cálculos matemáticos sin intervención manual.
* **☁️ Arquitectura Cloud-Native:** Despliegue en plataforma PaaS (Render) utilizando `Gunicorn` como servidor WSGI de producción y `Whitenoise` para el empaquetado ultra-rápido de archivos estáticos.
* **🛡️ Seguridad Estricta:** Implementación de tokens CSRF en todos los formularios, sanitización de datos de entrada, validación de sesiones y protección de credenciales mediante variables de entorno (`.env`).
* **🗄️ Gestión de Bases de Datos Híbrida:** Configuración dual que utiliza MariaDB/MySQL para entornos de desarrollo iterativo local, y PostgreSQL para el entorno transaccional de producción.
* **💻 Interfaz Administrativa:** Panel de control integrado para operaciones CRUD (Crear, Leer, Actualizar, Borrar) sobre los mantenedores del sistema.

---

## 🛠️ Stack Tecnológico

### Backend & Core
* **Lenguaje:** Python 3
* **Framework:** Django 5.x
* **Servidor de Aplicaciones:** Gunicorn

### Base de Datos & ORM
* **Producción:** PostgreSQL
* **Desarrollo:** MariaDB / MySQL
* **Conector Cloud:** `dj-database-url`, `psycopg2-binary`

### Frontend & UI
* **Estructura:** HTML5, CSS3
* **Motor de Plantillas:** Django Templates

### Infraestructura & DevOps
* **Control de Versiones:** Git & GitHub
* **Hosting PaaS:** Render
* **Gestión de Estáticos:** Whitenoise

---

## ⚙️ Instrucciones de Despliegue Local

Para levantar este proyecto en un entorno de desarrollo, sigue estos pasos:

**1. Clonar el repositorio**
bash
git clone [https://github.com/Polvo1Magico0/NUAM.git](https://github.com/Polvo1Magico0/NUAM.git)
cd NUAM

2. Crear y activar el entorno virtual aislando dependencias

python -m venv venv
# En sistemas Windows:
venv\Scripts\activate
# En sistemas Unix/macOS:
source venv/bin/activate

3. Instalar requerimientos del sistema

pip install -r requirements.txt

4. Ejecutar migraciones de la base de datos local

python manage.py migrate

5. Compilar archivos estáticos y levantar el servidor

python manage.py collectstatic --no-input
python manage.py runserver

El sistema estará disponible en http://localhost:8000.

| Nombre | Rol Principal | Responsabilidades |
| :--- | :--- | :--- |
| **Cristóbal Lucero Cavieres** | *Cloud Engineer & Backend* | Arquitectura Cloud (Render), Configuración WSGI/Static, Gestión de BD, Lógica de Modelos. |
| **Renato Díaz López** | *Backend Developer & Logic* | Implementación de carga por factores, algoritmos de cálculo, vistas (Views) y validaciones. |
| **Cristian Reyes Arratia** | *QA & Documentation* | Pruebas estructurales del sistema, documentación técnica y testing de flujos de usuario. |
