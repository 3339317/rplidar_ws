# -*- coding: utf-8 -*-
import os
from volcenginesdkarkruntime import Ark
import dotenv
import wave
import requests
import json
import base64
import asyncio
import time
import sounddevice as sd # type: ignore
import asyncio
import edge_tts
import rclpy
import subprocess
import psutil
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Int32
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped,PoseWithCovarianceStamped
from ai_msgs.msg import PerceptionTargets
from pose_msg.msg import GoalPose

class AITalker(Node):
    def __init__(self):
        super().__init__('ai_talker')
        self.publisher = self.create_publisher(String, 'ai_msg', 10)
        self.twist_pub = self.create_publisher(Twist,"/cmd_vel",10)
        self.goal_status_pub = self.create_publisher(Int32, '/goal1', 10)
        self.publisher_ = self.create_publisher(GoalPose, '/goal_pose1', 10)
        self.goal_sub = self.create_subscription(
            Int32,
            '/goal',
            self.goal_callback,
            10
        )

        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.pose_callback,
            10
        )
        
        self.subscription = self.create_subscription(
            PerceptionTargets,
            '/hobot_face_age_detection',
            self.callback,
            10
        )
        
        self.current_age = None
        self.current_pose = PoseStamped()
        self.pose_num = 1
        self.auto_pose = False
        self.timer = self.create_timer(1, self.timer_callback)  # 定时触发
        self.ai = AIAssistant()
        self.ai_star = False
        ai = AIAssistant()
        self.twist = Twist()
        self.ai_respon = False
        #ai.init()
        self.line_speed = 0.1
        self.angular_speed = 0.3
        self.recognizer = BaiduSpeechRecognizer()
        self.audio_file = "my_recording.wav"
        self.msg = String()
        self.ai.init()
        
    def callback(self, msg):
        for self.target in msg.targets:
            if self.target.type != '':
                for attr in self.target.attributes:
                    # 提取age属性
                    if attr.type == 'age':
                        self.current_age = attr.value
                        self.get_logger().info(
                            f"age: {self.current_age} "  
                        )   
        
    def goal_callback(self, msg: Int32):
        """处理goal状态消息"""
        if msg.data == 1 :
            audio_file = "/root/rplidar_ws/dianwei1.mp3"
            os.system(f"mpg123 -q -o alsa -a plughw:2,0 {audio_file}")
            self.auto_pose = False
        if msg.data == 2 :
            audio_file = "/root/rplidar_ws/dianwei2.mp3"
            os.system(f"mpg123 -q -o alsa -a plughw:2,0 {audio_file}")
            self.auto_pose = False
        if msg.data == 3 :
           goal_msg = GoalPose()
           goal_msg.x = 26.40
           goal_msg.y = 2.71
           goal_msg.yaw = 0.1
           self.publisher_.publish(goal_msg)
           self.goal_status_pub.publish(Int32(data=4))
           self.auto_pose = False  
        if msg.data == 4 :
            audio_file = "/root/rplidar_ws/dianwei1.mp3"
            os.system(f"mpg123 -q -o alsa -a plughw:2,0 {audio_file}")
            self.auto_pose = False
            
            
    def pose_callback(self, msg):
        self.current_pose.header = msg.header
        self.current_pose.pose = msg.pose.pose

        self.current_x = self.current_pose.pose.position.x  # 与您写的方式一致
        self.current_y = self.current_pose.pose.position.y


    def move(self):
        self.twist.linear.x = self.line_speed
        self.twist.angular.z = 0.0
        self.twist_pub.publish(self.twist)
            
    def back(self):
        self.twist.linear.x = -self.line_speed
        self.twist.angular.z = 0.0
        self.twist_pub.publish(self.twist)

    def right(self):
        self.twist.linear.x = 0.05
        self.twist.angular.z = self.angular_speed
        self.twist_pub.publish(self.twist)
        
    def left(self):
        self.twist.linear.x = 0.05
        self.twist.angular.z = self.angular_speed
        self.twist_pub.publish(self.twist)
        
    def stop(self):
        self.twist.linear.x = 0.0
        self.twist.angular.z = 0.0
        self.twist_pub.publish(self.twist)

    def add_line(self):
        self.line_speed += 0.2
        if self.line_speed > 0.7:
            self.line_speed = 0.7
            response = "我已经全速前进了"
        else: 
            response = f"当前速度为 {self.line_speed:.1f}"  
        asyncio.run(text_to_speech_edge(response))

    def reduce_line(self): 
        self.line_speed -= 0.2
        if self.line_speed < 0.1:
            self.line_speed = 0.1
            response = "我已经比乌龟还要慢了"
        else:
            response = f"当前速度为 {self.line_speed:.1f}"  
        asyncio.run(text_to_speech_edge(response))

    def add_angular(self):
        self.angular_speed +=0.2
        if self.angular_speed > 0.7:
            self.angular_speed = 0.7
            response = "我已经全速旋转了"
        else: 
            response = f"当前速度为 {self.angular_speed:.1f}"  
        asyncio.run(text_to_speech_edge(response))

    def reduce_angular(self): 
        self.angular_speed -= 0.2
        if self.angular_speed < 0.3:
            self.angular_speed = 0.3
            response = "我已经转不动了"
        else:
            response = f"当前速度为 {self.angular_speed:.1f}"  
        asyncio.run(text_to_speech_edge(response))
    def timer_callback(self):
        if self.ai_star == False :
                
            record_audio(self.audio_file, duration=5)
            print("录音完成")

            result = self.recognizer.recognize_speech(self.audio_file)
            print(f"识别结果: {result}")
            if not result:  # 判断空字符串或 None
                print("字符串为空或 None")
                result = "code"

            if "启动" in result:
                self.ai_star = True
                asyncio.run(text_to_speech_edge("你好请问有什么可以帮你的"))
            else :
                pass
    
        if self.ai_star == True :
            if self.auto_pose == False :
                record_audio(self.audio_file, duration=5)
                print("录音完成")
                result = self.recognizer.recognize_speech(self.audio_file)
                self.msg.data = result
                self.publisher.publish(self.msg)
                self.get_logger().info(f'Publishing: "{self.msg.data}"')  # 打印日志
                print(f"识别结果: {result}")

                
                if "年龄识别" in result:
                    if self.target.type != '':
                        age_int = int(self.current_age)
                        age_str = f"您的年龄为{age_int}岁"
                        asyncio.run(text_to_speech_edge(age_str))
                        self.target.type = ""
                    else :
                        asyncio.run(text_to_speech_edge("非真人目标"))
                    self.ai_respon = False
                
                            
                if "前往一号" in result :
                    if self.pose_num == 1 :
                        msg = GoalPose()
                        msg.x = 8.13
                        msg.y = 1.59
                        msg.yaw = 0.64
                        self.publisher_.publish(msg)
                        self.goal_status_pub.publish(Int32(data=1))
                        self.ai_respon = False
                        self.auto_pose = True
                
                if "前往二号" in result :
                    if self.pose_num == 1 :
                        msg = GoalPose()
                        msg.x = 19.42
                        msg.y = 0.12
                        msg.yaw = 0.99
                        self.publisher_.publish(msg)
                        self.goal_status_pub.publish(Int32(data=2))
                        self.ai_respon = False
                        self.auto_pose = True
                        
                if "前往三号" in result :
                    if self.pose_num == 1 :
                        msg = GoalPose()
                        msg.x = 16.43
                        msg.y = 0.34
                        msg.yaw = 0.93
                        self.publisher_.publish(msg)
                        self.goal_status_pub.publish(Int32(data=3))
                        self.ai_respon = False
                        self.auto_pose = True
                        
                
                if "停止导航" in result :
                    msg = GoalPose()
                    msg.x = self.current_x
                    msg.y = self.current_y
                    msg.yaw = 0.1
                    self.publisher_.publish(msg)
                    self.ai_respon = False
                     
                if "前进" in result:
                    self.move()
                    self.ai_respon = False
                    asyncio.run(text_to_speech_edge("前进中"))
                    time.sleep(2)
                    self.stop()    
    
                if "后退" in result:
                    self.back()
                    self.ai_respon = False
                    asyncio.run(text_to_speech_edge("后退中"))
                    time.sleep(2)
                    self.stop()    
    
                if "右转" in result:
                    self.right()
                    self.ai_respon = False
                    asyncio.run(text_to_speech_edge("右转中"))
                    time.sleep(2)
                    self.stop()    
    
                if "左转" in result:
                    self.left()
                    self.ai_respon = False
                    asyncio.run(text_to_speech_edge("左转中"))
                    time.sleep(2)
                    self.stop()     
                
                if "增加角速度" in result:
                    self.add_angular()
                    self.ai_respon = False
    
                if "减小角速度" in result:
                    self.reduce_angular()
                    self.ai_respon = False
                
                if "增加线速度" in result:
                    self.add_line()
                    self.ai_respon = False
    
                if "减小线速度" in result:
                    self.reduce_line()
                    self.ai_respon = False
    
                
                if "停车" in result:
                    self.stop()
                    self.ai_respon = False
                    asyncio.run(text_to_speech_edge("好的"))     
                        
                if "退出" in result:
                    self.ai_respon = False
                    self.ai_star = False
                    asyncio.run(text_to_speech_edge("再见")) 

                if self.ai_respon == True and result !=  "":
                    print("正在获取AI回复...")
                    response = self.ai.doubao(result)
                    print(f"AI回复: {response}")
                    asyncio.run(text_to_speech_edge(response))   
                    print("准备下一次录音...\n")
    
                if "小王同学" in result:
                    self.ai_respon = True
                    # self.ai_respon = False
                    asyncio.run(text_to_speech_edge("你好我是小王同学"))
            
        #if os.path.exists(self.audio_file):  # 检查文件是否存在
            #os.remove(self.audio_file)

  
async def text_to_speech_edge(text, voice="zh-CN-YunxiNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("output.mp3")  # 保存为文件
    os.system("mpg123 -q -o alsa -a plughw:2,0 output.mp3")
    os.remove("output.mp3")

class AIAssistant:
    def __init__(self):
        self.client = None
        self.model_id = None
        self.is_initialized = False
    
    def init(self, env_path="/root/.env"):

        dotenv.load_dotenv(env_path)
        
        # 初始化Ark客户端
        self.client = Ark()
        self.model_id = os.getenv("ENDPOINT_ID")
        
        self.is_initialized = True
        print("AI助手初始化完成，请输入您的问题")
    
    def doubao(self, question):

        if not self.is_initialized:
            raise RuntimeError("请先调用init()方法初始化")
        
        if not question:
            return None
        
        # 创建流式对话请求
        stream = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": "你是小王同学"},
                {"role": "user", "content": question},
            ],
            stream=True
        )
        
        # 收集AI的回复
        full_text = ""
        for chunk in stream:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content
            print(text, end="")
            full_text += text
        
        return full_text

class BaiduSpeechRecognizer:
    def __init__(self):
        self.API_KEY = "IP43hM6K4Fg67gQX7TtM3Kpw"
        self.SECRET_KEY = "ZVblYrM1N9iMPC6dAnynmByn5jpWaHjN"
    
    def get_file_content_as_base64(self, file_path, urlencoded=False):

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
            if urlencoded:
                content = requests.utils.quote(content)
        return content
    
    def get_access_token(self):

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.API_KEY,
            "client_secret": self.SECRET_KEY
        }
        response = requests.post(url, params=params)
        return response.json().get("access_token")
    
    def recognize_speech(self, audio_file_path):

        # 检查文件是否存在
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
        
        url = "https://vop.baidu.com/server_api"
        
        try:
            # 获取音频文件的 Base64 编码和原始大小
            speech_base64 = self.get_file_content_as_base64(audio_file_path, False)
            file_size = os.path.getsize(audio_file_path)  # 更高效获取文件大小的方法
            
            payload = json.dumps({
                "format": "wav",  # 如果是PCM格式请改为"pcm"
                "rate": 16000,
                "channel": 1,
                "cuid": "python_client",
                "speech": speech_base64,
                "len": file_size,
                "token": self.get_access_token()
            }, ensure_ascii=False)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
            result = response.json()
            
            if "result" in result:
                return result["result"][0]  # 返回识别结果
            else:
                print(f"识别失败: {result.get('err_msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"语音识别过程中发生错误: {str(e)}")
            return None



def record_audio(output_file="out.wav", duration=5, sample_rate=16000, channels=1):
    print(f"?? 开始录音（{duration}秒）...")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype='int16'
    )
    sd.wait()  # 等待录音完成
    
    print("? 录音完成！")
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())
    
    print(f"?? 音频已保存至: {output_file}")
    return output_file




def main():
    rclpy.init()
    node = AITalker()
    rclpy.spin(node)  # 所有逻辑在回调中处理
    node.destroy_node()
    rclpy.shutdown()
if __name__ == "__main__":
    main()