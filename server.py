from flask import Flask
from flask import render_template
from flask_restful import Api, Resource, reqparse
import time
import thread
from collections import deque

app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('id', type=str)
parser.add_argument('radius', type=int)
parser.add_argument('x', type=int)
parser.add_argument('y', type=int)
parser.add_argument('color', type=str)
parser.add_argument('source', type=str)
parser.add_argument('timestamp', type=float)


data = {}
watching = {}
playing = {}
queue = deque(maxlen=1024)
key = 0

def gen_id():
    global key
    key = key + 1
    return 'obj_%s'%(key)
            
class Circles(Resource):
    def get(self):
        return data
    
    def post(self):
        obj = parser.parse_args()
        obj_id = obj['id']
        if not obj_id:
            obj_id = gen_id()
            obj['id'] = obj_id;
            command = 'create'
        else:
            command = 'update'
        timestamp = time.time()
        source = obj['source']
        
        obj['timestamp'] = timestamp
        playing[source] = timestamp
        watching[source] = timestamp
        
        data[obj_id] = obj
        item = obj.copy()
        item['command'] = command
        queue.append(item)
        return data[obj_id], 201
        
class Queue(Resource):
    def get(self):
        args = parser.parse_args()
        source = args['source']
        timestamp = args['timestamp']
        result = []
        for item in reversed(queue):
            if item['timestamp'] > timestamp:
                if item['source'] != source:
                    result.insert(0, item)
            else:
                break
        watching[source] = time.time()
        return result

class Stat(Resource):
    def get(self):
        return {'watching' : len(watching), 'playing': len(playing) }
                
api.add_resource(Queue, '/queue')
api.add_resource(Circles, '/data')
api.add_resource(Stat, '/stat')

@app.route('/')
def index():
    return render_template('canvas.html')

def live(threadName, interval):
    while True:
        time.sleep(interval)
        for t in playing.copy():
            if time.time() - playing[t] > 10:
                del playing[t]
                
        for t in watching.copy():
            if time.time() - watching[t] > 10:
                del watching[t]
                 
        for obj_id in data.copy():
            obj = data[obj_id]
            if time.time() - obj['timestamp'] < 2:
                continue
            radius = obj['radius']
            if radius <= 100:
                radius = radius - 10
            else:
                radius = radius * .9;
                radius = round(radius)
                if radius < 100:
                    radius = 100
            if radius <= 0:
                del data[obj_id]
                command = 'destroy'
            else:
                obj['radius'] = radius
                command = 'update'
            obj['timestamp'] = time.time()
            item = obj.copy()
            item['command'] = command
            item['source'] = ''
            queue.append(item)
    
if __name__ == '__main__':
    thread.start_new_thread(live, ('Live', 0.1))
    app.run(debug=False, host='0.0.0.0')
        
        
        