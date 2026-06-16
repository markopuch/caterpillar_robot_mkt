# roboclaw_ros2

Paquete ROS 2 minimo para controlar una base movil diferencial con RoboClaw.

El flujo principal es:

```text
interface_pc -> cmd_vel -> roboclaw_node -> RoboClaw SpeedM1M2
```

## Nodo principal

`roboclaw_ros2/nodes/roboclaw_node.py`

- Se suscribe a `cmd_vel` (`geometry_msgs/msg/Twist`).
- Usa `linear.x` y `angular.z` para calcular velocidad izquierda y derecha.
- Convierte m/s a ticks/s con:

```text
ticks_per_meter = ticks_per_revolution / (2 * pi * wheel_radius)
```

- Envia velocidades al RoboClaw con `SpeedM1M2(address, left_ticks, right_ticks)`.
- Si deja de recibir `cmd_vel`, manda velocidad cero.
- Publica setpoints de diagnostico:
  - `roboclaw/cmd_speed/left`
  - `roboclaw/cmd_speed/right`
  - `roboclaw/cmd_ticks/left`
  - `roboclaw/cmd_ticks/right`

Este paquete ya no lee encoder, corriente, voltaje, temperatura ni publica odometria.

## Parametros

`config/params.yaml`

- `port`: puerto serial del RoboClaw, por ejemplo `/dev/ttyACM0`.
- `baud`: baudrate serial.
- `address`: direccion del controlador, normalmente `128` (`0x80`).
- `control_rate_hz`: frecuencia de envio de velocidades.
- `max_speed`: velocidad maxima por rueda en m/s.
- `ticks_per_revolution`: ticks de encoder por una vuelta completa de la rueda.
- `wheel_radius`: radio de la rueda en metros.
- `base_width`: distancia entre rueda izquierda y derecha.
- `cmd_vel_timeout`: tiempo maximo sin `cmd_vel` antes de mandar cero.
- `invert_left_motor`: invierte el signo enviado a M1.
- `invert_right_motor`: invierte el signo enviado a M2.

## Uso

Compilar:

```bash
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Arrancar robot en la Raspberry:

```bash
ros2 launch roboclaw_ros2 mobile_robot.launch.py port:=/dev/ttyACM0
```

Solo RoboClaw:

```bash
ros2 launch roboclaw_ros2 roboclaw_node.launch.py
```

Interfaz de control:

```bash
ros2 run interface_pc interface_pc
```

## Suposiciones

- `M1` es la rueda izquierda.
- `M2` es la rueda derecha.
- Si algun motor gira al reves, cambia `invert_left_motor` o `invert_right_motor` en `params.yaml`.
- `ticks_per_revolution` debe incluir la relacion de engranajes si el encoder esta en el eje del motor.
