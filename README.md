# Hackernews_Clone
Developed a clone of the hacker news application

-> Performed web Scraping on the hacker news website using beautiful soup 
-> Created databases - articles, users, relation
-> Using Flask as the backend, with different routes validated login, register, and mark as read and delete operations
-> Handled the logic for logged-in and logged-out users separately in the frontend, backend, and the database
-> the articles are displayed in descending order of the time - handled in SQL

Tech Stack:
Framework: Flask
Language: Python
Database: MYSQL
software: Apache server, phpmyadmin - to create a database 
web scraper : BeautifulSoup4
frontend: HTML (login.html, register.html, newsdashboard.html) , Bootstrap

Requirements:
-> After creating a virtual env in pycharm, I have installed the following packages
pip install -U flask
pip install beautifulsoup4
pip install mysql-connector-python
pip install requests

Databases:
1. Articles
The retrieved article content is stored in articles db
(article_id, title, url, newsurl, time, postedon, votes, comments)

2. Users
(user_id, username, password)

3. relation
(user_id, article_id, mark_read,delete)
