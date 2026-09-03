# MES-BOT — Comprehensive User Manual / Manual de Usuario

---

### Language Selection / Selección de Idioma
* 🇺🇸 **[English User Manual](#english-user-manual)**
  1. [System Overview & Pedagogical Purpose](#1-system-overview--pedagogical-purpose)
  2. [Deployment Option A: Official Robot Target (Arduino Uno Q)](#2-deployment-option-a-official-robot-target-arduino-uno-q)
  3. [Deployment Option B: Alternative / PC Environment (Experimental)](#3-deployment-option-b-alternative--pc-environment-experimental)
  4. [Display & Connection Modes (Offline Operation)](#4-display--connection-modes-offline-operation)
  5. [Password Management & Security](#5-password-management--security)
  6. [Classroom Workflow & Step-by-Step Operation](#6-classroom-workflow--step-by-step-operation)
     * [6.1 Trajectories: Matrix Design & QR Generation](#61-trajectories-matrix-design--qr-generation)
     * [6.2 Players: Avatar & Profile Customization](#62-players-avatar--profile-customization)
     * [6.3 The Game: Execution, Voice Commands & Manual Driving](#63-the-game-execution-voice-commands--manual-driving)
     * [6.4 Historical Progress Tracking & Analytics](#64-historical-progress-tracking--analytics)
  7. [Troubleshooting & Diagnostics](#7-troubleshooting--diagnostics)
* 🇪🇸 **[Manual de Usuario en Español](#manual-de-usuario-español)**
  1. [Descripción General y Propósito Pedagógico](#1-descripción-general-y-propósito-pedagógico)
  2. [Opción de Despliegue A: Robot Oficial (Arduino Uno Q)](#2-opción-de-despliegue-a-robot-oficial-arduino-uno-q)
  3. [Opción de Despliegue B: Plataforma Alternativa / PC (Experimental)](#3-opción-de-despliegue-b-plataforma-alternativa--pc-experimental)
  4. [Modos de Pantalla y Conexión (Uso Sin Internet)](#4-modos-de-pantalla-y-conexión-uso-sin-internet)
  5. [Gestión de Contraseñas y Seguridad](#5-gestión-de-contraseñas-y-seguridad)
  6. [Flujo de Trabajo en el Aula Paso a Paso](#6-flujo-de-trabajo-en-el-aula-paso-a-paso)
     * [6.1 Trayectorias: Diseño en Matriz y Creación de QR](#61-trayectorias-diseño-en-matriz-y-creación-de-qr)
     * [6.2 Jugadores: Personalización de Avatar y Perfiles](#62-jugadores-personalización-de-avatar-y-perfiles)
     * [6.3 El Juego: Ejecución, Comandos de Voz y Conducción Manual](#63-el-juego-ejecución-comandos-de-voz-y-conducción-manual)
     * [6.4 Seguimiento Histórico y Analítica de Progreso](#64-seguimiento-histórico-y-analítica-de-progreso)
  7. [Solución de Problemas y Diagnóstico](#7-solución-de-problemas-y-diagnóstico)

---

# English User Manual

## 1. System Overview & Pedagogical Purpose

**MES-BOT** (*Sistema de Enseñanza Métrico-Espacial y Plataforma Robótica*) is an interactive educational robotics platform developed at the Faculty of Engineering of **Universidad de La Sabana** (Bogotá, Colombia). Its mission is to support the development of metric-spatial thinking during early childhood education.

### Learning Through Tangible Play
Spatial concepts such as orientation, relative distance, angles of rotation, and directional vocabulary (*forward*, *backward*, *left*, *right*) are often difficult for young children to grasp through static textbooks or two-dimensional computer simulations. MES-BOT anchors these concepts in the physical classroom through movement, observation, auditory interaction, and playful collaboration:
* **Physical Floor Grid:** Children interact on a tangible grid mat laid out on the classroom floor or table.
* **Voice-Guided Control:** Wearing a lightweight lapel microphone, children speak clear directional commands to guide their robot from square to square.
* **Immediate Auditory and Physical Feedback:** When a command matches the planned route, the robot executes the motion and sounds an affirmative chime. When a command does not match, the robot remains stopped and the interface records the mistake.
* **Identity and Engagement:** Children create and customize their own hero avatars and colors, turning abstract metric challenges into exciting storytelling adventures.

### Classroom Roles
Following the workflow model in `assets/common/role_workflow.pdf`:
1. **Teacher / Facilitator:** Prepares the curriculum, configures the step sequence in the Trajectories matrix, prints physical QR cards, manages student profiles, and monitors learning runs.
2. **Student:** Receives the configured robot, personalizes their hero avatar, clips on the lapel microphone, speaks directional commands, and uses manual arrow keys when assistance is needed.

---

## 2. Deployment Option A: Official Robot Target (Arduino Uno Q)

The primary hardware target for MES-BOT is the **Arduino Uno Q** board, which pairs a real-time microcontroller core (running Zephyr RTOS) with an embedded microprocessor unit (running Linux).

### Hardware Architecture
* **MCU (Zephyr RTOS Core):** Executes `sketch/sketch.ino`. Manages motor drivers (PWM), quadrature wheel encoders, the onboard LED matrix, the BNO085 IMU through the SparkFun BNO080-compatible library, and the Adafruit INA219 sensor for 4S battery voltage monitoring. It exposes control primitives through `Arduino_RouterBridge` (RPC Lite).
* **MPU (Linux Core):** Executes `python/main.py` orchestrated by Arduino App Lab bricks (`app.yaml`). Handles downward computer vision QR code reading, voice keyword spotting (`kids.eim` model), SQLite data storage, and the web interface.

### Step 1: Prepare the Project Before Setup

Complete this configuration before running `setup.sh`, creating the deployment ZIP, importing the project into App Lab, or starting MES-BOT:

1. In the project root, copy `.env.example` to a new file named `.env`.
2. Ask the project developer for the deployment-specific values of `EMAIL_USER`, `EMAIL_PASS`, and `EMAIL_FROM`.
3. Enter those values in `.env` without adding quotes unless the provided value includes them.
4. Keep `.env` private. It is excluded by `.gitignore` and must not be committed or placed in a public ZIP.
5. The private ZIP used to deploy the configured robot must contain `.env` at its root so the trajectory PDF email function can use the InfoSeed mail account. A public source ZIP must contain only `.env.example`.

### Step 2: First-Time UNO Q Installation

> **Important:** An active internet connection is required during the first installation so App Lab can download containers, Arduino libraries, system packages, and Python dependencies. After this setup, the local `kids.eim` model and core robot functions can operate without Internet. When Internet access is available, the application can also use its Google Speech Recognition fallback.

1. Connect the Arduino Uno Q to power and connect it to a network with Internet access.
2. In Arduino App Lab, configure the UNO Q device name and Linux device password.
3. Import the private deployment ZIP containing the configured `.env`.
4. After the project is available on the UNO Q, open an SSH or App Lab terminal session and navigate to its deployed project directory.
5. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   The script updates package lists, installs required Linux packages (`portaudio19-dev`, `alsa-utils`, `sqlite3`, `ffmpeg`), and downloads Python libraries (`opencv-python-headless`, `pyzbar`, `flask`, `flask-socketio`, `eventlet`, `Adafruit-Blinka`, etc.).
6. Confirm that the script exits with:
   ```text
   [OK] MES-BOT environment is CLEAN and READY.
   ```
7. Return to App Lab and start MES-BOT. App Lab will:
   * Compile and flash the MCU sketch (`sketch/sketch.ino`).
   * Provision the Python environment and required bricks.
   * Start the Linux container and launch the App Lab bricks defined in `app.yaml`.

---

## 3. Deployment Option B: Alternative / PC Environment (Experimental)

> **Status Notice:** This deployment method is **theoretical and has yet to be physically validated in practical testing**. Because the project architecture decouples the educational web GUI from the physical microcontroller, running the web dashboard and Python backend on a standard PC, laptop, or generic Linux/macOS board is architecturally supported, but proceed knowing adjustments may be needed.

Before starting the Python backend on a PC, complete the same `.env.example` to `.env` preparation described in Step 1. Email delivery requires the three InfoSeed email values; a local test that does not send email may leave them empty.

### How the Decoupled Layer Works
The user interface consists of standard HTML, CSS, JavaScript, and Socket.IO files located in `assets/`. It communicates with the Python backend via REST API requests (`/list_users`, `/create_trajectory`, `/record_game`) and Socket.IO events.

In an environment without the physical Arduino Uno Q board:

1. **Microcontroller Bridge Simulation:**
   * Calls to `Bridge.call("move_forward")`, `Bridge.call("get_state")`, and `Bridge.call("init_robot")` can be wrapped with a software shim that outputs motor actions to the console and returns simulated state objects:
     ```json
     {
       "mode": "IDLE",
       "macro_mode": "NONE",
       "bno_ok": 1,
       "ina_ok": 1,
       "step_heading_result": "COMPLETED",
       "battery_v": 15.2,
       "battery_percent_est": 90
     }
     ```
2. **Camera Requirement & The Undetected Camera Warning:**
   * On the official Arduino target, if no USB camera is plugged in, the `CameraCodeDetection` brick fails to start, triggering a yellow warning banner (`DEVICE NOT DETECTED: Camera`).
   * On a PC, you can connect any standard USB webcam via OpenCV.
   * **Bypassing the camera entirely in software:** You do not need a camera to test trajectories. You can mount any trajectory directly using the backend API:
     * **Endpoint:** `POST /set_active_trajectory`
     * **Body (JSON):** `{"id": 1}` *(replace 1 with your trajectory ID)*
     * This loads the entire step sequence directly into the active game session without requiring a downward camera scan.
3. **Database:**
   * Uses standard SQLite (`data/frames.db` and `data/code-scanner.db`), fully portable across Windows, macOS, and Linux.

---

## 4. Display & Connection Modes (Offline Operation)

Once installed, **MES-BOT does not require an active internet connection**. You can run and display the system in three different ways:

### Mode 1: Standalone Robot with HDMI Screen (Zero Network Setup)
The Arduino Uno Q provides video through DisplayPort Alt Mode on its USB-C connection. HDMI requires a powered USB-C hub or dongle with HDMI output.
* Connect the powered USB-C hub to the UNO Q, then connect the monitor or TV, USB mouse, and keyboard to the hub.
* When the board powers on, **Arduino App Lab launches directly on the robot, and the web browser opens automatically right on the robot's screen** pointing to `http://localhost:7000`.
* **Advantage:** Completely self-contained. No laptop, no tablet, no Wi-Fi, and no router needed.

### Mode 2: Local Laptop or Smartphone Hotspot
* Turn on the personal Wi-Fi Hotspot on your laptop or smartphone.
* **You do not need cellular data or internet access.** Cellular data can be turned **OFF**; the hotspot only provides a private local Wi-Fi signal (LAN).
* Connect the robot and your laptop or tablet to this shared hotspot network.
* Open your browser and navigate to:
  ```text
  http://mes-bot:7000
  ```
  *(Or use the local IP assigned to the robot: `http://<robot-ip>:7000`)*.

### Mode 3: Classroom Wi-Fi Router (Offline Local Network)
* Connect the robot and your classroom tablet or computer to the school's local Wi-Fi router.
* Even if the router has no internet connectivity, the local network allows full communication.
* Open `http://mes-bot:7000` *(or `http://<robot-ip>:7000`)* in any browser.

---

## 5. Password Management & Security

* **Device Password:** During the initial UNO Q setup, the administrator creates the Linux device password used for SSH and system administration.
* **Default Web Password:** `M123`
* **How to Change the Password:**
  The web password controls the MES-BOT access screen and is separate from the Linux device password. It does not replace device or network security. To set a custom web password:
  1. Open the file `assets/index.html` in any code or text editor.
  2. Locate line 329:
     ```javascript
     if (pwd === 'M123') {
     ```
  3. Replace `'M123'` with your desired password (for example, `'School2026'`):
     ```javascript
     if (pwd === 'School2026') {
     ```
  4. Save the file and reload the browser page.

---

## 6. Classroom Workflow & Step-by-Step Operation

The MES-BOT console is organized into three primary modules:

```
┌────────────────────────────────────────────────────────┐
│                   MES-BOT DASHBOARD                    │
├─────────────────┬──────────────────┬───────────────────┤
│  TRAYECTORIAS   │    JUGADORES     │       JUEGO       │
│  (Trajectories) │    (Players)     │    (Game Play)    │
└─────────────────┴──────────────────┴───────────────────┘
```

---

### 6.1 Trajectories: Matrix Design & QR Generation

The Trajectories module (`assets/trayectorias/`) allows teachers to design routes on a coordinate grid matching the physical classroom floor mat.

#### Design Rules
1. **Consecutive Cells Only:** Click only cells that are immediately adjacent horizontally or vertically. Diagonal jumps are not permitted because the robot moves in orthogonal steps (Forward, Backward, Turn Left, Turn Right).
2. **No Repeated Cells:** A trajectory cannot visit the same cell twice. Each step must be a unique cell to prevent infinite loops.

#### Step-by-Step Creation
1. From the main dashboard, click **TRAYECTORIAS**.
2. Click **New Trajectory** (`+`) in the right sidebar and enter a name (e.g., *Level 1 - Straight Path* or *ZigZag Challenge*).
3. On the grid matrix (8 rows × 13 columns), click the starting square (Frame 1).
4. Click the next consecutive square (Frame 2). The software computes the relative movement vector automatically:
   * Upward step: **FORWARD**
   * Downward step: **BACKWARD**
   * Rightward step: **RIGHT**
   * Leftward step: **LEFT**
5. Continue clicking consecutive squares until the route is complete.
6. Each step is automatically saved into the local SQLite database (`frames.db`). You can click **Play Animation** to preview the route.

#### Printing QR Cards to PDF
1. In the right sidebar, check the boxes for the trajectories you want to print.
2. Select your preferred **PDF Layout**:
   * `2 x 2`: 4 large cards per page (ideal for large floor mats).
   * `2 x 3` (Default): 6 cards per page.
   * `3 x 3`: 9 smaller cards per page (ideal for tabletop mats).
3. Click **Bulk PDF** to generate the printable sheet.
   *(Optional: If SMTP email is configured in `.env`, click **Send Email** to dispatch the PDF directly to a teacher's inbox).*
4. Each printed card displays the trajectory name, ID, matrix diagram, cutting guides, and the QR code encoded with `LOAD_TRAJECTORY:<ID>`.
5. Print the PDF, cut out the cards, and place them carefully in the **center of the corresponding grid squares** on the floor.

---

### 6.2 Players: Avatar & Profile Customization

The Players module (`assets/usuarios/`) allows children to build their individual game profiles.

#### Creating a Player Profile
1. From the main dashboard, click **JUGADORES**.
2. Click the round **Add Player (+)** button in the bottom right corner.
3. The **Character Creator** opens:
   * **Name or Nickname:** The child types their name into the text box (up to 12 characters).
   * **Hero Avatar:** Choose from 15 illustrated characters:
     * *Robot, Astronaut, Ninja, Superhero, Rocket, Wizard, Monster, Dragon, Ghost, Graduate, Spy, Cat, Dog, Spider, Meteor.*
   * **Power Color:** Select a favorite theme color from 9 color circles or use the full color picker.
   * **Magic Dice Button:** Clicking the dice randomly generates a fun avatar, color, and name combination.
4. Click **I'M READY!** (`¡ESTOY LISTO!`). Confetti bursts across the screen, and the profile is saved.
5. The player's card now appears on screen showing their avatar, color border, games played, games won, and win rate percentage.

---

### 6.3 The Game: Execution, Voice Commands & Manual Driving

The Game module (`assets/motor/`) brings the physical robot, the student, and the evaluation system together.

#### Physical Setup
1. Power on the robot and verify battery voltage is healthy (above 14.5V on the HUD).
2. Place the robot on the floor grid directly over the **Starting Cell's QR Code**.
3. Ensure the downward-facing camera lens has an unobstructed view of the QR card.

#### Game Dashboard Overview
1. From the main dashboard, click **JUEGO**.
2. In the top dropdown, select the student who is about to play.
3. Observe the dashboard panels:
   * **Live Video Feed:** Displays the downward camera stream in real time.
   * **Trajectory Status:** When the camera reads the QR card, it triggers `LOAD_TRAJECTORY:<ID>`. The system sounds an audible chime, sets the progress bar to `Step 0 / N`, and displays the required command sequence (e.g., `F → R → F`).
   * **Code Scanner:** Shows the decoded QR string and timestamp.
   * **Voice Interface:** Displays recognized speech words in real time.

#### Voice Commands (Offline Model: `kids.eim`)
The child wears the lapel microphone and speaks directional commands clearly.

> **Important Note on Voice Language:** The onboard `kids.eim` model was trained with recordings from Spanish-speaking children and recognizes five commands locally without Internet. English command aliases exist in the application, but the EIM model was not trained with English-speaking children. When Internet access is available, the Google Speech Recognition fallback may recognize additional Spanish or English phrases and map them to the same actions. Audio processed by that online fallback is transmitted to Google; disconnect Internet access when voice processing must remain entirely local.

| Voice Command (Spoken) | Robot Action | Motion Description |
| :--- | :--- | :--- |
| **ADELANTE** | FORWARD | Moves forward 20 cm to the next grid cell |
| **ATRÁS** | BACKWARD | Moves backward 20 cm to the previous grid cell |
| **IZQUIERDA** | LEFT | Turns 90° to the left (counter-clockwise) |
| **DERECHA** | RIGHT | Turns 90° to the right (clockwise) |
| **STOP** | STOP | Immediately stops the robot's motion |

#### Step Validation & Mistake Logging
* When the spoken command matches the expected next step:
  * The robot executes the physical motion (moving forward 20 cm or turning 90°).
  * The progress counter advances (`Step 1 / N`).
  * A success chime plays.
* When the spoken command contradicts the planned path:
  * The robot pauses safely in place.
  * The mistake counter increments (`Mistakes: 1`).

#### Manual Driving Fallback
If the classroom is noisy or the child needs assistance:
* Click the on-screen direction buttons: **Forward**, **Backward**, **Left**, **Right**, and **Stop**.
* Or use standard keyboard shortcuts on the connected computer:
  * `W` or `↑` (Up Arrow): Move Forward
  * `S` or `↓` (Down Arrow): Move Backward
  * `A` or `←` (Left Arrow): Turn 90° Left
  * `D` or `→` (Right Arrow): Turn 90° Right
  * `Space` or `Escape`: Emergency Stop

#### Evaluating and Saving the Session
1. When the robot reaches the final destination cell, the progress bar turns green and shows **COMPLETED**.
2. Click **Evaluate** (**Evaluar**):
   * Full completion: displays **WIN! All steps completed!**
   * Early finish: displays **Incomplete steps**.
3. Click **Record Result** (**Registrar**):
   * Saves the game session to SQLite with user ID, trajectory ID, mistake count, total steps, duration in seconds, and victory status.
   * Updates the student's profile statistics immediately.

---

### 6.4 Historical Progress Tracking & Analytics

Teachers can track longitudinal learning gains and spatial concept retention over time:

1. Return to **JUGADORES**.
2. Locate the student's card.
3. Click the **History Icon** (clock icon `fa-history`) in the card header.
4. The **Game History Modal** displays a chronological log of every game session:
   * Date and exact time.
   * Trajectory name.
   * Steps completed vs. total planned steps.
   * Number of mistakes made.
   * Total elapsed time in seconds.
   * Win / Loss badge.
5. Use this data during pedagogical evaluations to assess whether a child has overcome directional confusion (e.g., left vs. right) or improved spatial sequencing over multiple weeks.

---

## 7. Troubleshooting & Diagnostics

### Missing Peripheral Warnings
If a yellow banner appears reading `DEVICE NOT DETECTED`:
* **Camera:** Ensure the USB camera cable is firmly plugged into the host port. In PC testing mode without a camera, mount trajectories via `POST /set_active_trajectory`.
* **Microphone:** Check the 3.5mm or USB microphone connection.
* **MCU Connection:** Indicates that the Linux layer cannot communicate with the Zephyr sketch. Power cycle the robot or verify that `sketch.ino` is running.
* **Database:** Confirm write permissions for the `data/` folder.

### IMU Drift / Calibration ("Zero Pose")
If the robot veers during straight lines or turns inaccurate angles:
1. Open the calibration screen at `http://mes-bot:7000/calibration/` (or `http://localhost:7000/calibration/` if using the HDMI screen).
2. Place the robot straight on a level floor.
3. Click **Zero Pose** to re-baseline the BNO085 yaw angle.

---
---

# Manual de Usuario en Español

## 1. Descripción General y Propósito Pedagógico

**MES-BOT** (*Sistema de Enseñanza Métrico-Espacial y Plataforma Robótica*) es una plataforma robótica interactiva desarrollada en la Facultad de Ingeniería de la **Universidad de La Sabana** (Bogotá, Colombia). Su objetivo es fortalecer el pensamiento métrico-espacial en la educación infantil y básica primaria.

### Aprendizaje a Través del Juego Tangible
Los conceptos espaciales como orientación, distancia relativa, ángulos de giro y vocabulario de dirección (*adelante*, *atrás*, *izquierda*, *derecha*) suelen ser difíciles de asimilar para niños pequeños cuando se presentan en textos estáticos o pantallas abstractas. MES-BOT traslada estos conceptos al aula física mediante el movimiento, la observación, la interacción por voz y el juego colaborativo:
* **Tapete de Cuadrícula en el Suelo:** Los niños interactúan sobre un plano cuadriculado tangible en el suelo o en una mesa.
* **Control Guiado por Voz:** Con un micrófono de solapa ligero, el estudiante pronuncia órdenes directas para guiar a su robot de casilla en casilla.
* **Retroalimentación Física y Auditiva Inmediata:** Si la orden coincide con la ruta planeada, el robot realiza el movimiento y emite un tono de confirmación. Si la orden no coincide, el robot permanece detenido y la interfaz registra el error.
* **Identidad y Motivación:** Cada niño crea su héroe, elige colores y avatares, convirtiendo los desafíos matemáticos y espaciales en una aventura de exploración.

### Roles en el Aula
Siguiendo el flujo pedagógico documentado en `assets/common/role_workflow.pdf`:
1. **Profesor / Facilitador:** Prepara la sesión, diseña las secuencias de pasos en la matriz de Trayectorias, imprime las fichas con códigos QR, administra los perfiles de los niños y supervisa la evaluación.
2. **Estudiante / Niño:** Recibe el robot, personaliza su avatar, se coloca el micrófono de solapa, da las instrucciones verbales y utiliza los botones manuales como apoyo cuando sea necesario.

---

## 2. Opción de Despliegue A: Robot Oficial (Arduino Uno Q)

La plataforma oficial de MES-BOT opera sobre la placa **Arduino Uno Q**, que integra un microcontrolador de tiempo real (con Zephyr RTOS) y un microprocesador con sistema operativo Linux.

### Estructura de Hardware
* **MCU (Núcleo Zephyr RTOS):** Ejecuta `sketch/sketch.ino`. Controla los motores DC (PWM), los encoders ópticos de cuadratura, la matriz de LEDs frontal, la IMU BNO085 mediante la biblioteca compatible SparkFun BNO080 y el sensor Adafruit INA219 para monitorear la batería 4S. Expone funciones de control mediante `Arduino_RouterBridge` (RPC Lite).
* **MPU (Núcleo Linux):** Ejecuta `python/main.py` mediante los bloques (bricks) de Arduino App Lab (`app.yaml`). Procesa la visión artificial (lectura de QR), el reconocimiento de voz (`kids.eim`), la base de datos SQLite y sirve la aplicación web.

### Paso 1: Preparar el Proyecto Antes de la Instalación

Complete esta configuración antes de ejecutar `setup.sh`, crear el ZIP de despliegue, importar el proyecto en App Lab o iniciar MES-BOT:

1. En la raíz del proyecto, copie `.env.example` en un archivo nuevo llamado `.env`.
2. Solicite al desarrollador los valores específicos de despliegue para `EMAIL_USER`, `EMAIL_PASS` y `EMAIL_FROM`.
3. Escriba esos valores en `.env` sin agregar comillas, excepto si el valor proporcionado las incluye.
4. Mantenga `.env` en privado. El archivo está excluido por `.gitignore` y no debe incluirse en Git ni en un ZIP público.
5. El ZIP privado utilizado para desplegar el robot configurado debe contener `.env` en la raíz para que la función de envío de PDF utilice la cuenta de correo de InfoSeed. Un ZIP público del código fuente debe incluir únicamente `.env.example`.

### Paso 2: Primera Instalación en el UNO Q

> **Muy Importante:** La conexión a Internet se requiere durante la primera instalación para que App Lab descargue contenedores, bibliotecas Arduino, paquetes del sistema y dependencias Python. Después, el modelo local `kids.eim` y las funciones principales del robot pueden operar sin Internet. Cuando existe conexión, la aplicación también puede utilizar el reconocimiento de voz de Google como alternativa.

1. Conecte el Arduino Uno Q a la alimentación y a una red con acceso a Internet.
2. En Arduino App Lab, configure el nombre del dispositivo UNO Q y la contraseña Linux.
3. Importe el ZIP privado de despliegue que contiene el archivo `.env` configurado.
4. Cuando el proyecto esté disponible en el UNO Q, abra una terminal por SSH o desde App Lab y diríjase a la carpeta desplegada del proyecto.
5. Ejecute el script de instalación:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   Este script instala paquetes del sistema (`portaudio19-dev`, `alsa-utils`, `sqlite3`, `ffmpeg`) y bibliotecas Python (`opencv-python-headless`, `pyzbar`, `flask`, `flask-socketio`, `eventlet`, `Adafruit-Blinka`, etc.).
6. Confirme que el proceso finalice con el mensaje:
   ```text
   [OK] MES-BOT environment is CLEAN and READY.
   ```
7. Regrese a App Lab e inicie MES-BOT. App Lab compilará el sketch del microcontrolador (`sketch.ino`), preparará el entorno Python y los bricks, iniciará el contenedor Linux y activará los servicios web y de cámara.

---

## 3. Opción de Despliegue B: Plataforma Alternativa / PC (Experimental)

> **Aviso de Estado:** Esta modalidad es **teórica y aún no ha sido probada físicamente en la práctica**. Gracias a que la arquitectura desacopla la capa educativa del hardware físico, la interfaz web y el servidor Python pueden ejecutarse en computadores estándar o placas Linux genéricas, teniendo en cuenta las siguientes pautas.

Antes de iniciar el backend Python en una PC, realice la misma preparación de `.env.example` a `.env` indicada en el Paso 1. El envío de correo necesita los tres valores de InfoSeed; una prueba local que no envíe correo puede dejarlos vacíos.

### Funcionamiento de la Capa Desacoplada
La interfaz gráfica se compone de archivos HTML, CSS, JavaScript y Socket.IO en `assets/`. Se comunica con el backend mediante peticiones HTTP REST (`/list_users`, `/create_trajectory`, `/record_game`) y eventos de Socket.IO.

En un entorno sin la placa física Arduino Uno Q:

1. **Simulación del Puente de Control (Bridge):**
   * Las llamadas como `Bridge.call("move_forward")` o `Bridge.call("get_state")` pueden envolverse en un módulo simulador que imprima las acciones en consola y responda con estados simulados:
     ```json
     {
       "mode": "IDLE",
       "macro_mode": "NONE",
       "bno_ok": 1,
       "ina_ok": 1,
       "step_heading_result": "COMPLETED",
       "battery_v": 15.2,
       "battery_percent_est": 90
     }
     ```
2. **Manejo de Cámara y Omisión por Software:**
   * En el robot oficial, si la cámara no está conectada, el sistema activa la alerta amarilla `DISPOSITIVO NO DETECTADO: Cámara`.
   * En una PC de pruebas, se puede conectar cualquier cámara web USB mediante OpenCV.
   * **Cómo omitir la cámara sin escanear un QR físico:** No es obligatorio tener cámara para probar una ruta. Puede activar cualquier trayectoria directamente en memoria usando la API interna:
     * **Ruta:** `POST /set_active_trajectory`
     * **Cuerpo (JSON):** `{"id": 1}` *(reemplace 1 por el ID de la trayectoria)*
     * Al invocar este comando, la trayectoria se monta de inmediato en el panel de juego sin necesidad de escanear ninguna ficha física.
3. **Base de Datos:**
   * Utiliza SQLite estándar (`data/frames.db` y `data/code-scanner.db`), compatible con Windows, Linux y macOS.

---

## 4. Modos de Pantalla y Conexión (Uso Sin Internet)

Una vez completada la instalación inicial, **MES-BOT no requiere conexión a Internet**. Puede utilizarse de tres maneras diferentes:

### Modo 1: Robot Autónomo con Pantalla HDMI (Sin Red Externa)
La placa Arduino Uno Q entrega video mediante DisplayPort Alt Mode por USB-C. Para utilizar HDMI se necesita un concentrador o adaptador USB-C alimentado que tenga salida HDMI.
* Conecte el concentrador alimentado al UNO Q y conecte al concentrador el monitor o televisor, el ratón y el teclado USB.
* Al encender la placa, **Arduino App Lab se inicia automáticamente y abre el navegador web en la pantalla del robot** en la dirección `http://localhost:7000`.
* **Ventaja:** Funcionamiento 100% independiente. No requiere portátil externo, ni tablet, ni red Wi-Fi, ni router.

### Modo 2: Zona Wi-Fi Local desde Celular o Portátil
* Active la zona Wi-Fi (Hotspot) de su teléfono móvil o computador portátil.
* **No necesita datos móviles ni salida a Internet.** Los datos pueden estar **DESACTIVADOS**; el punto de acceso solo se utiliza como red local (LAN).
* Conecte el robot y su tablet o computador a dicha red local.
* Abra el navegador e ingrese a:
  ```text
  http://mes-bot:7000
  ```
  *(O el nombre que haya asignado a la placa, también puede usar: `http://<ip-del-robot>:7000`)*.

### Modo 3: Router Wi-Fi del Salón (Red Local)
* Conecte el robot y los dispositivos del colegio a la misma red Wi-Fi del aula (no es necesario que el router tenga salida a Internet).
* Abra `http://mes-bot:7000` *(O el nombre que haya asignado a la placa, también puede usar: `http://<ip-del-robot>:7000`)* en cualquier navegador.

---

## 5. Gestión de Contraseñas y Seguridad

* **Contraseña del dispositivo:** Durante la configuración inicial del UNO Q, el administrador crea la contraseña de Linux utilizada para SSH y la administración del sistema.
* **Contraseña web predeterminada:** `M123`
* **Instrucciones para cambiarla:**
  La contraseña del portal MES-BOT es independiente de la contraseña Linux del dispositivo. No sustituye la seguridad del dispositivo ni de la red. Para personalizar la contraseña web:
  1. Abra el archivo `assets/index.html` con un editor de texto o código.
  2. Ubique la línea 329:
     ```javascript
     if (pwd === 'M123') {
     ```
  3. Cambie `'M123'` por la clave deseada (por ejemplo, `'Colegio2026'`):
     ```javascript
     if (pwd === 'Colegio2026') {
     ```
  4. Guarde el archivo y recargue la página en el navegador.

---

## 6. Flujo de Trabajo en el Aula Paso a Paso

El panel principal de MES-BOT se divide en tres módulos:

```
┌────────────────────────────────────────────────────────┐
│                   CONSOLA MES-BOT                      │
├─────────────────┬──────────────────┬───────────────────┤
│  TRAYECTORIAS   │    JUGADORES     │       JUEGO       │
│  (Planeación)   │   (Perfiles)     │    (Evaluación)   │
└─────────────────┴──────────────────┴───────────────────┘
```

---

### 6.1 Trayectorias: Diseño en Matriz y Creación de QR

El módulo de Trayectorias (`assets/trayectorias/`) permite al docente diseñar recorridos lógicos sobre una cuadrícula de coordenadas que representa el tapete físico del salón.

#### Reglas de Diseño
1. **Casillas Estrictamente Consecutivas:** Debe hacer clic únicamente en casillas adyacentes horizontal o verticalmente. No se permiten saltos diagonales porque el robot se desplaza ortogonalmente (adelante, atrás, giro izquierda, giro derecha).
2. **Sin Casillas Repetidas:** Una trayectoria no puede pasar dos veces por la misma casilla. Cada paso debe ser único para evitar bucles.

#### Creación Paso a Paso
1. En el menú principal, haga clic en **TRAYECTORIAS**.
2. En la barra lateral derecha, presione **New Trajectory** (`+`) y escriba un nombre descriptivo (ej. *Reto 1 - Camino Recto* o *Circuito Laberinto*).
3. En la matriz (8 filas × 13 columnas), haga clic en la casilla de inicio (Frame 1).
4. Haga clic en la siguiente casilla contigua (Frame 2). El software detectará el vector de movimiento automáticamente:
   * Hacia arriba: **ADELANTE** (FORWARD)
   * Hacia abajo: **ATRÁS** (BACKWARD)
   * Hacia la derecha: **DERECHA** (RIGHT)
   * Hacia la izquierda: **IZQUIERDA** (LEFT)
5. Continúe marcando casillas hasta completar el recorrido deseado.
6. El recorrido se guarda automáticamente en la base de datos SQLite (`frames.db`). Puede presionar **Play Animation** para previsualizar el movimiento.

#### Exportación a PDF para Imprimir Fichas
1. En la lista lateral, marque la casilla de las trayectorias que desee imprimir.
2. Seleccione la distribución en **PDF Layout**:
   * `2 x 2`: 4 fichas grandes por página (ideal para tapetes de suelo grandes).
   * `2 x 3` (Predeterminado): 6 fichas por página.
   * `3 x 3`: 9 fichas medianas por página (ideal para mesas de trabajo).
3. Haga clic en **Bulk PDF** para descargar el documento imprimible.
   *(Opcional: Si configuró correo en `.env`, puede pulsar **Send Email** para enviarlo directamente a su cuenta).*
4. Cada ficha impresa incluye el nombre y número de la ruta, el diagrama de la cuadrícula, guías de corte y el código QR con el contenido `LOAD_TRAJECTORY:<ID>`.
5. Imprima el archivo, recorte las fichas y colóquelas exactamente en el **centro de las casillas correspondientes** en el tapete del salón.

---

### 6.2 Jugadores: Personalización de Avatar y Perfiles

En el módulo de Jugadores (`assets/usuarios/`), cada niño construye su identidad de juego antes de la actividad.

#### Creación del Perfil del Estudiante
1. En el menú principal, ingrese a **JUGADORES**.
2. Presione el botón flotante de agregar (**+**) en la esquina inferior derecha.
3. Se abrirá la ventana de personalización:
   * **Nombre o Apodo:** El estudiante escribe su nombre (hasta 12 caracteres).
   * **Elección de Héroe:** Selecciona entre 15 personajes ilustrados:
     * *Robot, Astronauta, Ninja, Superhéroe, Cohete, Mago, Monstruo, Dragón, Fantasma, Graduado, Espía, Gato, Perro, Araña, Meteoro.*
   * **Color de Poder:** Escoge su color preferido entre 9 opciones rápidas o con el selector cromático completo.
   * **Dado Mágico:** Al tocar el botón del dado, el sistema genera una combinación divertida de personaje, color y nombre al azar.
4. Presione **¡ESTOY LISTO!**. Una animación de confeti celebrará la creación y el perfil quedará registrado en la base de datos.
5. El perfil aparecerá en pantalla mostrando su avatar, borde con su color de poder, partidas jugadas, victorias y porcentaje de acierto.

---

### 6.3 El Juego: Ejecución, Comandos de Voz y Conducción Manual

El módulo de Juego (`assets/motor/`) conecta el robot físico con el estudiante y la consola de evaluación.

#### Preparación Física
1. Encienda el robot y verifique que la batería tenga buen nivel (superior a 14.5V en la consola).
2. Coloque el robot en el suelo, directamente sobre la **Ficha QR de la casilla inicial**.
3. Verifique que la cámara inferior apunte perpendicularmente hacia la ficha.

#### El Panel de Evaluación en Pantalla
1. En el menú principal, ingrese a **JUEGO**.
2. En el menú desplegable superior, **seleccione el estudiante** que va a jugar.
3. Observe los paneles de monitoreo:
   * **Flujo de Video en Vivo:** Muestra la imagen de la cámara inferior en tiempo real.
   * **Estado de Trayectoria:** Apenas la cámara lee el código QR, detecta `LOAD_TRAJECTORY:<ID>`, emite un sonido de confirmación, ubica la barra de progreso en `Paso 0 / N` y muestra la secuencia ordenada de comandos requeridos (ej. `A → D → A`).
   * **Lector de Códigos:** Confirma el contenido escaneado y la hora exacta.
   * **Interfaz de Voz:** Refleja las palabras que el micrófono va captando en tiempo real.

#### Conducción por Comandos de Voz (Modelo Offline: `kids.eim`)
El estudiante se coloca el micrófono de solapa y pronuncia las órdenes con voz clara y pausada.

> **Nota sobre el Reconocimiento de Voz:** El modelo local `kids.eim` fue entrenado con grabaciones de niños hispanohablantes y reconoce cinco comandos sin conexión a Internet. La aplicación contiene alias de comandos en inglés, pero el modelo EIM no fue entrenado con niños angloparlantes. Cuando hay Internet, el reconocimiento de voz de Google puede reconocer frases adicionales en español o inglés y asociarlas con las mismas acciones. El audio procesado por esa alternativa en línea se transmite a Google; desconecte el acceso a Internet cuando el procesamiento de voz deba permanecer completamente local.

| Comando Vocal (Hablado) | Acción del Robot | Descripción del Movimiento |
| :--- | :--- | :--- |
| **ADELANTE** | FORWARD | Avanza 20 cm hacia la siguiente casilla de la cuadrícula |
| **ATRÁS** | BACKWARD | Retrocede 20 cm hacia la casilla posterior |
| **IZQUIERDA** | LEFT | Gira 90° a la izquierda (sentido antihorario) |
| **DERECHA** | RIGHT | Gira 90° a la derecha (sentido horario) |
| **STOP** | STOP | Detiene inmediatamente cualquier movimiento del robot |

#### Validación de Pasos y Registro de Errores
* Si la orden coincide con el siguiente paso esperado:
  * El robot realiza el movimiento correspondiente (avanza 20 cm o gira 90°).
  * El contador de pasos aumenta (`Paso 1 / N`).
  * Suena un tono agradable de acierto.
* Si el niño dice una dirección equivocada respecto a la ruta planeada:
  * El robot permanece en su lugar de manera segura.
  * El contador de errores se incrementa (`Errores: 1`).

#### Modo de Conducción Manual (Alternativa)
Si en el aula hay mucho ruido o el estudiante necesita apoyo:
* Utilice los botones en pantalla: **Adelante**, **Atrás**, **Izquierda**, **Derecha** y **Parar**.
* O utilice las teclas del teclado en el computador del docente:
  * `W` o `↑` (Flecha Arriba): Avanzar
  * `S` o `↓` (Flecha Abajo): Retroceder
  * `A` o `←` (Flecha Izquierda): Girar 90° a la Izquierda
  * `D` o `→` (Flecha Derecha): Girar 90° a la Derecha
  * `Espacio` o `Escape`: Freno de Emergencia

#### Evaluación y Guardado de la Partida
1. Al llegar a la última casilla de la ruta, la barra de progreso se llena de color verde indicando **COMPLETADO**.
2. El docente pulsa el botón **Evaluar**:
   * Si completó todos los pasos: muestra **¡VICTORIA! ¡Todos los pasos completados!**
   * Si no alcanzó la meta: muestra **Pasos incompletos**.
3. Pulse **Registrar**:
   * La sesión queda guardada en SQLite con el nombre del jugador, la trayectoria realizada, la cantidad de errores, la duración total en segundos y si ganó o perdió.
   * Las estadísticas del perfil del niño se actualizan de inmediato.

---

### 6.4 Seguimiento Histórico y Analítica de Progreso

El sistema permite comprobar la evolución en la comprensión espacial de los niños a lo largo del tiempo:

1. Diríjase a **JUGADORES**.
2. Localice la tarjeta del estudiante.
3. Haga clic en el **Ícono de Reloj / Historial** (`fa-history`) en la cabecera de la tarjeta.
4. Se abrirá la ventana de **Historial de Partidas** con el registro cronológico completo:
   * Fecha y hora exacta de cada juego.
   * Nombre del reto o trayectoria.
   * Pasos completados frente al total.
   * Errores cometidos en cada intento.
   * Tiempo total empleado (en segundos).
   * Estado de victoria o derrota.
5. Estos datos proporcionan evidencia objetiva para que el docente identifique si el alumno confunde la lateralidad (derecha vs. izquierda) o si ha mejorado su capacidad de anticipación y secuenciación métrica a lo largo de las semanas.

---

## 7. Solución de Problemas y Diagnóstico

### Alertas de Dispositivo No Detectado
Si aparece una franja amarilla con el mensaje `DISPOSITIVO NO DETECTADO`:
* **Cámara:** Revise que el conector USB de la cámara esté bien insertado. Si está ejecutando en PC de pruebas sin cámara, monte la trayectoria mediante `POST /set_active_trajectory`.
* **Micrófono:** Compruebe la conexión del micrófono de solapa (USB o 3.5mm).
* **Conexión MCU:** Significa que la capa Linux no recibe respuesta del sketch Zephyr. Reinicie la alimentación del robot o verifique la compilación del sketch.
* **Base de Datos:** Verifique que la carpeta `data/` tenga permisos de lectura y escritura.

### Calibración de Orientación (Zero Pose)
Si el robot se desvía al avanzar en línea recta o realiza giros con ángulo impreciso:
1. Abra el panel de calibración ingresando a `http://mes-bot:7000/calibration/` (o `http://localhost:7000/calibration/` si está usando la pantalla HDMI).
2. Alinee el robot completamente recto sobre una superficie lisa.
3. Presione el botón **Zero Pose** para restablecer el punto cero de orientación de la IMU BNO085.
