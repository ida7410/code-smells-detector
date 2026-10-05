import os

user_input = "print('hello')"
eval(user_input)

password = 'admin123'

def get_user(user_id):
    query = 'SELECT * FROM users WHERE id = ' + user_id
    return query

assert os.path.exists("/tmp"), "Path must exist"
