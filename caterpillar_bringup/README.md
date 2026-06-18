# caterpillar_bringup

Paquete solo de launch para arrancar el robot por grupos.

## Launchers

Robot: RoboClaw en `/dev/ttyACM0` + pantalla de rostros.

```bash
ros2 launch caterpillar_bringup robot.launch.py
```

Interface: interfaz PC + WebApp de rostros para tablet.

```bash
ros2 launch caterpillar_bringup interface.launch.py
```

La tablet puede abrir:

```text
http://IP_DEL_ROBOT:8080
```

All: ejecuta `robot.launch.py` e `interface.launch.py`.

```bash
ros2 launch caterpillar_bringup all.launch.py
```
