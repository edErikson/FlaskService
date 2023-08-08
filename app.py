from flask import Flask, request, render_template, jsonify
from flask_restful import Api, Resource
import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'mydatabase.db')

app = Flask(__name__)
api = Api(app)
app._static_folder = 'static/css'


def query_database(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if query.startswith('SELECT'):
            return cur.fetchall()
        else:
            conn.commit()
            return cur.lastrowid


def get_available_languages():
    results = query_database("SELECT DISTINCT lang FROM translations", ())
    return [lang[0] for lang in results]


def get_word_count():
    count = query_database("SELECT COUNT(DISTINCT word) FROM translations")
    return count[0][0] if count else 0


def get_translations(word):
    results = query_database("SELECT lang, translation FROM translations WHERE word = ?", (word,))
    translations = {lang: text for lang, text in results}
    return translations


class Translation(Resource):
    @staticmethod
    def get():
        word = request.args.get('word')
        translations = get_translations(word)
        if isinstance(translations, str):
            return {"message": translations}
        else:
            return translations


api.add_resource(Translation, '/translate')


class AllWords(Resource):
    @staticmethod
    def get():
        results = query_database("SELECT DISTINCT word FROM translations")
        words = [word[0] for word in results]
        return words


api.add_resource(AllWords, '/words')


@app.route("/", methods=['GET', 'POST'])
def index():
    translation = {}
    languages = get_available_languages()
    word_count = get_word_count()

    if request.method == 'POST':
        word = request.form.get('word')
        if word:
            translation = get_translations(word)
            return render_template("index.html", translation=translation,
                                   word=word, languages=languages, word_count=word_count)

    if request.method == 'GET':
        word = request.args.get('word')
        if word:
            translation = get_translations(word)
            return jsonify(translation)

    return render_template("index.html", translation=translation, languages=languages, word_count=word_count)


@app.route('/word_list')
def word_list():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT word FROM translations ORDER BY word ASC')
        results = cur.fetchall()
        words = [row[0] for row in results]
        return jsonify(words)


if __name__ == '__main__':
    app.run(debug=True)
