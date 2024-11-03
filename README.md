VET-MANAGER 


This is a Comprehensive Management System for Agro-Veterinary shop

CONTRIBUTORS 
MOSES KIMANI WANGIGI

TABLES OF CONTENT 

Introduction
Features
Technologies Used
Installation
Usage
Project Structure
Challenges

INTRODUCTION

Vet-Manager is an all-in-one management solution designed for veterinary clinics. 
It integrates multiple critical functions like Point of Sale (POS), Stock management, and comprehensive business reporting into a single web-based application. 
This system is aimed at streamlining operations, improving clinic efficiency, and offering powerful reporting tools to enhance decision-making processes.

FEATURES 

Point of Sale (POS): Manage sales transactions, record invoices, and track payments.
HR Management: Handle employee records, track attendance, calculate payroll, and manage leave requests.
Stock Management: Monitor inventory levels, update stock in real-time, and receive low-stock alerts.
Business Reports: Generate detailed reports for sales, stock, and employee performance.
User Authentication: Role-based permissions for different levels of access (e.g., Admin, Employee).

TECHNOLOGIES USED:-

Backend: Python, Django
Frontend: JavaScript, HTML, CSS
Database: SQLlite
Version Control: Git, GitHub
API Integration: RESTful APIs 
Project Management: Trello

INSTALLATION

Clone the Repository:
bash

git clone https://github.com/key-money/vet-manager.git
cd vet-manager

Set up Virtual Environment:
bash

python3 -m venv env
source env/bin/activate  # On Windows, use `env\Scripts\activate`

Install Dependencies:
bash

pip install -r requirements.txt

Set up Environment Variables: Create a .env file in the root directory and add your environment variables, such as the database URL and secret key:

bash

SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
Run Database Migrations:

bash

python manage.py migrate
Run the Development Server:

bash

python manage.py runserver
Usage
Once the development server is running, you can access the application at:

arduino

http://127.0.0.1:8000
Admin Panel:
To access the admin dashboard, use /admin and log in with the superuser credentials.


CHALLENGES & LESSONS

POS & Stock Synchronization: Ensuring real-time updates between the POS system and stock levels.
HR Integration: Streamlining payroll, attendance, and leave management.
Time Constraint: Meeting the short timeline for a complete project has been the hardest part.


