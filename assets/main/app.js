 

document.addEventListener("DOMContentLoaded", async () => {
    
    window.socket = io(`http://${window.location.host}`);
    
    
    if (window.langManager) {
        await window.langManager.ready;
    }

    
    if (window.MesBotUtils) {
        window.MesBotUtils.injectHeader('main_app.header_title_main', 'main_app.header_subtitle_main');
    }

    
    document.body.classList.add('sabana-bg-active');
    
    
    if (window.MesBotAudio) {
        window.MesBotAudio.play();
    }
    
    console.log("MesBot Dashboard Initialized");
});
