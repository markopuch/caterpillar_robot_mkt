# interface_pc

Interfaz grafica PyQt para controlar el robot desde una PC o desde la misma
Raspberry.

## Uso

```bash
ros2 run interface_pc interface_pc
```

## Funcion

- Mueve la base con joystick o botones.
- En el joystick, los lados `GIRA IZQ` y `GIRA DER` cambian la velocidad
  relativa de las ruedas para girar.
- Limita la velocidad con un slider.
- Detiene el robot con `STOP`.
- Cambia el rostro mostrado en la pantalla HDMI.

## Publica

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | `linear.x` y `angular.z`. |
| `face_coms_topic` | `std_msgs/msg/String` | `blink`, `smile`, `heart`, `fire`, `music`. |

## Consume

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `roboclaw/cmd_speed/left` | `std_msgs/msg/Float32` | Velocidad actual mandada a M1. |
| `roboclaw/cmd_speed/right` | `std_msgs/msg/Float32` | Velocidad actual mandada a M2. |
| `roboclaw/cmd_ticks/left` | `std_msgs/msg/Int32` | Setpoint izquierdo en ticks/s. |
| `roboclaw/cmd_ticks/right` | `std_msgs/msg/Int32` | Setpoint derecho en ticks/s. |

## Salida Visible

```text
cmd_vel: linear.x=+0.17 m/s, angular.z=+0.00 rad/s
Motores: izq=+0.17 m/s (+1108 ticks/s), der=+0.17 m/s (+1108 ticks/s)
face_coms_topic: smile
Estado Base-roboclaw: CONECTADO / STOP / WAIT
Estado Rostro: SENT / WAIT
```

## Controles

- `Adelante`, `Atras`, `Girar izq`, `Girar der`: quedan activos en verde y
  se desactivan al volver a presionarlos.
- `STOP`: desactiva el boton activo y manda velocidad cero.
- Rostros: `Normal`, `Sonrisa`, `Corazon`, `Fuego`, `Musica`.
