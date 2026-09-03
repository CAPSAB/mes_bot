 





const MESBOT_LOCALES = {
    es: {
        main_app: {
            window_title:               "MesBot — Consola de Control",
            header_title:               "MES-BOT",
            header_title_main:          "MES-BOT",
            header_title_game:          "JUEGO",
            header_title_traj:          "TRAYECTORIAS",
            header_title_players:       "JUGADORES",
            header_subtitle_main:       "Sistema de Enseñanza Métrico-Espacial y Plataforma Robótica",
            header_subtitle_game:       "Lee el código QR bajo el robot y sigue la trayectoria deseada por voz, usa el control manual si algo falla",
            header_subtitle_traj:       "Crea trayectorias en la matriz y exporta los códigos QR correspondientes, decoralos de forma creativa y ubicalos en el centro de la casilla correspondiente en el tablero",
            header_subtitle_players:    "Crea usuarios para llevar el histórico de los estudiantes, deja que elijan su avatar",
            header_description:         "Sistema de Enseñanza Métrico-Espacial y Plataforma Robótica",
            header_experiment_title:    "CONTROL DE EXPERIMENTO",
            header_experiment_desc:     "Gestión de tracción, lectura de códigos y monitoreo en tiempo real.",
            header_experiment_subtitle: "Monitoreo en Tiempo Real — FBR",
            header_calibration_title:   "CALIBRACIÓN E INSTRUMENTACIÓN",
            header_calibration_subtitle:"Ajuste de Sensores y Actuadores",
            btn_home:       "Inicio",
            btn_exit:       "Salir",
            btn_fullscreen: "Pantalla Completa"
        },
        telemetry: {
            batt: "BATERÍA",
            volt: "VOLTAJE",
            curr: "CORRIENTE",
            acc:  "ACEL"
        },
        auth: {
            welcome_title: "MesBot - Acceso",
            login_title:   "MES-BOT",
            login_error:   "Acceso denegado"
        },
        control: {
            light_title: "Centro de Iluminación",
            temp_title:  "Gestión Térmica",
            level_title: "Regulación de Nivel",
            co2_title:   "Dosificación de CO2",
            intensity:   "Intensidad",
            color:       "Color",
            start:       "INICIAR",
            stop:        "DETENER",
            save:        "GUARDAR"
        },
        analytics: {
            window_title:      "Gestión de Datos",
            header_subtitle:   "Base de Datos y Jugadores",
            page_title:        "JUGADORES",
            db_card_title:     "BASE DE DATOS",
            db_card_desc:      "Historial de resultados, gestión de usuarios y analítica avanzada.",
            users_card_title:  "JUGADORES",
            users_card_desc:   "Crea usuarios para llevar el histórico de los estudiantes, deja que elijan su avatar"
        },
        motor_controls: {
            title:             "SISTEMA DE TRACCIÓN",
            hint:              "Control: W A S D / Flechas",
            card_title:        "JUEGO",
            card_desc:         "Lee el código QR bajo el robot y sigue la trayectoria deseada por voz, usa el control manual si algo falla",
            page_title:        "JUEGO",
            btn_up:            "Adelante",
            btn_down:          "Atrás",
            btn_left:          "Izquierda",
            btn_right:         "Derecha",
            btn_stop:          "Parar",
            qr_title:          "LECTURA DE CÓDIGOS",
            qr_waiting:        "Esperando escaneo...",
            cam_title:         "FLUJO DE VÍDEO",
            cam_waiting:       "Esperando cámara...",
            speech_title:      "INTERFAZ DE VOZ",
            speech_listening:  "Escuchando...",
            traj_title:        "TRAYECTORIAS",
            traj_page_title:   "TRAYECTORIAS",
            window_title:      "TRAYECTORIAS",
            traj_desc:         "Crea trayectorias en la matriz y exporta los códigos QR correspondientes, decoralos de forma creativa y ubicalos en el centro de la casilla correspondiente en el tablero",
            traj_empty:        "Sin trayectoria.",
            traj_steps:        "{current} / {total} pasos",
            game_title:        "PANEL DE EVALUACIÓN",
            game_player:       "Jugador",
            game_evaluate:     "Evaluar",
            game_record:       "Registrar",
            game_select_player:"— Seleccionar Jugador —"
        },
        nav: {
            sound:    "Sonido",
            home:     "Inicio",
            logout:   "Salir",
            language: "Idioma",
            menu:     "Menú"
        },
        alerts: {
            low_battery: "BATERÍA BAJA",
            peripheral_missing: "DISPOSITIVO NO DETECTADO: ",
            camera: "Cámara",
            microphone: "Micrófono",
            mcu_serial: "Conexión MCU",
            database: "Base de Datos"
        },
        avatar: {
            title_create: "¡Crea tu Héroe!",
            title_edit: "¡Edita tu Héroe!",
            name_placeholder: "TU NOMBRE",
            label_hero: "Elige tu Héroe",
            label_color: "Elige tu Color de Poder",
            btn_ready: "¡ESTOY LISTO!",
            robot: "Robot",
            astronaut: "Astronauta",
            ninja: "Ninja",
            superhero: "Superhéroe",
            rocket: "Cohete",
            wizard: "Mago",
            monster: "Monstruo",
            dragon: "Dragón",
            ghost: "Fantasma",
            graduate: "Graduado",
            spy: "Espía",
            cat: "Gato",
            dog: "Perro",
            spider: "Araña",
            meteor: "Meteoro"
        }
    },

    en: {
        main_app: {
            window_title:               "MesBot — Control Console",
            header_title:               "MES-BOT",
            header_title_main:          "MES-BOT",
            header_title_game:          "GAME",
            header_title_traj:          "TRAJECTORIES",
            header_title_players:       "PLAYERS",
            header_subtitle_main:       "Metric-Spatial Teaching System and Robotic Platform",
            header_subtitle_game:       "Read the QR code under the robot and follow the desired path by voice, use manual control if something fails",
            header_subtitle_traj:       "Create paths on the matrix and export the corresponding QR codes, decorate them creatively and place them in the center of the corresponding square on the board",
            header_subtitle_players:    "Create users to track student history, let them choose their avatar",
            header_description:         "Metric-Spatial Teaching System and Robotic Platform",
            header_experiment_title:    "EXPERIMENT CONTROL",
            header_experiment_desc:     "Traction system management, code scanning, and real-time monitoring.",
            header_experiment_subtitle: "Real-Time Monitoring — FBR",
            header_calibration_title:   "CALIBRATION & INSTRUMENTATION",
            header_calibration_subtitle:"Sensor & Actuator Tuning",
            btn_home:       "Home",
            btn_exit:       "Exit",
            btn_fullscreen: "Full Screen"
        },
        telemetry: {
            batt: "BATT",
            volt: "VOLT",
            curr: "CURR",
            acc:  "ACC"
        },
        auth: {
            welcome_title: "MesBot - Login",
            login_title:   "MES-BOT",
            login_error:   "Access denied"
        },
        control: {
            light_title: "Lighting Center",
            temp_title:  "Thermal Management",
            level_title: "Level Regulation",
            co2_title:   "CO2 Dosing",
            intensity:   "Intensity",
            color:       "Color",
            start:       "START",
            stop:        "STOP",
            save:        "SAVE"
        },
        analytics: {
            window_title:      "Data Management",
            header_subtitle:   "Database & Players",
            page_title:        "PLAYERS",
            db_card_title:     "DATABASE",
            db_card_desc:      "Results history, user management, and advanced analytics.",
            users_card_title:  "PLAYERS",
            users_card_desc:   "Create users to track student history, let them choose their avatar"
        },
        motor_controls: {
            title:             "TRACTION SYSTEM",
            hint:              "Control: W A S D / Arrow keys",
            card_title:        "GAME",
            card_desc:         "Read the QR code under the robot and follow the desired path by voice, use manual control if something fails",
            page_title:        "GAME",
            btn_up:            "Forward",
            btn_down:          "Backward",
            btn_left:          "Left",
            btn_right:         "Right",
            btn_stop:          "Stop",
            qr_title:          "CODE SCANNER",
            qr_waiting:        "Waiting for scan...",
            cam_title:         "LIVE VIDEO FEED",
            cam_waiting:       "Waiting for camera...",
            speech_title:      "VOICE INTERFACE",
            speech_listening:  "Listening...",
            traj_title:        "TRAJECTORIES",
            traj_page_title:   "TRAJECTORIES",
            window_title:      "TRAJECTORIES",
            traj_desc:         "Create paths on the matrix and export the corresponding QR codes, decorate them creatively and place them in the center of the corresponding square on the board",
            traj_empty:        "No path loaded.",
            traj_steps:        "{current} / {total} steps",
            game_title:        "EVALUATION PANEL",
            game_player:       "Player",
            game_evaluate:     "Evaluate",
            game_record:       "Record",
            game_select_player:"— Select User —"
        },
        nav: {
            sound:    "Sound",
            home:     "Home",
            logout:   "Logout",
            language: "Language",
            menu:     "Menu"
        },
        alerts: {
            low_battery: "LOW BATTERY",
            peripheral_missing: "DEVICE NOT DETECTED: ",
            camera: "Camera",
            microphone: "Microphone",
            mcu_serial: "MCU Connection",
            database: "Database"
        },
        avatar: {
            title_create: "Create your Hero!",
            title_edit: "Edit your Hero!",
            name_placeholder: "YOUR NAME",
            label_hero: "Pick your Hero",
            label_color: "Pick your Power Color",
            btn_ready: "I'M READY!",
            robot: "Robot",
            astronaut: "Astronaut",
            ninja: "Ninja",
            superhero: "Superhero",
            rocket: "Rocket",
            wizard: "Wizard",
            monster: "Monster",
            dragon: "Dragon",
            ghost: "Ghost",
            graduate: "Graduate",
            spy: "Spy",
            cat: "Cat",
            dog: "Dog",
            spider: "Spider",
            meteor: "Meteor"
        }
    }
};

class LanguageManager {
    constructor() {
        this.language = localStorage.getItem('mesbot_lang') || 'es';
        this.texts    = MESBOT_LOCALES[this.language] || MESBOT_LOCALES['es'];
        this.subscribers = [];
        this.ready    = Promise.resolve(true);
        document.documentElement.lang = this.language;
        document.addEventListener('DOMContentLoaded', () => this.applyTranslations());
    }

    setLanguage(lang) {
        if (!MESBOT_LOCALES[lang]) return;
        this.language = lang;
        this.texts    = MESBOT_LOCALES[lang];
        localStorage.setItem('mesbot_lang', lang);
        document.documentElement.lang = lang;
        this.applyTranslations();
        this.notify(lang);
    }

    toggleLanguage() {
        this.setLanguage(this.language === 'es' ? 'en' : 'es');
    }

    getLanguage() {
        return this.language;
    }

    t(module, key, defaultText) {
        return (this.texts[module] && this.texts[module][key]) || defaultText || null;
    }

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const [module, key] = el.getAttribute('data-i18n').split('.');
            const val = this.t(module, key);
            if (!val) return;
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = val;
            } else {
                el.textContent = val;
            }
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const [module, key] = el.getAttribute('data-i18n-placeholder').split('.');
            const val = this.t(module, key);
            if (val) el.placeholder = val;
        });

        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const [module, key] = el.getAttribute('data-i18n-title').split('.');
            const val = this.t(module, key);
            if (val) el.title = val;
        });

        document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
            const [module, key] = el.getAttribute('data-i18n-aria-label').split('.');
            const val = this.t(module, key);
            if (val) el.setAttribute('aria-label', val);
        });

        const pageTitle = this.t('main_app', 'window_title') || this.t('auth', 'welcome_title');
        if (pageTitle) document.title = pageTitle;
    }

    subscribe(callback) {
        this.subscribers.push(callback);
    }

    notify(lang) {
        this.subscribers.forEach(cb => cb(lang));
    }
}

window.langManager = new LanguageManager();
window.tr = (m, k, d) => window.langManager.t(m, k, d);
