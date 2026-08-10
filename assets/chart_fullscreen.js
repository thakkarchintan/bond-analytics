'use strict';
/**
 * Fullscreen for chart cards.
 * The ⛶ button is rendered by Python inside every .fs-card div.
 * This script only handles the click → requestFullscreen flow.
 */
(function () {
    var activeBtn = null;

    document.addEventListener('click', function (e) {
        // Work with both the button and any child element (SVG, span) that might be clicked
        var btn = e.target.closest ? e.target.closest('.fs-btn') : null;
        if (!btn) return;

        var card = btn.closest('.fs-card');
        if (!card) return;

        if (!document.fullscreenElement) {
            activeBtn = btn;
            card.requestFullscreen().then(function () {
                btn.textContent = '✕';
                btn.title = 'Exit fullscreen';
                // Give the browser a frame to resize, then resize Plotly charts
                setTimeout(function () {
                    card.querySelectorAll('.js-plotly-plot').forEach(function (gd) {
                        if (window.Plotly) window.Plotly.Plots.resize(gd);
                    });
                }, 150);
            }).catch(function (err) {
                console.warn('Fullscreen request failed:', err);
            });
        } else {
            document.exitFullscreen();
        }
    });

    document.addEventListener('fullscreenchange', function () {
        if (!document.fullscreenElement) {
            if (activeBtn) {
                activeBtn.textContent = '⛶';
                activeBtn.title = 'Fullscreen';
                activeBtn = null;
            }
            // Resize all visible Plotly charts back to their original dimensions
            setTimeout(function () {
                document.querySelectorAll('.js-plotly-plot').forEach(function (gd) {
                    if (window.Plotly) window.Plotly.Plots.resize(gd);
                });
            }, 150);
        }
    });
}());
