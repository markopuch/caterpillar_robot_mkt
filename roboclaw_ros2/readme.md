# roboclaw_ros2

Nodo minimo para controlar una base diferencial con RoboClaw desde `cmd_vel`.

## Uso

```bash
ros2 run roboclaw_ros2 roboclaw_node
```

Con launch:

```bash
ros2 launch roboclaw_ros2 roboclaw_node.launch.py
```

## Consume

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | Velocidad lineal y angular. |

## Publica Diagnostico

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `roboclaw/cmd_speed/left` | `std_msgs/msg/Float32` | Velocidad izquierda en m/s. |
| `roboclaw/cmd_speed/right` | `std_msgs/msg/Float32` | Velocidad derecha en m/s. |
| `roboclaw/cmd_ticks/left` | `std_msgs/msg/Int32` | Setpoint izquierdo en ticks/s. |
| `roboclaw/cmd_ticks/right` | `std_msgs/msg/Int32` | Setpoint derecho en ticks/s. |

## Calculo

```text
left_mps  = linear.x - angular.z * base_width / 2
right_mps = linear.x + angular.z * base_width / 2
ticks_per_meter = ticks_per_revolution / (2 * pi * wheel_radius)
```

El comando enviado al RoboClaw es:

```text
SpeedM1M2(address, left_ticks, right_ticks)
```

## Parametros

Archivo: `config/params.yaml`

| Parametro | Uso |
| --- | --- |
| `port` | Puerto serial, normalmente `/dev/ttyACM0`. |
| `baud` | Baudrate. |
| `address` | Direccion del RoboClaw. |
| `max_speed` | Velocidad maxima por lado. |
| `ticks_per_revolution` | Ticks por vuelta de rueda. |
| `wheel_radius` | Radio de rueda. |
| `base_width` | Distancia entre ruedas. |
| `cmd_vel_timeout` | Tiempo sin comandos antes de detener. |
| `invert_left_motor` | Invierte M1. |
| `invert_right_motor` | Invierte M2. |

## Suposiciones

- `M1`: lado izquierdo.
- `M2`: lado derecho.
- Si un motor gira al reves, cambia `invert_left_motor` o `invert_right_motor`.
