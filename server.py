import os
import datetime
from tinydb import TinyDB, Query
from flask import Flask, request, jsonify, Response

import semantifier
from src import *

TRAINING_IMG = 'data/training_img'
os.makedirs('database', exist_ok=True)

app = Flask(__name__)
db = TinyDB('database/db.json')


def now():
    return datetime.datetime.now().isoformat()


@app.route('/crawler')
def crawl():
    q = request.args.get('q')
    if q is None:
        raise ValueError('Missing required parameter: q')
    for keyword in q.split(';'):
        crawler.main(keyword, max_num=50)
    return jsonify({
        'task': 'crawl',
        'time': now(),
        'status': 'ok'
    })


@app.route('/train')
def train():
    FaceDetector.main()
    classifier.main('TRAIN', classifier='SVM', batch_size=200)
    return jsonify({
        'task': 'train',
        'time': now(),
        'status': 'ok'
    })


# http://127.0.0.1:5000/recognise?speedup=50&format=ttl&video=yle/a-studio/8a3a9588e0f58e1e40bfd30198274cb0ce27984e
# http://127.0.0.1:5000/recognise?speedup=50&format=ttl&video=yle/eurovaalit-2019-kuka-johtaa-eurooppaa/0460c1b7d735e3fc796aa2829811aa1ae5dc9fa8
# http://127.0.0.1:5000/recognise?speedup=50&format=ttl&video=yle/eurovaalit-2019-kuka-johtaa-eurooppaa/d9d05488b35db559cdef35bac95f518ee0dda76a
@app.route('/recognise')
def recognise():
    video = request.args.get('video')
    speedup = request.args.get('speedup', type=int, default=1)
    no_cache = 'no_cache' in request.args.to_dict()

    results = None
    if not no_cache:
        results = db.search(Query().video == video)
        if results and len(results) > 0:
            results = results[0]

    if not results:
        r = FaceRecogniser.main(video, video_speedup=speedup, confidence_threshold=0.7)
        results = {
            'task': 'recognise',
            'status': 'ok',
            'time': now(),
            'video': video,
            'results': r
        }

        db.insert(results)

    # with open('recognise.json', 'w') as outfile:
    #     json.dump(r, outfile)
    fmt = request.args.get('format')
    if fmt == 'ttl':
        return Response(semantifier.semantify(results), mimetype='text/turtle')

    return jsonify(results)


@app.errorhandler(ValueError)
def handle_invalid_usage(error):
    response = jsonify({
        'status': 'error',
        'error': str(error),
        'time': now()
    })
    response.status_code = 422
    return response


if __name__ == '__main__':
    app.run()
