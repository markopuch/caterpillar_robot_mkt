# caterpillar_robot_mkt

Robot movil diferencial con RoboClaw y pantalla HDMI para rostros animados.
El sistema esta preparado para ROS 2 Jazzy.

Desarrollado para un proyecto de la Universidad de Ingenieria y Tecnologia
(UTEC), Departamento de Mecatronica. Codigo desarrollado por Marko Puchuri.

```text
interface_pc -> cmd_vel -> roboclaw_node -> RoboClaw
interface_pc -> face_coms_topic -> interface_rpi -> pantalla HDMI
```

## Vista General

![Interfaz de control](docs/interface_pc.png)

La interfaz mueve la base diferencial, limita velocidad, detiene el robot y
envia rostros a la pantalla.

![Ejemplos de rostros](docs/faces_examples.png)

## Instalacion

```bash
cd /home/utec/robot_ws/src/caterpillar_robot_mkt
./install_ros2_jazzy.sh
./install_robot_dependencies.sh
./install_roboclaw_udev.sh
./build_robot.sh
source ../../install/setup.bash
```

Si el usuario fue agregado a `dialout`, reinicia sesion antes de usar
`/dev/ttyACM0`.

## Ejecucion

Robot en Raspberry:

```bash
./run_robot.sh
```

Interfaz de control:

```bash
./run_interface.sh
```

Robot e interfaz juntos:

```bash
./run_all.sh
```

## Paquetes

| Paquete | Funcion | README |
| --- | --- | --- |
| `interface_pc` | GUI para movimiento y rostros. | [`interface_pc/README.md`](interface_pc/README.md) |
| `interface_rpi` | Pantalla HDMI de rostros. | [`interface_rpi/README.md`](interface_rpi/README.md) |
| `roboclaw_ros2` | Puente `cmd_vel` a RoboClaw. | [`roboclaw_ros2/readme.md`](roboclaw_ros2/readme.md) |
| `caterpillar_bringup` | Launchers `robot`, `interface` y `all`. | [`caterpillar_bringup/README.md`](caterpillar_bringup/README.md) |

## Topics Principales

| Topic | Tipo | Uso |
| --- | --- | --- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | Movimiento diferencial. |
| `face_coms_topic` | `std_msgs/msg/String` | Seleccion de rostro. |
| `roboclaw/cmd_ticks/left` | `std_msgs/msg/Int32` | Diagnostico ticks lado izquierdo. |
| `roboclaw/cmd_ticks/right` | `std_msgs/msg/Int32` | Diagnostico ticks lado derecho. |

## Pruebas Rapidas

Mover:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

Detener:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

Rostro:

```bash
ros2 topic pub --once /face_coms_topic std_msgs/msg/String "{data: 'music'}"
```
