import numpy as np
import transformations as tf

import rospy
from visualization_msgs.msg import Marker, MarkerArray


class GraspPlotter:

    def __init__(
        self,
        topic='/plot_grasps',
        finger_width=0.0065,
        outer_diameter=0.098,
        hand_depth=0.055,
        hand_height=0.025,
    ):
        self.rviz_pub = rospy.Publisher(topic, MarkerArray, queue_size=1)
        self.finger_width = finger_width
        self.outer_diameter = outer_diameter
        self.hand_depth = hand_depth
        self.hand_height = hand_height

    def draw_grasps(self, grasps, scores, frame='world'):
        markers = self.convert_to_visual_grasp_msg(grasps, scores, frame)
        self.rviz_pub.publish(markers)

    def pose_to_matrix(self, pose_msg):
        translation = [
            pose_msg.position.x,
            pose_msg.position.y,
            pose_msg.position.z,
        ]
        quaternion = [
            pose_msg.orientation.w,
            pose_msg.orientation.x,
            pose_msg.orientation.y,
            pose_msg.orientation.z,
        ]
        transform = tf.quaternion_matrix(quaternion)
        transform[:3, 3] = translation
        return transform

    def convert_to_visual_grasp_msg(self, grasps, scores, frame_id):
        hw = 0.5 * self.outer_diameter - 0.5 * self.finger_width

        marker_array = MarkerArray()
        for i, g, score in zip(range(len(grasps)), grasps, scores):
            hand = self.pose_to_matrix(g)

            grasp_approach = hand[:3, 2]
            grasp_binormal = -hand[:3, 1]
            grasp_axis = hand[:3, 0]
            grasp_bottom = hand[:3, 3]

            frame = np.eye(4)
            frame[:3, 0] = grasp_approach
            frame[:3, 1] = grasp_binormal
            frame[:3, 2] = grasp_axis

            left_bottom = grasp_bottom - hw * grasp_binormal
            right_bottom = grasp_bottom + hw * grasp_binormal
            left_bottom += 0.055 * grasp_approach
            right_bottom += 0.055 * grasp_approach
            left_top = left_bottom + self.hand_depth * grasp_approach
            right_top = right_bottom + self.hand_depth * grasp_approach
            left_center = left_bottom + 0.5 * (left_top - left_bottom)
            right_center = right_bottom + 0.5 * (right_top - right_bottom)
            base_center = left_bottom + 0.5 * (right_bottom - left_bottom)
            base_center -= 0.01 * grasp_approach
            approach_center = base_center - 0.04 * grasp_approach

            finger_lwh = np.array(
                [
                    self.hand_depth,
                    self.finger_width,
                    self.hand_height,
                ]
            )
            approach_lwh = np.array([0.08, self.finger_width, self.hand_height])

            base = self.create_hand_base_marker(
                score,
                left_bottom,
                right_bottom,
                frame,
                0.02,
                self.hand_height,
                i,
                frame_id,
            )
            left_finger = self.create_finger_marker(
                score,
                left_center,
                frame,
                finger_lwh,
                i * 3,
                frame_id,
            )
            right_finger = self.create_finger_marker(
                score,
                right_center,
                frame,
                finger_lwh,
                i * 3 + 1,
                frame_id,
            )
            approach = self.create_finger_marker(
                score,
                approach_center,
                frame,
                approach_lwh,
                i * 3 + 2,
                frame_id,
            )

            marker_array.markers.extend(
                [
                    left_finger,
                    right_finger,
                    approach,
                    base,
                ]
            )

        return marker_array

    def create_finger_marker(
        self,
        score,
        center,
        frame,
        lwh,
        marker_id,
        frame_id,
    ):
        marker = Marker()
        marker.header.frame_id = frame_id
        marker.header.stamp = rospy.Time()
        marker.ns = "finger"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = center[0]
        marker.pose.position.y = center[1]
        marker.pose.position.z = center[2]
        marker.lifetime = rospy.Duration(10)

        quat = tf.quaternion_from_matrix(frame)
        marker.pose.orientation.w = quat[0]
        marker.pose.orientation.x = quat[1]
        marker.pose.orientation.y = quat[2]
        marker.pose.orientation.z = quat[3]

        marker.scale.x = lwh[0]  # forward direction
        marker.scale.y = lwh[1]  # hand closing direction
        marker.scale.z = lwh[2]  # hand vertical direction

        blue = 1 - score
        red = score

        marker.color.a = 0.5
        marker.color.r = red
        marker.color.g = 0.0
        marker.color.b = blue

        return marker

    def create_hand_base_marker(
        self,
        score,
        start,
        end,
        frame,
        length,
        height,
        marker_id,
        frame_id,
    ):
        center = start + 0.5 * (end - start)

        marker = Marker()
        marker.header.frame_id = frame_id
        marker.header.stamp = rospy.Time()
        marker.ns = "hand_base"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = center[0]
        marker.pose.position.y = center[1]
        marker.pose.position.z = center[2]
        marker.lifetime = rospy.Duration(10)

        quat = tf.quaternion_from_matrix(frame)
        marker.pose.orientation.w = quat[0]
        marker.pose.orientation.x = quat[1]
        marker.pose.orientation.y = quat[2]
        marker.pose.orientation.z = quat[3]

        marker.scale.x = length  # forward direction
        marker.scale.y = np.linalg.norm(end - start)  # hand closing direction
        marker.scale.z = height  # hand vertical direction

        blue = 1 - score
        red = score

        marker.color.a = 0.5
        marker.color.r = red
        marker.color.g = 0.0
        marker.color.b = blue

        return marker
