# interface_faces_web

Interfaz web de rostros para una tablet controlada desde ROS 2 mediante
`rosbridge_server`.

La tablet no ejecuta ROS. Solo abre una pagina web servida por este paquete.
La pagina se conecta por WebSocket a rosbridge y escucha el topic:

```bash
/face/expression
```

Tipo de mensaje:

```bash
std_msgs/msg/String
```

## Arquitectura

```text
ROS 2 topic /face/expression
        |
        v
rosbridge_server WebSocket :9090
        |
        v
Tablet en el mismo WiFi
        |
        v
http://IP_DEL_ROBOT:8080
```

## Compatibilidad

El codigo evita APIs exclusivas de una distribucion y esta pensado para:

- Laptop con Ubuntu 22.04 + ROS 2 Humble.
- Raspberry Pi con Ubuntu 24.04 + ROS 2 Jazzy.

Solo cambia el entorno ROS cargado:

```bash
source /opt/ros/humble/setup.bash
```

o:

```bash
source /opt/ros/jazzy/setup.bash
```

## Dependencias

En Humble:

```bash
sudo apt update
sudo apt install ros-humble-rosbridge-server
```

En Jazzy:

```bash
sudo apt update
sudo apt install ros-jazzy-rosbridge-server
```

El paquete `interface_rpi` debe estar en el mismo workspace o instalado en el
entorno ROS, porque sus assets de rostros se usan como fuente visual.

## Compilacion

Desde el workspace:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

En este proyecto, si el workspace es `/home/utec/robot_ws`:

```bash
cd /home/utec/robot_ws
colcon build --symlink-install
source install/setup.bash
```

## Ejecucion completa

```bash
ros2 launch interface_faces_web tablet_face.launch.py
```

Esto levanta:

- `rosbridge_server` en `0.0.0.0:9090`.
- El servidor web en `0.0.0.0:8080`.
- La WebApp de rostros.

Para activar tambien la demo:

```bash
ros2 launch interface_faces_web tablet_face.launch.py run_demo:=true
```

## URLs

Prueba local en la laptop:

```text
http://localhost:8080
```

Desde una tablet conectada al mismo WiFi:

```text
http://IP_DE_LA_LAPTOP:8080
```

Para ver la IP:

```bash
hostname -I
```

En Raspberry Pi:

```text
http://IP_DE_LA_RASPBERRY:8080
```

## Publicar rostros manualmente

```bash
ros2 topic pub /face/expression std_msgs/msg/String "{data: 'happy'}" --once
ros2 topic pub /face/expression std_msgs/msg/String "{data: 'talking'}" --once
ros2 topic pub /face/expression std_msgs/msg/String "{data: 'idle'}" --once
```

## Nodos de prueba

Demo ciclica:

```bash
ros2 run interface_faces_web face_demo_node
```

Publicar una expresion:

```bash
ros2 run interface_faces_web set_face_node happy
```

Publicar en otro topic:

```bash
ros2 run interface_faces_web set_face_node happy /otro/topic
```

## Parametros del launch

Puerto web:

```bash
ros2 launch interface_faces_web tablet_face.launch.py web_port:=8081
```

Puerto de rosbridge:

```bash
ros2 launch interface_faces_web tablet_face.launch.py rosbridge_port:=9091
```

Host del servidor web y address de rosbridge:

```bash
ros2 launch interface_faces_web tablet_face.launch.py host:=0.0.0.0 rosbridge_address:=0.0.0.0
```

Usar rostros desde una carpeta manual:

```bash
ros2 launch interface_faces_web tablet_face.launch.py faces_dir:=/ruta/a/los/rostros
```

## faces_dir

Si `faces_dir` esta vacio, el servidor intenta encontrar los recursos con:

```python
ament_index_python.packages.get_package_share_directory("interface_rpi")
```

Luego busca una carpeta `faces/` dentro del share directory de `interface_rpi`.

Si los assets de `interface_rpi` no estan instalados en `share`, no se modifica
`interface_rpi`. En ese caso usa:

```bash
ros2 launch interface_faces_web tablet_face.launch.py faces_dir:=/ruta/a/los/rostros
```

## Mapeo de rostros

El mapeo esta en:

```text
interface_faces_web/face_assets.py
```

Expresiones soportadas:

```text
idle, happy, sad, talking, listening, thinking, surprised, angry, sleeping, error
```

Tambien acepta los nombres usados por la interfaz PC:

```text
blink, smile, heart, fire, music
```

Estos aliases permiten que los botones de `interface_pc` cambien directamente
el rostro de la tablet publicando en `/face/expression`.

El servidor soporta estas extensiones:

```text
.png, .jpg, .jpeg, .svg, .gif, .webp, .json
```

Si una expresion no tiene recurso propio, se usa `idle` como fallback.

## Diagnostico

Ver diagnostico de rostros:

```bash
curl http://localhost:8080/api/faces
```

La respuesta indica:

- expresiones soportadas
- archivos encontrados
- URL usada por cada rostro
- extension
- fallback aplicado
- si se encontro `interface_rpi`
- si se usa `faces_dir`
- directorio activo
- errores o advertencias

Ver que el servidor web responde:

```bash
curl http://localhost:8080
```

Probar rosbridge manualmente:

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090 address:=0.0.0.0
```

Ver topic:

```bash
ros2 topic echo /face/expression
```

## Flujo en laptop con Humble

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install ros-humble-rosbridge-server

cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash

ros2 launch interface_faces_web tablet_face.launch.py
```

Abrir en la laptop:

```text
http://localhost:8080
```

Abrir desde tablet:

```text
http://IP_DE_LA_LAPTOP:8080
```

Publicar:

```bash
ros2 topic pub /face/expression std_msgs/msg/String "{data: 'happy'}" --once
```

## Flujo en Raspberry Pi con Jazzy

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-jazzy-rosbridge-server

cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash

ros2 launch interface_faces_web tablet_face.launch.py
```

Abrir desde la tablet:

```text
http://IP_DE_LA_RASPBERRY:8080
```

Publicar:

```bash
ros2 topic pub /face/expression std_msgs/msg/String "{data: 'happy'}" --once
```

## Troubleshooting

- La tablet no carga la pagina: verifica que tablet y laptop/Raspberry esten en
  la misma red WiFi y usa `hostname -I` para confirmar la IP.
- Carga en `localhost` pero no desde tablet: confirma que el launch usa
  `host:=0.0.0.0`.
- La pagina carga pero no cambia el rostro: confirma que rosbridge esta
  corriendo en `0.0.0.0:9090`.
- El puerto 8080 no responde: revisa si otro proceso usa ese puerto o cambia
  `web_port:=8081`.
- El puerto 9090 no responde: instala `rosbridge_server` y revisa
  `rosbridge_port`.
- No se encuentra `interface_rpi`: compila y carga el workspace con
  `source install/setup.bash`.
- No se encuentran rostros: revisa `curl http://localhost:8080/api/faces` y usa
  `faces_dir` si los assets no estan instalados.
- `/faces/...` devuelve 404: revisa el mapeo en `face_assets.py` y la respuesta
  de `/api/faces`.
- WebSocket falla desde tablet: revisa que `rosbridge_address:=0.0.0.0`, que el
  firewall no bloquee el puerto 9090 y que la IP sea correcta.
- Si algo funciona en Humble pero no en Jazzy, confirma que instalaste
  `ros-jazzy-rosbridge-server` y que cargaste `/opt/ros/jazzy/setup.bash`.
