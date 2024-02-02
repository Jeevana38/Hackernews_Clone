from flask import Flask, render_template, redirect, request, session, url_for
import requests
import mysql.connector
from bs4 import BeautifulSoup
import os
app = Flask(__name__)
app.secret_key=os.urandom(24)
conn = mysql.connector.connect(host="localhost",user="root",password="",database="newsdb")
cursor=conn.cursor()

def webscraping(): #scraping the url to retrieve the article content
    for page_number in range(1, 4):  # To get articles from first 3 pages
        url = f'https://news.ycombinator.com/news?p={page_number}'
        response = requests.get(url)

        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            tr_elements = soup.find_all('tr', class_='athing')

            for tr_element in tr_elements:
                td = tr_element.find_next('td', class_='subtext')

                url = tr_element.select_one('.titleline a')['href']
                a_element = tr_element.select_one('.titleline a')
                title = a_element.text if a_element else ''

                sitebit_element = tr_element.select_one('.sitebit a')
                newsurl = "https://news.ycombinator.com/" + sitebit_element['href'] if sitebit_element else ''

                time = td.select_one('.age')['title']

                score_element = td.select_one('.score')
                votes = score_element.get_text(strip=True) if score_element else ''

                time_element = td.select_one('.age a')
                postedon = time_element.get_text(strip=True)

                comments_element = td.select_one('.subtext a[href*="item?id="]')
                comments_text = comments_element.get_text(strip=True) if comments_element else ''
                comments = int(comments_text.split()[0]) if comments_text else 0

                cursor.execute("""
                    INSERT INTO `articles` (`article_id`, `title`, `url`, `newsurl`, `time`, `postedon`, `votes`, `comments`)
                    VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    `url` = VALUES(`url`),
                    `newsurl` = VALUES(`newsurl`),
                    `time` = VALUES(`time`),
                    `postedon` = VALUES(`postedon`),
                    `votes` = VALUES(`votes`),
                    `comments` = VALUES(`comments`)
                """, (title, url, newsurl, time, postedon, votes, comments))

            conn.commit()



@app.route('/')
def dashboard():
    webscraping()
    user_id = session.get('user_id')

    if user_id is not None:  #if user is logged in, implementing logic for display
        delete = True
        cursor.execute("""
            SELECT a.article_id, a.title, a.url, a.newsurl, a.time, a.postedon, a.votes, a.comments
            FROM `articles` a
            LEFT JOIN `relation` r ON a.article_id = r.article_id
            WHERE (r.user_id = %s AND r.delete != %s) OR r.user_id IS NULL
            ORDER BY a.time DESC
        """, (user_id, delete))
        articles = cursor.fetchall()
        login=True
        return render_template('newsdashboard.html', login=login, articles=articles)
    else: #if user is not logged in
        cursor.execute("""SELECT * FROM `articles` ORDER BY time DESC""")
        articles = cursor.fetchall()
        login = False
        return render_template('newsdashboard.html', login=login, articles=articles)



@app.route('/register', methods=['GET', 'POST'])
def register(): #adding new user by retrieving username and password from form
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor.execute("""SELECT * FROM `users` WHERE `username` = '{}'""".format(username))
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.execute("""INSERT INTO `users` (`user_id`,`username`,`password`) VALUES(NULL,'{}','{}')""".format(username,password))
            conn.commit()
            cursor.execute("""SELECT * FROM `users` WHERE `username` = '{}'""".format(username))
            new_user = cursor.fetchone()
            if new_user:
                session['user_id'] = new_user[0]
                return redirect('/')

        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login(): #login validation
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor.execute("""SELECT * FROM `users` WHERE `username` = '{}' and `password` = '{}'""".format(username,password))
        user = cursor.fetchone()
        if user: #if user exists with the combination, then we set user_id in session
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html', error=None)

@app.route('/mark_as_read/<int:article_id>', methods=['GET','POST'])
def mark_as_read(article_id):
    user_id = session.get('user_id')
    if user_id is None: #user needs to login to perform this operation
        return redirect('/login')
    try: #if user is logged in, I am marking the article as read..the changes are reflected in the relation database
        #cursor.execute("""INSERT INTO `relation` (`user_id`,`article_id`,`mark_read`,`delete`) VALUES('{}','{}','{}',NULL) ON DUPLICATE KEY UPDATE mark_read=True)""".format(user_id,article_id,True))
        cursor.execute("""
                    INSERT INTO `relation` (`user_id`, `article_id`, `mark_read`, `delete`)
                    VALUES (%s, %s, %s, NULL)
                    ON DUPLICATE KEY UPDATE `mark_read` = %s
                """, (user_id, article_id, True, True))
        conn.commit()

        return redirect('/')
    except Exception as e:
        print(f"Error: {e}")
        return redirect('/')

@app.route('/delete/<int:article_id>',methods=['GET','POST'])
def delete(article_id):
    user_id = session.get('user_id')
    if user_id is None: #user needs to login to perform delete operation
        return redirect('/login')
    try: #if user is logged in, I delete the article on the display but it's  still in the db
        #cursor.execute("""INSERT INTO `relation` (`user_id`,`article_id`,`mark_read`,`delete`) VALUES('{}','{}',NULL,'{}') ON DUPLICATE KEY UPDATE delete= `True`""".format(user_id,article_id,True))
        cursor.execute("""
            INSERT INTO `relation` (`user_id`, `article_id`, `mark_read`, `delete`)
            VALUES (%s, %s, NULL, %s)
            ON DUPLICATE KEY UPDATE `delete` = %s
        """, (user_id, article_id, True, True))

        cursor.commit()
        return redirect('/')
    except Exception as e:
        print(f"Error: {e}")
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')

if __name__=="__main__":
    app.run(debug=True)