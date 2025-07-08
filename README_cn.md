语音交互是通过调用网上的deepseek ai的API来实现加上了语音转文本 再文本转语音
ai_node  中为只要逻辑代码 其中包含了点位定制以及语音控制的部分

大部分基础包为轮趣ros底盘自带
启动底盘 雷达 imu 以及融合 nv2导航
ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py
启动rviz2 
ros2 launch wheeltec_rviz2 wheeltec_rviz.launch.py
语音交互包
ros2 run ai_node ai_speak

