#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from pose_msg.msg import GoalPose  # 替换为你的包名

class GoalPublisher(Node):
    def __init__(self):
        super().__init__('goal_publisher')
        self.publisher_ = self.create_publisher(GoalPose, '/goal_pose1', 10)
        timer_period = 2.0  # 每2秒发布一次
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = GoalPose()
        msg.x = 2.0
        msg.y = 0.0
        msg.yaw = 0.1
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: x={msg.x:.2f}, y={msg.y:.2f}, yaw={msg.yaw:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = GoalPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()