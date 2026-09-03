window.MesBotUtils = {
    toggleFullscreen: function() {
        if (!document.fullscreenElement) {
            if (document.activeElement && typeof document.activeElement.blur === 'function') {
                document.activeElement.blur();
            }
            document.documentElement.requestFullscreen().catch(err => {
                console.warn(`Fullscreen request blocked: ${err.message}. Will retry on first interaction.`);
            });
        }
    },

    forceFullscreen: function() {
        this.toggleFullscreen();

        const trigger = () => {
            this.toggleFullscreen();
            document.removeEventListener('click', trigger);
            document.removeEventListener('keydown', trigger);
        };

        document.addEventListener('click', trigger);
        document.addEventListener('keydown', trigger);
    },

    updateFullscreenUI: function() {},

    openModule: function(path) {
        window.location.href = path;
    },

    closeModule: function() {
        window.location.href = '../';
    },


    injectHeader: function(titleKey, subtitleKey) {
        const basePath = '../';
        const homeAction = `window.location.href='${basePath}main/'`;
        const exitAction = `MesBotUtils.logout()`;

        titleKey = titleKey || 'main_app.header_title_main';
        subtitleKey = subtitleKey || 'main_app.header_subtitle_main';

        const localizedText = (i18nKey, fallback = '') => {
            if (!window.langManager || !i18nKey) return fallback;
            const [module, key] = i18nKey.split('.');
            return window.langManager.t(module, key, fallback) || fallback;
        };

        const titleFallback = localizedText(titleKey, 'MES-BOT');
        const subtitleFallback = localizedText(subtitleKey);
        const soundLabel = localizedText('nav.sound');
        const homeLabel = localizedText('nav.home');
        const logoutLabel = localizedText('nav.logout');
        const languageLabel = localizedText('nav.language');
        const menuLabel = localizedText('nav.menu');

        const headerHTML = `
        <header class="unified-header">
          <div class="logo-group" id="header-logo-group">
              <img class="brand-logo" src="${basePath}common/img/logo_sabana.svg" alt="Sabana" />
              <img class="brand-logo" src="${basePath}common/img/logo_capsab.png" alt="CAPSAB" />
          </div>

          <div class="header-center">
              <div class="header-title" data-i18n="${titleKey}">${titleFallback}</div>
              <div class="header-subtitle" data-i18n="${subtitleKey}">${subtitleFallback}</div>
              <div class="header-telemetry" id="header-telemetry">
                  <div class="h-tel-item">
                    <span class="h-tel-dot" id="htel-dot"></span>
                    <span class="h-tel-label" data-i18n="telemetry.batt">BATT:</span>
                    <span class="h-tel-val"><span id="htel-batt">—</span>%</span>
                  </div>
                  <div class="h-tel-item">
                    <span class="h-tel-label" data-i18n="telemetry.volt">VOLT:</span>
                    <span class="h-tel-val"><span id="htel-volt">—</span>V</span>
                  </div>
                  <div class="h-tel-item">
                    <span class="h-tel-label" data-i18n="telemetry.curr">CURR:</span>
                    <span class="h-tel-val"><span id="htel-curr">—</span>mA</span>
                  </div>
                  <div class="h-tel-item">
                    <span class="h-tel-label" data-i18n="telemetry.acc">ACC:</span>
                    <span class="h-tel-val">X:<span id="htel-ax">—</span> Y:<span id="htel-ay">—</span> Z:<span id="htel-az">—</span></span>
                  </div>
              </div>
          </div>

          <div class="header-right-zone">
              <div class="unified-nav" id="desktop-nav">
                  <button class="nav-item" onclick="${homeAction}" title="${homeLabel}" aria-label="${homeLabel}" data-i18n-title="nav.home" data-i18n-aria-label="nav.home"><i class="fas fa-home"></i></button>
                  <button class="nav-item" onclick="${exitAction}" title="${logoutLabel}" aria-label="${logoutLabel}" data-i18n-title="nav.logout" data-i18n-aria-label="nav.logout"><i class="fas fa-sign-out-alt"></i></button>
                  <button class="nav-item" id="btn-lang-toggle" onclick="window.langManager.toggleLanguage()" style="border-right:none;" title="${languageLabel}" aria-label="${languageLabel}" data-i18n-title="nav.language" data-i18n-aria-label="nav.language"><i class="fas fa-language"></i></button>
              </div>

              <button class="hamburger-btn" id="hamburger-btn" onclick="MesBotUtils.toggleMobileMenu()" title="${menuLabel}" aria-label="${menuLabel}" data-i18n-title="nav.menu" data-i18n-aria-label="nav.menu">
                  <i class="fas fa-bars" id="hamburger-icon"></i>
              </button>
          </div>

          <div id="low-battery-warning" style="display:none; position:fixed; top:80px; left:50%; transform:translateX(-50%); background:#ef4444; color:white; padding:8px 20px; border-radius:30px; z-index:10000; font-weight:bold; box-shadow:0 4px 20px rgba(239,68,68,0.5); border:2px solid white; white-space:nowrap;">
              <i class="fas fa-exclamation-triangle"></i> <span data-i18n="alerts.low_battery">LOW BATTERY</span>
          </div>

          <div id="peripheral-warning" style="display:none; position:fixed; top:130px; left:50%; transform:translateX(-50%); background:#eab308; color:black; padding:8px 20px; border-radius:30px; z-index:10000; font-weight:bold; box-shadow:0 4px 20px rgba(234,179,8,0.5); border:2px solid white; white-space:nowrap;">
              <i class="fas fa-exclamation-circle"></i> <span id="peripheral-warning-text">DISPOSITIVO NO DETECTADO</span>
          </div>
        </header>

        <div class="mobile-menu" id="mobile-menu">
            <div class="mobile-menu-inner">
                <div class="mobile-menu-logos">
                    <img src="${basePath}common/img/logo_sabana.svg" alt="Sabana" />
                    <img src="${basePath}common/img/logo_capsab.png" alt="CAPSAB" />
                </div>

                <div class="mobile-telemetry">
                    <span class="h-tel-dot" id="m-htel-dot"></span>
                    <span class="mobile-tel-item">
                        <span class="mobile-tel-label" data-i18n="telemetry.batt">BATT</span>
                        <span class="mobile-tel-val"><span id="m-htel-batt">—</span>%</span>
                    </span>
                    <span class="mobile-tel-item">
                        <span class="mobile-tel-label" data-i18n="telemetry.volt">VOLT</span>
                        <span class="mobile-tel-val"><span id="m-htel-volt">—</span>V</span>
                    </span>
                    <span class="mobile-tel-item">
                        <span class="mobile-tel-label" data-i18n="telemetry.curr">CURR</span>
                        <span class="mobile-tel-val"><span id="m-htel-curr">—</span>mA</span>
                    </span>
                </div>

                <div class="mobile-menu-actions">
                    <button class="mobile-action-btn" id="mobile-mute-btn" onclick="window.MesBotAudio && window.MesBotAudio.toggle(); MesBotUtils.closeMobileMenu();" title="${soundLabel}" aria-label="${soundLabel}" data-i18n-title="nav.sound" data-i18n-aria-label="nav.sound">
                        <i class="fas fa-volume-up" id="mobile-mute-icon"></i>
                    </button>
                    <button class="mobile-action-btn" onclick="window.location.href='${basePath}main/'; MesBotUtils.closeMobileMenu();" title="${homeLabel}" aria-label="${homeLabel}" data-i18n-title="nav.home" data-i18n-aria-label="nav.home">
                        <i class="fas fa-home"></i>
                    </button>
                    <button class="mobile-action-btn" onclick="MesBotUtils.logout();" title="${logoutLabel}" aria-label="${logoutLabel}" data-i18n-title="nav.logout" data-i18n-aria-label="nav.logout">
                        <i class="fas fa-sign-out-alt"></i>
                    </button>
                    <button class="mobile-action-btn" onclick="window.langManager.toggleLanguage(); MesBotUtils.closeMobileMenu();" title="${languageLabel}" aria-label="${languageLabel}" data-i18n-title="nav.language" data-i18n-aria-label="nav.language">
                        <i class="fas fa-language"></i>
                    </button>
                </div>
            </div>
        </div>
        <div class="mobile-menu-overlay" id="mobile-menu-overlay" onclick="MesBotUtils.closeMobileMenu()"></div>
        `;

        const container = document.getElementById('mesbot-header-container');
        if (container) {
            container.outerHTML = headerHTML;
            if (window.langManager) window.langManager.applyTranslations();
            if (window.MesBotAudio) window.MesBotAudio.init();
            if (window.MesBotTelemetry) window.MesBotTelemetry.init();
        } else {
            console.warn('MesBotUtils: #mesbot-header-container not found.');
        }
    },

    toggleMobileMenu: function() {
        const menu    = document.getElementById('mobile-menu');
        const overlay = document.getElementById('mobile-menu-overlay');
        const icon    = document.getElementById('hamburger-icon');
        if (!menu) return;
        const open = menu.classList.toggle('open');
        if (overlay) {
            overlay.style.display = open ? 'block' : 'none';
            overlay.classList.toggle('open', open);
        }
        if (icon) { icon.className = open ? 'fas fa-times' : 'fas fa-bars'; }
    },

    closeMobileMenu: function() {
        const menu    = document.getElementById('mobile-menu');
        const overlay = document.getElementById('mobile-menu-overlay');
        const icon    = document.getElementById('hamburger-icon');
        if (menu)    menu.classList.remove('open');
        if (overlay) { overlay.classList.remove('open'); overlay.style.display = 'none'; }
        if (icon)    icon.className = 'fas fa-bars';
    },

    logout: function() {
        sessionStorage.removeItem('mesbot_auth');
        if (window.MesBotAudio) window.MesBotAudio.stop();
        window.location.href = '../index.html';
    }
};




window.MesBotAudio = {
    _audio: null,
    _musicPath: '/common/sounds/MusicaFondo.mp3',
    _volume: 0.08,

    init: function() {
        if (!this._audio) {
            const depth = (window.location.pathname.match(/\//g) || []).length;
            const rootPath = window.location.pathname.includes('/assets/') 
                ? window.location.pathname.split('/assets/')[0] + '/assets/'
                : '/';
            const finalPath = rootPath + 'common/sounds/MusicaFondo.mp3';

            this._audio = document.createElement('audio');
            this._audio.id = 'bg-music-global';
            this._audio.loop = true;
            this._audio.src = finalPath;
            this._audio.volume = this._volume;
            this._audio.muted = localStorage.getItem('mesbot_muted') === 'true';
            document.body.appendChild(this._audio);
        }
        
        this.injectMuteButton();

        if (sessionStorage.getItem('mesbot_auth') === 'granted') {
            this.play();
        }
    },

    injectMuteButton: function() {
        const nav = document.querySelector('.unified-nav');
        if (!nav) return;

        const placeholder = document.getElementById('btn-mute-placeholder');
        if (placeholder) placeholder.remove();

        if (document.getElementById('btn-mute-global')) return;

        const muted = this._audio ? this._audio.muted : localStorage.getItem('mesbot_muted') === 'true';
        const btn = document.createElement('button');
        btn.id = 'btn-mute-global';
        btn.className = 'nav-item';
        btn.title = 'Mute/Unmute';
        btn.onclick = () => window.MesBotAudio.toggle();

        const icon = document.createElement('i');
        icon.id = 'mute-icon-global';
        icon.className = muted ? 'fas fa-volume-mute' : 'fas fa-volume-up';

        btn.appendChild(icon);
        nav.prepend(btn);

        const mobileIcon = document.getElementById('mobile-mute-icon');
        if (mobileIcon) mobileIcon.className = icon.className;
    },

    play: function() {
        if (!this._audio) return;
        this._audio.play().catch(() => {
            const resume = () => {
                this._audio.play();
                document.removeEventListener('click', resume);
            };
            document.addEventListener('click', resume);
        });
    },

    stop: function() {
        if (!this._audio) return;
        this._audio.pause();
        this._audio.currentTime = 0;
    },

    toggle: function() {
        if (!this._audio) return;
        this._audio.muted = !this._audio.muted;
        localStorage.setItem('mesbot_muted', this._audio.muted);

        const cls = this._audio.muted ? 'fas fa-volume-mute' : 'fas fa-volume-up';

        const desktopIcon = document.getElementById('mute-icon-global');
        if (desktopIcon) desktopIcon.className = cls;

        const mobileIcon = document.getElementById('mobile-mute-icon');
        if (mobileIcon) mobileIcon.className = cls;
    }
};

window.MesBotTelemetry = {
    _set: function(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    },
    update: function(data) {
        const dot  = document.getElementById('htel-dot');
        const mDot = document.getElementById('m-htel-dot');
        if (dot)  dot.classList.add('live');
        if (mDot) mDot.classList.add('live');

        const ina = data.ina219;
        if (ina) {
            const pct = Math.round(data.battery_pct ?? 0);
            const battEl = document.getElementById('htel-batt');
            const mBattEl = document.getElementById('m-htel-batt');
            const color = pct < 20 ? '#ef4444' : pct < 40 ? '#eab308' : '#22c55e';
            
            if (battEl) {
                battEl.textContent = pct;
                battEl.style.color = color;
            }
            if (mBattEl) {
                mBattEl.textContent = pct;
                mBattEl.style.color = color;
            }

            const warnBanner = document.getElementById('low-battery-warning');
            if (pct > 0 && pct < 20) {
                document.body.classList.add('low-battery-alert');
                if (warnBanner) warnBanner.style.display = 'block';
            } else {
                document.body.classList.remove('low-battery-alert');
                if (warnBanner) warnBanner.style.display = 'none';
            }

            const volt = ina.voltage_v.toFixed(1);
            const curr = Math.round(ina.current_ma);

            this._set('htel-volt',   volt);
            this._set('htel-curr',   curr);
            this._set('m-htel-batt', pct);
            this._set('m-htel-volt', volt);
            this._set('m-htel-curr', curr);
        }

        const mpu = data.mpu6050;
        if (mpu) {
            this._set('htel-ax', mpu.ax_g.toFixed(1));
            this._set('htel-ay', mpu.ay_g.toFixed(1));
            this._set('htel-az', mpu.az_g.toFixed(1));
        }

        const periphs = data.peripherals;
        if (periphs) {
            const missing = [];
            const alerts = (window.langManager && window.langManager.texts && window.langManager.texts.alerts) || {};
            if (periphs.camera === false) missing.push(alerts.camera || 'Camera');
            if (periphs.microphone === false) missing.push(alerts.microphone || 'Microphone');
            if (periphs.mcu_serial === false) missing.push(alerts.mcu_serial || 'MCU Connection');
            if (periphs.database === false) missing.push(alerts.database || 'Database');
            
            const warnEl = document.getElementById('peripheral-warning');
            const warnTextEl = document.getElementById('peripheral-warning-text');
            if (warnEl && warnTextEl) {
                if (missing.length > 0) {
                    const prefix = alerts.peripheral_missing || 'Missing: ';
                    warnTextEl.textContent = prefix + missing.join(', ');
                    warnEl.style.display = 'block';
                } else {
                    warnEl.style.display = 'none';
                }
            }
        }
    },
    init: function() {
        const headerTel = document.getElementById('header-telemetry');
        if (!headerTel) return;

        headerTel.style.display = 'flex';
        
        const sensorUrl = `http://${window.location.host || 'localhost'}/sensors`;
        fetch(sensorUrl, { cache: 'no-store' })
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d) this.update(d); })
            .catch(() => {
                console.warn("[Telemetry] Initial fetch failed, waiting for stream.");
            });
            
        if (window.socket) {
            window.socket.on('sensor_update', (d) => this.update(d));
        } else if (window._sbarSocket) {
             window._sbarSocket.on('sensor_update', (d) => this.update(d));
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (window.parent && window.parent !== window) {
        document.body.classList.add('in-iframe');
    }

    if (sessionStorage.getItem('mesbot_auth') === 'granted') {
        document.body.classList.add('sabana-bg-active');
    }

    window.MesBotAudio.init();

    window.MesBotTelemetry.init();

    window.MesBotUtils.forceFullscreen();

    document.body.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            window.MesBotUtils.toggleFullscreen();
        }
    }, { once: false });
});

(function() {
    const path = window.location.pathname.toLowerCase();
    const isLoginPage = path.endsWith('/assets/') || path.endsWith('/assets/index.html');
    const isAuth = sessionStorage.getItem('mesbot_auth') === 'granted';
    
    if (!isLoginPage && !isAuth) {
        window.location.href = '../index.html';
    }
})();
