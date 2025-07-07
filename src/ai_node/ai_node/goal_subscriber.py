#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Quaternion
from std_msgs.msg import Int32
from pose_msg.msg import GoalPose
import math

class GoalNavigation(Node):
    def __init__(self):
        super().__init__('goal_navigation_node')
        
        # 创建目标位姿发布者
        self.goal_publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.goal_status_pub = self.create_publisher(Int32, '/goal', 10)
        # 订阅当前位置
        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.pose_callback,
            10
        )
        self.goal_sub = self.create_subscription(
            Int32,
            '/goal1',
            self.goal_callback,
            10
        )
        # 订阅目标点话题
        self.goal_sub = self.create_subscription(
            GoalPose,
            '/goal_pose1',
            self.goal1_callback,
            10
        )
        
        # 参数设置
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('position_threshold', 0.25)  # 位置误差阈值
        self.pose_num = 0
        # 获取参数
        self.frame_id = self.get_parameter('frame_id').value
        self.position_threshold = self.get_parameter('position_threshold').value
        
        # 状态变量
        self.current_pose = PoseStamped()
        self.current_pose.header.frame_id = self.frame_id
        self.current_pose.pose.position.x = 0.0
        self.current_pose.pose.position.y = 0.0
        self.current_pose.pose.position.z = 0.0
        self.current_pose.pose.orientation = self.euler_to_quaternion(0, 0, 0)
        
        self.current_goal = None
        self.timer = self.create_timer(0.1, self.navigate_to_goal)
        
        
    def goal_callback(self, msg: Int32):

        print(msg.data)
        self.pose_num = msg.data 
        

    def goal1_callback(self, msg):
       
        self.current_goal = {
            'x': msg.x,
            'y': msg.y,
            'yaw': msg.yaw
        }
       

    def pose_callback(self, msg):
       
        self.current_pose.header = msg.header
        self.current_pose.pose = msg.pose.pose

    def navigate_to_goal(self):
        
        if self.current_goal is None:
            return
            
        try:
            goal = PoseStamped()
            goal.header.frame_id = self.frame_id
            goal.header.stamp = self.get_clock().now().to_msg()
            goal.pose.position.x = self.current_goal['x']
            goal.pose.position.y = self.current_goal['y']
            goal.pose.position.z = 0.0
            goal.pose.orientation = self.euler_to_quaternion(0, 0, self.current_goal['yaw'])
            
            self.goal_publisher.publish(goal)
            
            # 计算位置误差
            position_error = self.calculate_position_error(self.current_pose, goal)
            self.get_logger().info(f" {position_error:.2f}m", throttle_duration_sec=1.0)
            
            if position_error < self.position_threshold:
                print(self.pose_num)
                self.goal_status_pub.publish(Int32(data=self.pose_num))
                self.current_goal = None
                
        except Exception as e:
            self.get_logger().error("err")

    def euler_to_quaternion(self, roll, pitch, yaw):
     
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        
        q = Quaternion()
        q.w = cr * cp * cy + sr * sp * sy
        q.x = sr * cp * cy - cr * sp * sy
        q.y = cr * sp * cy + sr * cp * sy
        q.z = cr * cp * sy - sr * sp * cy
        return q

    def calculate_position_error(self, current_pose, target_pose):
      
        dx = target_pose.pose.position.x - current_pose.pose.position.x
        dy = target_pose.pose.position.y - current_pose.pose.position.y
        return math.sqrt(dx**2 + dy**2)

def main(args=None):
    rclpy.init(args=args)
    node = GoalNavigation()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()