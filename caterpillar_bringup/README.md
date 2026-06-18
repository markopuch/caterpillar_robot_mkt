# caterpillar_bringup

Paquete solo de launch para arrancar el robot por grupos.

## Launchers

Robot: RoboClaw en `/dev/ttyACM0` + pantalla de rostros.

```bash
ros2 launch caterpillar_bringup robot.launch.py
```

Interface: solo interfaz PC.

```bash
ros2 launch caterpillar_bringup interface.launch.py
```

All: ejecuta `robot.launch.py` e `interface.launch.py`.

```bash
ros2 launch caterpillar_bringup all.launch.py
```
