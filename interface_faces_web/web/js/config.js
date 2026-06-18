window.FACE_WEB_CONFIG = {
  rosbridgeUrl: `ws://${window.location.hostname}:9090`,
  faceTopic: "/face/expression",
  reconnectMs: 2000,
  fallbackExpression: "idle",
  messageType: "std_msgs/msg/String"
};
