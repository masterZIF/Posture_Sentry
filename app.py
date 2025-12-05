import os
from flask import Flask, render_template, Response, jsonify
from camera import VideoCamera
import webbrowser
from threading import Timer

app = Flask(__name__)

# 全局单例，用于摄像头设备，以防止资源冲突
video_camera = None

def get_camera_instance():
    """
    确保在所有请求中只有一个 VideoCapture 实例存在。
    """
    global video_camera
    if video_camera is None:
        video_camera = VideoCamera()
    return video_camera

def generate_stream(camera):
    """视频流生成器函数。"""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/')
def index():
    return render_template('menu.html')

@app.route('/mode/<mode_name>')
def switch_mode(mode_name):
    """
    用于模式切换的统一路由。
    根据请求的模式重置摄像头可视化风格。
    """
    if mode_name not in ['cute', 'hacker']:
        return "Invalid Mode", 400
    
    camera = get_camera_instance()
    camera.set_mode(mode_name)
    
    return render_template(f'{mode_name}.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(get_camera_instance()), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status_feed():
    """用于前端 AJAX 轮询的 API。"""
    return jsonify(get_camera_instance().get_data())

if __name__ == '__main__':
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5001/')
    # 启动定时器，在 1 秒后打开浏览器
    Timer(1, open_browser).start()
    # 运行 Flask 应用
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)