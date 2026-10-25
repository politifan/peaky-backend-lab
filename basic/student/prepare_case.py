import os,sys,subprocess
from sqlalchemy import create_engine,inspect,text
from pwdlib import PasswordHash
# Запускайте только с новой отдельной учебной БД. Скрипт никогда не удаляет существующие таблицы.
case=sys.argv[1] if len(sys.argv)>1 else '02-schema'
url=os.environ['DATABASE_URL'];engine=create_engine(url)
if inspect(engine).has_table('users'):raise SystemExit('Нужна новая отдельная учебная БД без users; существующие данные не удаляются')
target='0001' if case=='02-schema' else 'head'
subprocess.run([sys.executable,'-m','alembic','upgrade',target],check=True)
with engine.begin() as con:
 con.execute(text('INSERT INTO users(username,password_hash) VALUES (:name,:hash)'),{'name':'legacy','hash':PasswordHash.recommended().hash('TutorialPassword42')})
 owner=con.scalar(text("SELECT id FROM users WHERE username='legacy'"))
 columns='owner_id,title,request_key,request_title,request_priority'
 values=':owner,:title,:key,:title,1'
 if target=='head':columns+=',priority';values+=',1'
 con.execute(text('INSERT INTO tickets('+columns+') VALUES ('+values+')'),{'owner':owner,'title':'Старая заявка не удалять','key':'baseline'})
print('Исходная ревизия',target,'старые данные созданы. Пользователь legacy пароль только учебный TutorialPassword42')
