# MES-BOT

## English

### Overview

MES-BOT is an educational robotics application developed at the Faculty of Engineering of Universidad de La Sabana, Colombia. A teacher defines a route on a grid, a student gives directional commands, and a differential-drive robot executes the route while the application records the result.

Straight movements use a nominal target of 200 mm. Turns use a nominal target of 90 degrees. The effective accuracy depends on the mechanical condition of the robot and its calibration.

### System architecture

The reference implementation runs on Arduino UNO Q:

- The microcontroller controls the motors, wheel encoders, BNO085 IMU, INA219 battery monitor, and LED matrix.
- The Linux processor runs the web interface, camera processing, local voice model, PDF generation, email delivery, and SQLite storage.

The BNO085 is connected through Qwiic. A powered USB-C hub or adapter provides the HDMI output and connections for a keyboard and mouse; the UNO Q does not have a dedicated HDMI connector.

### Main workflow

1. Create a trajectory and generate its QR card.
2. Create or select a student profile.
3. Place the robot on the initial cell and load the trajectory.
4. Execute the route by voice or with the manual controls.
5. Review and record the completed session.

### First deployment

Configure `.env` before running `setup.sh`, packaging the deployment ZIP, importing the project into Arduino App Lab, or starting MES-BOT for the first time:

1. Copy `.env.example` to `.env`.
2. Ask the project developer for the deployment-specific email values.
3. Set `EMAIL_USER`, `EMAIL_PASS`, and `EMAIL_FROM` in `.env`.
4. Keep `.env` and every deployment ZIP that contains it outside public repositories.

These variables support trajectory PDF delivery by email. MES-BOT can run without them, but automated email delivery will remain unavailable.

After configuring `.env`:

1. Package the complete project, including the configured `.env`, as a private ZIP for the target device.
2. Connect the UNO Q to the Internet for initial provisioning.
3. Import the project into Arduino App Lab and configure the device name and Linux device password.
4. Run `setup.sh` from the deployed project directory on the UNO Q.
5. Start MES-BOT from App Lab and wait for sketch compilation, Python provisioning, and container startup to finish.

Initial provisioning requires Internet access. After provisioning, the Edge Impulse model in `assets/models/kids.eim` recognizes five Spanish commands locally: `adelante`, `atras`, `izquierda`, `derecha`, and `stop`. When Internet access is available, Google Speech Recognition can act as a fallback and map recognized Spanish or English words to the same robot commands.

### Access

The web interface is available from the UNO Q or another device on the same local network:

- `http://mes-bot:7000`
- `http://<robot-ip>:7000`
- `http://localhost:7000` on the UNO Q

The default web-interface password is `M123`. It is separate from the Linux device password selected during initial UNO Q configuration.

### Documentation and license

The complete bilingual installation, calibration, and operating instructions are in [userManual.md](userManual.md). Third-party components and license notices are listed in [thirdPartyNotices.txt](thirdPartyNotices.txt).

MES-BOT source code is distributed under the Mozilla Public License 2.0. The full official license text is in [LICENSE](LICENSE).

## Español

### Descripción general

MES-BOT es una aplicación de robótica educativa desarrollada en la Facultad de Ingeniería de la Universidad de La Sabana, Colombia. El docente define una trayectoria sobre una cuadrícula, el estudiante da instrucciones de dirección y un robot de tracción diferencial ejecuta la ruta mientras la aplicación registra el resultado.

Los movimientos rectos utilizan un objetivo nominal de 200 mm. Los giros utilizan un objetivo nominal de 90 grados. La precisión efectiva depende del estado mecánico del robot y de su calibración.

### Arquitectura del sistema

La implementación de referencia funciona sobre Arduino UNO Q:

- El microcontrolador controla los motores, los encoders de las ruedas, la IMU BNO085, el monitor de batería INA219 y la matriz LED.
- El procesador Linux ejecuta la interfaz web, el procesamiento de cámara, el modelo local de voz, la generación de PDF, el envío de correo y el almacenamiento SQLite.

El BNO085 se conecta mediante Qwiic. Un concentrador o adaptador USB-C con alimentación proporciona la salida HDMI y las conexiones para teclado y mouse; la UNO Q no tiene un conector HDMI dedicado.

### Flujo principal

1. Crear una trayectoria y generar su tarjeta QR.
2. Crear o seleccionar el perfil de un estudiante.
3. Ubicar el robot en la casilla inicial y cargar la trayectoria.
4. Ejecutar la ruta por voz o con los controles manuales.
5. Revisar y registrar la sesión terminada.

### Primera instalación

Configure `.env` antes de ejecutar `setup.sh`, crear el ZIP de instalación, importar el proyecto en Arduino App Lab o iniciar MES-BOT por primera vez:

1. Copie `.env.example` como `.env`.
2. Solicite al desarrollador los valores de correo correspondientes a la instalación.
3. Defina `EMAIL_USER`, `EMAIL_PASS` y `EMAIL_FROM` en `.env`.
4. Mantenga `.env` y cualquier ZIP de instalación que lo contenga fuera de repositorios públicos.

Estas variables permiten enviar por correo los PDF de las trayectorias. MES-BOT puede funcionar sin ellas, pero el envío automático de correos no estará disponible.

Después de configurar `.env`:

1. Empaquete el proyecto completo, incluido el `.env` configurado, como un ZIP privado para el dispositivo de destino.
2. Conecte la UNO Q a Internet para el aprovisionamiento inicial.
3. Importe el proyecto en Arduino App Lab y configure el nombre del dispositivo y la contraseña de Linux.
4. Ejecute `setup.sh` desde el directorio del proyecto instalado en la UNO Q.
5. Inicie MES-BOT desde App Lab y espere a que terminen la compilación del sketch, el aprovisionamiento de Python y el inicio de los contenedores.

El aprovisionamiento inicial necesita acceso a Internet. Después, el modelo de Edge Impulse incluido en `assets/models/kids.eim` reconoce localmente cinco comandos en español: `adelante`, `atras`, `izquierda`, `derecha` y `stop`. Cuando hay conexión a Internet, Google Speech Recognition puede funcionar como alternativa y asociar palabras reconocidas en español o inglés con los mismos comandos del robot.

### Acceso

La interfaz web está disponible desde la UNO Q o desde otro equipo conectado a la misma red local:

- `http://mes-bot:7000`
- `http://<robot-ip>:7000`
- `http://localhost:7000` desde la UNO Q

La contraseña predeterminada de la interfaz web es `M123`. Es independiente de la contraseña de Linux elegida durante la configuración inicial de la UNO Q.

### Documentación y licencia

Las instrucciones bilingües completas de instalación, calibración y operación están en [userManual.md](userManual.md). Los componentes de terceros y sus avisos de licencia están enumerados en [thirdPartyNotices.txt](thirdPartyNotices.txt).

El código fuente de MES-BOT se distribuye bajo Mozilla Public License 2.0. El texto oficial completo de la licencia está en [LICENSE](LICENSE).
