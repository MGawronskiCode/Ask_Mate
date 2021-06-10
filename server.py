import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)
from werkzeug.utils import secure_filename

import data_handler

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

VOTE_TYPES = {'upvote': 1, 'downvote': -1}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # maksymalny akceptowany rozmiar pliku: 8mb


# zasadniczo w webie jest tak, że niezależnie od tego co zrobimy po stronie frontendu,
# i tak wszystko musimy ponownie sprawdzić na backendzie. (zawsze można zmienić ręcznie formularz na froncie i wrzucić jakieś śmieci)
# w templacie html zaznaczyłem, że akceptujemy tylko png, jpg i jpeg,
# oraz że plik jest wymagany.
# to nie wystarczy (tzn jest fajne, bo użytkownik będzie dokładnie wiedział
# dzięki komunikatom czego w jego formularzu brakuje)
# więc muszę te same rzeczy sprawdzić po stronie pytona
def file_extension_acceptable(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def main_page():
    #TODO how to merge???
    sort_column = 'id'
    sort_method = 'descending'
    user_questions = data_handler.sort_questions(sort_column, sort_method)
    last_questions = []

    for i in range(5):
        last_questions.append(dict(user_questions[i]))

    return render_template('index.html', user_questions=last_questions, headers=data_handler.QUESTIONS_DATA_HEADERS)


@app.route("/add-question", methods=["GET", "POST"])
def add_question():
    if request.method == "POST":
        question_data = dict(request.form)
        image_data = dict(request.files)

        if image_data.values() != "<FileStorage: '' ('application/octet-stream')>":
            image = request.files['image']
            # if not file_extension_acceptable(image.filename):
            #     flash('Unsupported file format')
            #     return redirect(request.url)
            sanitized_filename = secure_filename(image.filename)
            image_storage_filepath = os.path.join(UPLOAD_FOLDER, sanitized_filename)
            image.save(image_storage_filepath)
            image_storage_filepath_as_list = image_storage_filepath.split('/')
            image_storage_filepath_as_list.remove(image_storage_filepath_as_list[0])

            prepared_image_data = "".join(image_storage_filepath_as_list)
            question_data['image'] = prepared_image_data.replace("\\", "/")
            # image_storage_filepath.replace("\\", "/")
        else:
            question_data['image'] = ''
        question_id = data_handler.add_question(question_data)
        return redirect(url_for("show_question", question_id=question_id))
    else:
        return render_template("add_question.html")


@app.route("/question/<question_id>/delete", methods=["GET", "POST"])
def delete_question(question_id):
    if request.method == "POST":
        if request.form["you_sure_button"] == "Yes":
            
            # TODO delete all answers
            # TODO delete all comments to question
            data_handler.delete_question(question_id)

            return redirect(url_for("list_questions"))

        elif request.form["you_sure_button"] == "No":
            return redirect(url_for("show_question", question_id=question_id))

    else:
        return render_template("delete.html", question_id=question_id)


@app.route('/list', methods=["POST", "GET"])
def list_questions():
    sort_data = sort()
    sort_column = sort_data[0]
    sort_method = sort_data[1]

    if request.method == 'POST':
        vote(request.form, 'question')

    user_questions = data_handler.sort_questions(sort_column, sort_method)

    return render_template('question_list.html', search_questions=user_questions, search_answers=[],
                           headers=data_handler.QUESTIONS_DATA_HEADERS)


def sort():
    if request.args.get('sort_submit') is None:
        sort_column = 'submission_time'
        sort_method = 'ascending'
    else:
        sort_column = request.args.get('sort_column')
        sort_method = request.args.get('sort_method')
    return sort_column, sort_method


@app.route('/list/<question_id>', methods=['POST', 'GET'])
def show_question(question_id):
    comment_id = 0
    answer_id = 0
    data_handler.increase_question_views(question_id)
    question_comments = data_handler.sql_get_question_comments(question_id)

    full_data_question = dict(data_handler.get_question(question_id)[0])
    for question_comment in question_comments:
        comment_id = question_comment['id']

    if full_data_question is None:  # tu if false, no?
        return render_template('error_message.html')

    if request.method == 'POST':
        vote(request.form, 'answer')

    answers = data_handler.get_question_answers(question_id)
    for answer in answers:
        answer_id = answer['id']
    answer_comments = data_handler.sql_get_answer_comments(answer_id)
    question_tags = data_handler.get_question_tags(question_id)

    return render_template('show_question.html', question=full_data_question, answers=answers,
                           headers=data_handler.ANSWERS_DATA_HEADERS, question_comments=question_comments,
                           comment_id=comment_id, answer_comments=answer_comments, id=question_id, tags=question_tags)


def vote(request_form, object_type):
    data_list = dict(request_form)['vote'].split()
    vote_type_index = 0
    object_id_index = 1

    vote_type = data_list[vote_type_index]
    object_id = data_list[object_id_index]
    vote_value = VOTE_TYPES[vote_type]

    data_handler.vote(vote_value, object_id, object_type)


@app.route("/question/<question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):
    if request.method == "POST":
        new_title = request.form['title']
        new_message = request.form['message']
        data_handler.edit_question(question_id, new_title, new_message)
        return redirect(url_for("show_question", question_id=question_id))

    else:
        question_to_edit = dict(data_handler.get_question(question_id)[0])
        title = question_to_edit["title"]
        message = question_to_edit["message"]
        return render_template("edit_question].html", question_id=question_id, title=title, message=message)


@app.route('/list/<question_id>/new-answer', methods=["GET", "POST"])
def add_answer(question_id):
    full_data_question = dict(data_handler.get_question(question_id)[0])
    question = [full_data_question['title'], full_data_question['message']]

    if request.method == 'POST':
        message = dict(request.form)['answer']
        data_handler.add_answer(question_id, message)
        return redirect(url_for("show_question", question_id=question_id))

    return render_template('add_answer.html', question_id=question_id, question=question)


@app.route('/answer/<answer_id>/delete', methods=["GET", "POST"])
def delete_answer(answer_id):
    answer = dict(data_handler.get_answer(answer_id)[0])
    question_id = answer['question_id']

    if request.method != "POST":
        return render_template("delete.html", answer_id=answer_id)
    else:

        if request.form["you_sure_button"] == "Yes":
            data_handler.delete_answer(answer_id)
            return redirect(url_for("show_question", question_id=question_id))

        elif request.form["you_sure_button"] == "No":

            return redirect(url_for("show_question", question_id=question_id))
        else:
            return render_template('error_message.html')


@app.route("/answer/<answer_id>/edit", methods=["GET", "POST"])
def edit_answer(answer_id):
    answer_to_edit = dict(data_handler.get_answer(answer_id)[0])
    question_id = answer_to_edit["question_id"]

    if request.method == "POST":
        new_message = request.form['message']
        data_handler.edit_answer(answer_id, new_message)
        return redirect(url_for("show_question", question_id=question_id))
    else:
        message = answer_to_edit["message"]
        return render_template('edit_answer.html', answer_id=answer_id, message=message)


@app.route("/question/<question_id>/delete-tag", methods=['GET', 'POST'])
def delete_tag(question_id):
    all_question_data = data_handler.get_question(question_id)[0]
    tags = data_handler.get_question_tags(question_id)

    if request.method == 'POST':
        tag_to_delete = request.form['tag_to_delete']
        data_handler.delete_tag_from_question(int(question_id), tag_to_delete)
        # todo: info to user about deleting success
        return redirect(url_for("show_question", question_id=question_id))
    return render_template('delete_tag.html', question=all_question_data, tags=tags)


@app.route("/question/<question_id>/new-tag", methods=['GET', 'POST'])
def add_tag(question_id):
    all_question_data = data_handler.get_question(question_id)[0]
    tags = data_handler.get_tags()
    tag_names = []
    for tag in tags:
        tag_names.append(tag['name'])

    if request.method == 'POST':
        if request.form['old_tag'] == 'new tag' and request.form['new_tag'] != '':
            data_handler.add_tag(request.form['new_tag'])
            data_handler.add_tag_to_question(request.form['new_tag'], question_id)
        elif request.form['old_tag'] == 'new tag' and request.form['new_tag'] == '':
            # flash('Please provide new tag name or choose from the list')
            pass
        else:
            data_handler.add_tag(request.form['old_tag'])
            data_handler.add_tag_to_question(request.form['old_tag'], question_id)
        return redirect(url_for("show_question", question_id=question_id))
    return render_template('add_tag.html', question_id=question_id,
                           question=all_question_data, tags=tag_names)


@app.route("/search", methods=['POST', 'GET'])
def search():
    search_questions = data_handler.get_questions()
    # search_answers = []

    if request.args is not None:
        search_phrase = dict(request.args)['search_phrase']
        if search_phrase == '':
            return render_template('question_list.html', search_questions=search_questions, search_answers=[],
                                   headers=data_handler.QUESTIONS_DATA_HEADERS)

        search_questions = data_handler.search_questions(search_phrase)
        search_answers = data_handler.search_answers(search_phrase)

        if not search_questions and not search_answers:
            return render_template('question_list.html', search_questions=[], search_answers=[],
                                   headers=['no results found'])
        else:
            search_questions_id_from_answers = []
            search_questions_from_answers = []
            # search_question_from_answers_id = []
            for answer in search_answers:
                search_questions_id_from_answers.append(data_handler.get_answer_question_id(answer['id']))
                for i in range(len(search_questions_id_from_answers)):
                    search_questions_from_answers.append(
                        data_handler.get_question(dict(search_questions_id_from_answers[i][0])['question_id']))

            search_questions_from_answers_no_duplicates = []
            added_questions_id = []
            for question in search_questions_from_answers:
                if question[0]['id'] not in added_questions_id:
                    search_questions_from_answers_no_duplicates.append(question[0])
                    added_questions_id.append(question[0]['id'])

            return render_template('question_list.html', search_questions=search_questions,
                                   search_questions_from_answers=search_questions_from_answers_no_duplicates,
                                   search_answers=search_answers, headers=data_handler.QUESTIONS_DATA_HEADERS,
                                   answer_headers=data_handler.ANSWERS_DATA_HEADERS)

    return render_template('question_list.html', search_questions=search_questions, search_answers=[],
                           headers=data_handler.QUESTIONS_DATA_HEADERS)


@app.route('/question/<question_id>/new-comment', methods=["GET", "POST"])
def add_question_comment(question_id):
    full_data_question = dict(data_handler.get_question(question_id)[0])
    question = [full_data_question['title'], full_data_question['message']]

    if request.method == 'POST':
        data_handler.sql_add_question_comment(question_id)
        return redirect(url_for("show_question", question_id=question_id))
    return render_template('add_comment.html', question_id=question_id, question=question)


@app.route('/answer/<answer_id>/new-comment', methods=["GET", "POST"])
def add_answer_comment(answer_id):
    full_data_answer = dict(data_handler.get_answer(answer_id)[0])
    answer = full_data_answer['message']
    question_id = full_data_answer['question_id']

    if request.method == 'POST':
        data_handler.sql_add_answer_comment(answer_id)
        return redirect(url_for("show_question", question_id=question_id))
    return render_template('add_answer_comment.html', answer_id=answer_id, answer=answer, question_id=question_id)


@app.route('/comment/<comment_id>/edit', methods=["GET", "POST"])
def edit_question_comment(comment_id):
    comment = dict(data_handler.sql_get_comment(comment_id)[0])
    question_id = comment['question_id']

    if request.method == "POST":
        if question_id is None:
            answer_id = comment['answer_id']
            answer = dict(data_handler.get_answer(answer_id)[0])
            question_id = answer['question_id']
        new_message = request.form['message']
        data_handler.sql_edit_comment(comment_id, new_message)
        return redirect(url_for("show_question", question_id=question_id))
    else:
        if question_id is None:
            answer_id = comment['answer_id']
            answer = dict(data_handler.get_answer(answer_id)[0])
            question_id = answer['question_id']
        message = comment["message"]
        return render_template('edit_comment.html', question_id=question_id, message=message, id=comment_id)


@app.route('/comment/<comment_id>/delete', methods=["GET", "POST"])
def delete_comment(comment_id):
    comment = dict(data_handler.sql_get_comment(comment_id)[0])
    question_id = comment['question_id']

    if request.method != "POST":
        return render_template("delete_comment.html", comment_id=comment_id)
    else:
        if request.form["you_sure_button"] == "Yes":
            data_handler.sql_delete_comment(comment_id)
            return redirect(url_for("show_question", question_id=question_id))
        elif request.form["you_sure_button"] == "No":
            return redirect(url_for("show_question", question_id=question_id))


@app.route('/register', methods=["GET", "POST"])
def register():
    # if already_logged:
    # communicate
    #     return redirect (url_for('main_page'))

    if request.method == 'POST':
        username = request.form['login']
        if data_handler.check_if_username_exist(username):
            # todo:communicate user exist
            return redirect('login')
        else:
            password = request.form['password']
            password_confirm = request.form['password_confirm']
            if password != password_confirm:
                #     message wrong password
                return redirect('register')
            # todo: confirm email
            data_handler.add_new_user(username, password)
            # comunicate added
            return redirect('login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
    #       if check if the usrnme&pass correct:
    #           message about corect loging in
    #           return redirect(url_for('main_page'))
    #       else:
    #           message wrong login/password
    #           return redirect(url_for('login'))

    return render_template('login.html')


if __name__ == "__main__":
    app.run(debug=True)
