'use strict';
/**
 * Fullscreen for chart cards.
 * ⛶ button is rendered by Python inside every .fs-card.
 * On enter: relayout all Plotly charts in the card to fill the screen height.
 * On exit:  restore original heights.
 */
(function () {
    var activeBtn  = null;
    var activeCard = null;

    // ── Click on ⛶ button ───────────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('.fs-btn') : null;
        if (!btn) return;

        var card = btn.closest('.fs-card');
        if (!card) return;

        if (!document.fullscreenElement) {
            activeBtn  = btn;
            activeCard = card;
            card.requestFullscreen().catch(function (err) {
                console.warn('Fullscreen request failed:', err);
            });
        } else {
            document.exitFullscreen();
        }
    });

    // ── fullscreenchange: fires after transition completes ──────────────────
    document.addEventListener('fullscreenchange', function () {

        if (document.fullscreenElement) {
            // ── Entered fullscreen ──────────────────────────────────────────
            if (activeBtn) {
                activeBtn.textContent = '✕';
                activeBtn.title = 'Exit fullscreen';
            }

            var card = document.fullscreenElement;

            // Small delay to let the browser finish painting at full size
            setTimeout(function () {
                var charts = card.querySelectorAll('.js-plotly-plot');
                if (!charts.length || !window.Plotly) return;

                // window.innerHeight is the fullscreen viewport height here
                // Subtract card header (section label + padding ~90px)
                var headerH = card.querySelector('.section-header-row') ? 90 : 90;
                var newH    = Math.max(300, window.innerHeight - headerH);

                charts.forEach(function (gd) {
                    gd._origH = (gd.layout || {}).height;   // save for restore
                    window.Plotly.relayout(gd, { height: newH });
                });
            }, 80);

        } else {
            // ── Exited fullscreen ────────────────────────────────────────────
            if (activeBtn) {
                activeBtn.textContent = '⛶';
                activeBtn.title = 'Fullscreen';
            }
            activeBtn  = null;
            activeCard = null;

            // Restore all charts to their original heights
            setTimeout(function () {
                document.querySelectorAll('.js-plotly-plot').forEach(function (gd) {
                    if (!window.Plotly) return;
                    if (gd._origH != null) {
                        window.Plotly.relayout(gd, { height: gd._origH });
                        gd._origH = null;
                    } else {
                        window.Plotly.Plots.resize(gd);
                    }
                });
            }, 80);
        }
    });

}());
