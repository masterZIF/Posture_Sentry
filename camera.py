import cv2
import mediapipe as mp
import numpy as np
from collections import deque

class VideoCamera(object):
    # 配置：可视化主题和检测阈值
    THEMES = {
        'hacker': {
            'landmark': (0, 255, 65),    # 矩阵绿 (Matrix Green)
            'connection': (0, 255, 65)
        },
        'cute': {
            'landmark': (255, 255, 255), # 白色 (White)
            'connection': (200, 255, 200) # 柔和绿 (Pastel Green)
        }
    }
    
    # 姿势分类阈值
    ANGLE_SLOUCH_THRESH = 145    # 低于此角度视为“弯腰”
    ANGLE_RECOVERY_THRESH = 155  # 高于此角度视为恢复“正常”

    def __init__(self):
        # 初始化视频捕获并设置标准分辨率
        self.video = cv2.VideoCapture(0) 
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 初始化 MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.status = "Normal" 
        self.neck_inclination = 0 
        self.current_mode = 'cute'
        
        # 使用 deque 作为移动平均滤波器，以平滑抖动的检测结果
        self.angle_history = deque(maxlen=5)

    def set_mode(self, mode):
        if mode in self.THEMES:
            self.current_mode = mode

    def _calculate_vector_angle(self, a, b, c):
        """
        给定三个点 (a, b, c)，计算点 'b' 处的角度。
        用于确定颈部相对于垂直轴的倾斜度。
        """
        a, b, c = np.array(a), np.array(b), np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle

    def get_frame(self):
        success, image = self.video.read()
        if not success: 
            return None

        # 优化：将图像标记为不可写入，以便按引用传递给 MediaPipe
        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        
        # 重新启用绘图
        image.flags.writeable = True
        
        if results.pose_landmarks:
            h, w, _ = image.shape
            landmarks = results.pose_landmarks.landmark
            
            # 提取关键地标点
            # 左耳 (idx 7) 和 左肩 (idx 11)
            pt_ear = [landmarks[7].x * w, landmarks[7].y * h]
            pt_shoulder = [landmarks[11].x * w, landmarks[11].y * h]
            
            # 虚拟点，用于创建从肩部开始的垂直参考线
            pt_vertical = [pt_shoulder[0], pt_shoulder[1] + 100] 
            
            # 计算和平滑角度
            raw_angle = self._calculate_vector_angle(pt_ear, pt_shoulder, pt_vertical)
            self.angle_history.append(raw_angle)
            avg_angle = sum(self.angle_history) / len(self.angle_history)
            
            self.neck_inclination = avg_angle
            self._update_status(avg_angle)
            self._draw_overlay(image, results.pose_landmarks)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def _update_status(self, angle):
        # 迟滞逻辑，防止在阈值处状态闪烁
        if angle < self.ANGLE_SLOUCH_THRESH:
            self.status = "Warning: Slouching!"
        elif angle > self.ANGLE_RECOVERY_THRESH:
            self.status = "Normal"

    def _draw_overlay(self, image, landmarks):
        # 获取当前模式的主题配置，如果找不到则使用 'cute'
        theme = self.THEMES.get(self.current_mode, self.THEMES['cute'])
        
        # 定义地标点绘制规范
        landmark_spec = self.mp_drawing.DrawingSpec(
            color=theme['landmark'], thickness=2, circle_radius=2
        )
        # 定义连接线绘制规范
        connection_spec = self.mp_drawing.DrawingSpec(
            color=theme['connection'], thickness=2, circle_radius=1
        )

        # 绘制 MediaPipe 姿势地标点和连接线
        self.mp_drawing.draw_landmarks(
            image, landmarks, self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=landmark_spec,
            connection_drawing_spec=connection_spec
        )

    def get_data(self):
        """返回当前的遥测数据。"""
        return { 
            "status": self.status, 
            "angle": int(self.neck_inclination) 
        }

    def __del__(self):
        # 析构函数：释放摄像头资源
        if self.video.isOpened():
            self.video.release()