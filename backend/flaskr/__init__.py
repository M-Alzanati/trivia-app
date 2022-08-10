import sys
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from models import setup_db, Question, Category
import random


QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    return questions[start:end]


def dump_categories(categories):
    result = {}
    for item in categories:
        result[item.id] = item.type
    return result


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/*": {"origins": "*"}})

    """
    TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers', 'Content-Type, Authorization, true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS'
        )

        return response

    """
    TODO: Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()

        if (len(categories) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'categories': dump_categories(categories)
        })

    """
    TODO: Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        questions = Question.query.all()
        categories = Category.query.all()

        selected_questions = paginate_questions(request, questions)

        selected_category_ids = list(
            set(map(lambda item: item['category'], selected_questions))
        )

        if (len(selected_questions) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'questions': selected_questions,
            'total_questions': len(questions),
            'categories': dump_categories(categories)
        })

    """
    TODO: Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_questions(id):
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            abort(404)

        try:
            Question.delete(question)
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
        except:
            print(sys.exc_info())
            abort(422)
        finally:
            return jsonify({
                'success': True,
                'deleted': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

    """
    TODO: Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body['question']
        new_answer = body['answer']
        new_difficulty = body['difficulty']
        new_category = body['category']

        question = Question(new_question, new_answer,
                            new_category, new_difficulty)

        try:
            question.insert()
        except:
            print(sys.exc_info())
            abort(422)
        finally:
            return jsonify({
                'success': True
            })

    """
    TODO: Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.get_json()['searchTerm']
        search_result = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        print (search_result)
        return jsonify(
            {
                'questions': [question.format() for question in search_result],
                'totalQuestions': len(search_result),
                'currentCategory': search_result[0].category,
            })

    """
    TODO: Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category_id(id):
        questions = Question.query.filter(Question.category == id).all()
        
        if not questions:
            abort(404)
        
        return jsonify({
          'questions': [question.format() for question in questions],
          'totalQuestions': len(questions)
        })
    
    """
    TODO: Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        body = request.get_json()
        previous_questions = body['previous_questions']
        quiz_category = body['quiz_category']
        questions = []
                  
        if quiz_category['id'] != 0:
            questions = Question.query.filter(Question.category == quiz_category['id']).all()
        else:
            questions = Question.query.all()
        
        if not questions:
            abort(404)
        
        if previous_questions:
            questions = list(filter(lambda item: item.id not in previous_questions, questions))

        try:   
            return jsonify({
                'question': random.choice([q.format() for q in questions]),
            })
        except:
            print(sys.exc_info)
            abort(404)
    
    """
    TODO: Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400
    
    return app
