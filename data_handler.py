from datetime import datetime

from flask import request
from psycopg2 import sql

import connection

ANSWERS_DATA_PATH = 'sample_data/answer.csv'
QUESTIONS_DATA_PATH = 'sample_data/question.csv'
ANSWERS_DATA_HEADERS = ['id', 'submission_time', 'vote_number', 'question_id', 'message', 'image']
QUESTIONS_DATA_HEADERS = ['id', 'submission_time', 'view_number', 'vote_number', 'title', 'message', 'image']


@connection.connection_handler
def get_answers(cursor):
    query = """ select id, submission_time, vote_number, message, image 
    from answer
    ORDER BY id
    """
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_answer(cursor, answer_id: int):
    query = '''select id, submission_time,question_id, vote_number, message, image 
    from answer 
    where id = %s;
    '''
    query_params = [answer_id]
    cursor.execute(query, query_params)
    x = cursor.fetchall()
    return x


@connection.connection_handler
def get_answer_question_id(cursor, answer_id):
    query = f"""
        SELECT question_id
        FROM answer
        WHERE id = %s"""
    query_params = [answer_id]
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def get_question_answers(cursor, question_id: int):
    query = '''select * 
    from answer 
    where question_id = %s
    order by id;
    '''
    query_params = [question_id]  # [int(question_id)]?
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def sort_questions(cursor, sort_column: str, sort_method):
    if sort_method != 'ascending':
        cursor.execute(sql.SQL(" select * from question order by {} DESC").format(sql.Identifier(sort_column)))
    else:
        cursor.execute(sql.SQL(" select * from question order by {} ").format(sql.Identifier(sort_column)))

    return cursor.fetchall()


@connection.connection_handler
def get_questions(cursor):
    query = ''' select * 
    from question
    order by id;
    '''
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_question(cursor, question_id):
    query = ''' select * 
    from question 
    where id = %s
    '''
    query_params = [question_id]
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def add_answer(cursor, question_id, message, image=None):
    # TODO add uploading image to answer
    submission_time = get_submission_time()
    query = '''
    insert into answer (submission_time, vote_number, question_id, message)
    values(%s, 0, %s, %s)
    '''
    query_params = [submission_time, question_id, message]
    cursor.execute(query, query_params)
    return cursor.rowcount


@connection.connection_handler
def vote(cursor, vote_value, object_id, object_type):
    cursor.execute(
        sql.SQL(' update {} set vote_number = vote_number + %s where id = %s;').format(sql.Identifier(object_type)),
        [vote_value, object_id])


@connection.connection_handler
def add_question(cursor, question_data_dict):
    sub_time = get_submission_time()
    query = ''' insert into question (submission_time,view_number, vote_number,title, message, image)
    values(%s,0,0, %s, %s,%s)
    RETURNING id;  
    '''
    query_params = [sub_time, question_data_dict['title'], question_data_dict['message'], question_data_dict['image']]
    cursor.execute(query, query_params)
    question_id = cursor.fetchall()
    return question_id[0]['id']


@connection.connection_handler
def edit_question(cursor, object_id, new_title, new_message):
    object = "question"
    cursor.execute(sql.SQL(" update {} set title = %s, message = %s where id = %s;").format(sql.Identifier(object)),
                   [new_title, new_message, object_id])
    return cursor.rowcount


@connection.connection_handler
def edit_answer(cursor, object_id, new_message):
    object = "answer"
    cursor.execute(sql.SQL(" update {} set message = %s where id = %s;").format(sql.Identifier(object)),
                   [new_message, object_id])


@connection.connection_handler
def increase_question_views(cursor, question_id):
    query = f"""
        UPDATE question
        SET view_number = view_number + 1
        WHERE id = %s
    """
    query_params = [question_id]
    cursor.execute(query, query_params)
    return cursor.rowcount


@connection.connection_handler
def delete_question(cursor, question_id):


    cursor.execute(delete_answers_comments(question_id))
    cursor.execute(delete_question_answers(question_id))
    cursor.execute(delete_question_comments(question_id))

    query1 = "delete from question where id = %s "
    query_params = [question_id]
    cursor.execute(query1, query_params)



#     query = ''' WITH deleting_func AS (
#     DELETE FROM question
#           WHERE id = %s
#       RETURNING *)
#
# INSERT INTO deleted_question
#             SELECT * FROM deleting_func;
#
#     '''

# def get_answer_ids(cursor, question_id):
#     query = "select id from answer where question_id = question_id"
#     cursor.execute(query)
#     return cursor.fetchall()

def delete_answers_comments(question_id):

    query = "delete from comment where answer_id in(select id from answer where question_id = question_id) "
    return query

def delete_question_answers(question_id):
    query = "delete from answer where question_id = question_id"
    return query

def delete_question_comments(question_id):
    query = "delete from comment where question_id = question_id"
    return query

@connection.connection_handler
def delete_answer(cursor, answer_id):
    query1 = "delete from comment where answer_id = %s"
    query2 = "delete from answer where id = %s"
    # query = '''with deleting_function as (
    # delete from answer
    # where id = %s
    # returning *)
    # insert into deleted_answer
    # select * from deleting_function
    # '''

    query_params = [answer_id]
    cursor.execute(query1,query_params)
    cursor.execute(query2, query_params)


def get_submission_time():
    now = datetime.now()
    date_string = now.strftime("%d/%m/%Y %H:%M:%S")

    return date_string


@connection.connection_handler
def search_questions(cursor, search_phrase):
    query = f"""
        SELECT DISTINCT *
        FROM question
        WHERE UPPER(question.title) LIKE %s OR UPPER(question.message) LIKE %s
    """
    arg = f'%{search_phrase.upper()}%'
    query_params = [arg, arg]
    cursor.execute(query, query_params)

    return cursor.fetchall()


@connection.connection_handler
def search_answers(cursor, search_phrase):
    query = f"""
        SELECT DISTINCT *
        FROM answer
        WHERE UPPER(answer.message) LIKE %s
    """
    query_params = [f'%{search_phrase.upper()}%']
    cursor.execute(query, query_params)

    return cursor.fetchall()


@connection.connection_handler
def get_tags(cursor):
    query = f"""
        SELECT DISTINCT *
        FROM tag
    """
    cursor.execute(query)

    return cursor.fetchall()


@connection.connection_handler
def get_tag_by_name(cursor, tag_name: str):
    query = f"""
        SELECT DISTINCT *
        FROM tag
        WHERE name = %s
    """
    query_params = [tag_name]
    cursor.execute(query, query_params)

    return cursor.fetchall()


@connection.connection_handler
def get_tag(cursor, tag: dict):
    query = f"""
        SELECT DISTINCT *
        FROM tag
        WHERE id = %s
    """
    query_params = [tag['tag_id']]
    cursor.execute(query, query_params)

    return cursor.fetchall()


@connection.connection_handler
def get_question_tags(cursor, question_id):
    query = f"""
            SELECT *
            FROM question_tag
            WHERE question_id = %s
        """
    query_params = [question_id]
    cursor.execute(query, query_params)

    return cursor.fetchall()


@connection.connection_handler
def get_question_tags(cursor, question_id):
    query = f"""
            SELECT *
            FROM question_tag
            WHERE question_id = %s
        """
    query_params = [question_id]
    cursor.execute(query, query_params)

    question_tags = cursor.fetchall()
    tag_data = []
    for question_tag in question_tags:
        tag_data.append(get_tag(question_tag))
    tag_names = []
    for element in tag_data:
        tag_names.append(element[0]['name'])

    return tag_names


@connection.connection_handler
def add_tag(cursor, tag_name):
    tags = get_tags()
    tag_names = []
    for tag in tags:
        if tag['name'] not in tag_names:
            tag_names.append(tag['name'])
    if tag_name not in tag_names:
        query = f"""
            INSERT INTO tag (name)
            VALUES (%s)
        """
        query_params = [tag_name]
        cursor.execute(query, query_params)


@connection.connection_handler
def add_tag_to_question(cursor, tag_name, question_id):
    question_tags_id = get_question_tags(question_id)
    question_tags = []
    for tag_id in question_tags_id:
        question_tags.append(get_tag(tag_id)[0])
    question_tags_names = []
    for question_tag in question_tags:
        if question_tag['name'] not in question_tags_names:
            question_tags_names.append(question_tag['name'])

    if tag_name not in question_tags_names:
        query = f"""
            INSERT INTO question_tag (question_id, tag_id)
            VALUES (%s, %s)
        """
        tag = get_tag(tag_name)[0]
        query_params = [question_id, tag['id']]
        cursor.execute(query, query_params)


@connection.connection_handler
def sql_get_question_comments(cursor, question_id):
    query = f'''
    SELECT *
    FROM comment
    WHERE question_id=%s
    '''
    query_params = (question_id,)
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def sql_get_answer_comments(cursor, answer_id):
    query = f'''
    SELECT *
    FROM comment
    WHERE answer_id=%s
    '''
    query_params = (answer_id,)
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def sql_add_answer_comment(cursor, answer_id):
    comment = dict(request.form)['comment']
    # comment_id = create_id(answer_id)
    submission = get_submission_time()
    query = f'''
    INSERT INTO comment (answer_id, message, submission_time, edited_count)
    VALUES ( %s, %s, %s, %s)
    '''
    query_params = [answer_id, comment, submission, 0]
    cursor.execute(query, query_params)


@connection.connection_handler
def sql_add_question_comment(cursor, question_id):
    comment = dict(request.form)['comment']
    # comment_id = create_id(question_id)
    submission = get_submission_time()
    query = f'''
    INSERT INTO comment (question_id, message, submission_time, edited_count)
    VALUES ( %s, %s, %s, %s)
    '''
    query_params = [question_id, comment, submission, 0]
    cursor.execute(query, query_params)


@connection.connection_handler
def sql_edit_comment(cursor, object_id, new_message):
    object = "comment"
    submission = get_submission_time()
    cursor.execute(
        sql.SQL(" update {} set submission_time = %s, message = %s where id = %s;").format(sql.Identifier(object)),
        [submission, new_message, object_id])
    return cursor.rowcount


@connection.connection_handler
def sql_delete_comment(cursor, comment_id):
    query = f"""
        DELETE FROM comment
        WHERE id = %s
    """
    query_params = [int(comment_id)]
    cursor.execute(query, query_params)


@connection.connection_handler
def sql_get_comments(cursor):
    query = f"""
        SELECT * from comment    
        """
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def sql_get_comment(cursor, id):
    query = f'''
    SELECT *
    FROM comment
    WHERE id=%s
    '''
    query_params = (id,)
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def sql_get_question_comments(cursor, question_id):
    query = f'''
    SELECT *
    FROM comment
    WHERE question_id=%s
    '''
    query_params = (question_id,)
    cursor.execute(query, query_params)
    return cursor.fetchall()


@connection.connection_handler
def delete_tag_from_question(cursor, question_id, tag_to_delete):
    tag = get_tag_by_name(tag_to_delete)[0]
    query = f'''
            WITH deleting_function AS (
                DELETE FROM question_tag
                WHERE question_id = %s AND tag_id = %s
                RETURNING *)
            INSERT INTO deleted_tag
            SELECT * FROM deleting_function;
        '''
    query_params = [question_id, tag['id']]
    cursor.execute(query, query_params)
