from flask import Flask, request, jsonify, render_template_string
import subprocess

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Command Server</title>
</head>
<body>
    <h2>Remote Command Server</h2>
    <p>Server is running. Use the client to send commands.</p>
    <p>Endpoint: <code>/command</code> (POST)</p>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/command', methods=['POST'])
def execute_command():
    command = request.json.get('command')
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return jsonify({
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)