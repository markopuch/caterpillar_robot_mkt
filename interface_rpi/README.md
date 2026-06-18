# interface_rpi

Pantalla de rostros para Raspberry Pi con monitor HDMI. Abre una ventana PyQt
fullscreen y reproduce secuencias PNG.

## Uso

```bash
ros2 run interface_rpi interface_rpi
```

Launch individual:

```bash
ros2 launch interface_rpi interface_rpi.launch.py
```

## Consume

| Topic | Tipo | Contenido |
| --- | --- | --- |
| `face_coms_topic` | `std_msgs/msg/String` | Nombre del rostro a mostrar. |

## Rostros

| Valor | Frames | Funcion |
| --- | --- | --- |
| `blink` | 5 | Rostro normal por defecto. |
| `smile` | 7 | Sonrisa. |
| `heart` | 25 | Corazones. |
| `fire` | 23 | Fuego. |
| `music` | 33 | Musica. |

## Salida Esperada

```text
[face_screen]: Loaded face sequences: blink, fire, heart, music, smile
```

## Prueba

```bash
ros2 topic pub --once /face_coms_topic std_msgs/msg/String "{data: 'heart'}"
```
