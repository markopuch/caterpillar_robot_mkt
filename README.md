# caterpillar_robot_mkt

Robot movil diferencial con RoboClaw y pantalla HDMI en Raspberry Pi para
rostros animados.

```text
interface_pc -> cmd_vel -> roboclaw_node -> RoboClaw
interface_pc -> face_coms_topic -> interface_rpi -> pantalla HDMI
```

## Instalacion

```bash
chmod +x install_raspberry.sh
./install_raspberry.sh
source install/setup.bash
```

Si el script agrega el usuario al grupo `dialout`, reinicia sesion o reinicia la
Raspberry antes de usar `/dev/ttyACM0`.

## Ejecucion Rapida

Robot en Raspberry:

```bash
ros2 launch roboclaw_ros2 mobile_robot.launch.py port:=/dev/ttyACM0
```

Interfaz de control:

```bash
ros2 run interface_pc interface_pc
```

Robot completo con interfaz en la misma Raspberry:

```bash
ros2 launch roboclaw_ros2 mobile_robot.launch.py start_control_gui:=true
```

## Paquetes

### `interface_pc`

Interfaz PyQt para mover el robot y cambiar rostros.

Ejecutable:

```bash
ros2 run interface_pc interface_pc
```

Publica:

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | `linear.x` y `angular.z` para la base diferencial. |
| `face_coms_topic` | `std_msgs/msg/String` | Nombre del rostro: `blink`, `smile`, `heart`, `fire`, `music`. |

Salidas visibles en la interfaz:

```text
cmd_vel: linear.x=+0.17 m/s, angular.z=+0.00 rad/s
face_coms_topic: smile
Estado Base: TX / STOP / WAIT
Estado Rostro: SENT / WAIT
```

Controles:

- Joystick y botones: adelante, atras, girar izquierda, girar derecha, STOP.
- Slider: limita velocidad.
- Rostros: Normal, Sonrisa, Corazon, Fuego, Musica.

### `interface_rpi`

Pantalla de rostro fullscreen para HDMI en Raspberry Pi.

Ejecutable:

```bash
ros2 run interface_rpi interface_rpi
```

Consume:

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `face_coms_topic` | `std_msgs/msg/String` | Rostro que se mostrara en pantalla. |

Rostros disponibles:

| Valor | Frames | Funcion |
| --- | --- | --- |
| `blink` | 5 | Rostro normal por defecto. |
| `smile` | 7 | Sonrisa. |
| `heart` | 25 | Corazones. |
| `fire` | 23 | Fuego. |
| `music` | 33 | Musica. |

Salida esperada:

```text
[face_screen]: Loaded face sequences: blink, fire, heart, music, smile
```

Prueba manual:

```bash
ros2 topic pub --once /face_coms_topic std_msgs/msg/String "{data: 'heart'}"
```

### `roboclaw_ros2`

Nodo minimo para convertir `cmd_vel` en velocidades para RoboClaw.

Ejecutable:

```bash
ros2 run roboclaw_ros2 roboclaw_node
```

Consume:

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | Velocidad lineal y angular del robot. |

Publica diagnostico:

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `roboclaw/cmd_speed/left` | `std_msgs/msg/Float32` | Velocidad izquierda en m/s. |
| `roboclaw/cmd_speed/right` | `std_msgs/msg/Float32` | Velocidad derecha en m/s. |
| `roboclaw/cmd_ticks/left` | `std_msgs/msg/Int32` | Setpoint izquierdo en ticks/s. |
| `roboclaw/cmd_ticks/right` | `std_msgs/msg/Int32` | Setpoint derecho en ticks/s. |

Calculo:

```text
left_mps  = linear.x - angular.z * base_width / 2
right_mps = linear.x + angular.z * base_width / 2
ticks_per_meter = ticks_per_revolution / (2 * pi * wheel_radius)
```

Salida esperada:

```text
[roboclaw_node]: RoboClaw speed bridge on /dev/ttyACM0, address 0x80
[roboclaw_node]: Connected to RoboClaw
```

Si no hay comandos recientes:

```text
[roboclaw_node]: No recent cmd_vel, commanding zero speed
```

## Parametros Minimos

Archivo:

```text
roboclaw_ros2/config/params.yaml
```

| Parametro | Uso |
| --- | --- |
| `port` | Puerto serial, normalmente `/dev/ttyACM0`. |
| `baud` | Baudrate del RoboClaw. |
| `address` | Direccion del RoboClaw, normalmente `128`. |
| `max_speed` | Velocidad maxima por lado en m/s. |
| `ticks_per_revolution` | Ticks por vuelta completa de rueda. |
| `wheel_radius` | Radio de rueda en metros. |
| `base_width` | Distancia entre ruedas izquierda y derecha. |
| `cmd_vel_timeout` | Tiempo sin comandos antes de detener. |
| `invert_left_motor` | Invierte M1 si gira al reves. |
| `invert_right_motor` | Invierte M2 si gira al reves. |

## Pruebas Rapidas

Mover:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

Detener:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

Cambiar rostro:

```bash
ros2 topic pub --once /face_coms_topic std_msgs/msg/String "{data: 'music'}"
```

## Suposiciones

- `M1` del RoboClaw: lado izquierdo.
- `M2` del RoboClaw: lado derecho.
- Pantalla conectada por HDMI a la Raspberry Pi.
- Rostros en `interface_rpi/interface_rpi/faces/<nombre>/<nombre>_<n>.png`.
