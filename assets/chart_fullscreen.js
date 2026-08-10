'use strict';
/**
 * Adds a fullscreen button to every Plotly chart rendered by Dash.
 * Uses the browser's native Fullscreen API (requestFullscreen / exitFullscreen).
 * Dash automatically loads any JS file placed in the assets/ folder.
 */
(function () {
    var FS_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>';
    var EX_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="10" y1="14" x2="3" y2="21"/><line x1="21" y1="3" x2="14" y2="10"/></svg>';

    var BTN_STYLE = [
        'position:absolute', 'top:46px', 'right:10px', 'z-index:200',
        'background:rgba(255,255,255,0.92)', 'border:1px solid #cbd5e1',
        'border-radius:5px', 'padding:5px 7px', 'cursor:pointer',
        'color:#475569', 'display:flex', 'align-items:center',
        'justify-content:center', 'line-height:1',
        'box-shadow:0 1px 4px rgba(0,0,0,0.12)',
        'transition:background 0.15s,border-color 0.15s',
    ].join(';');

    function wrapPlot(el) {
        if (el._fsWrapped) return;
        el._fsWrapped = true;

        // Ensure the parent can host an absolutely-positioned button
        var parent = el.parentElement;
        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        var btn = document.createElement('button');
        btn.innerHTML = FS_ICON;
        btn.title = 'Fullscreen';
        btn.setAttribute('style', BTN_STYLE);
        btn.setAttribute('aria-label', 'Toggle fullscreen');

        btn.addEventListener('mouseenter', function () {
            btn.style.background = '#f1f5f9';
            btn.style.borderColor = '#94a3b8';
        });
        btn.addEventListener('mouseleave', function () {
            btn.style.background = 'rgba(255,255,255,0.92)';
            btn.style.borderColor = '#cbd5e1';
        });

        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            var target = el.closest('.card-wrap') || parent;
            if (!document.fullscreenElement) {
                var savedStyle = {
                    background: target.style.background,
                    padding:    target.style.padding,
                    overflow:   target.style.overflow,
                };
                target.requestFullscreen().then(function () {
                    btn.innerHTML = EX_ICON;
                    btn.title = 'Exit fullscreen';
                    target.style.background = '#f0f4f8';
                    target.style.padding    = '24px';
                    target.style.overflow   = 'auto';
                    // Resize Plotly so the chart fills the screen
                    if (window.Plotly) { window.Plotly.Plots.resize(el); }
                    target._fsStyle = savedStyle;
                }).catch(function () {});
            } else {
                document.exitFullscreen().then(function () {
                    btn.innerHTML = FS_ICON;
                    btn.title = 'Fullscreen';
                    if (target._fsStyle) {
                        target.style.background = target._fsStyle.background;
                        target.style.padding    = target._fsStyle.padding;
                        target.style.overflow   = target._fsStyle.overflow;
                    }
                    if (window.Plotly) { window.Plotly.Plots.resize(el); }
                }).catch(function () {});
            }
        });

        // Reset icon when user presses Escape
        document.addEventListener('fullscreenchange', function () {
            if (!document.fullscreenElement) {
                btn.innerHTML = FS_ICON;
                btn.title = 'Fullscreen';
                if (window.Plotly) { window.Plotly.Plots.resize(el); }
            }
        });

        parent.appendChild(btn);
    }

    // Watch for Plotly charts added to the DOM (Dash renders them dynamically)
    var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (m) {
            m.addedNodes.forEach(function (n) {
                if (n.nodeType !== 1) return;
                if (n.classList && n.classList.contains('js-plotly-plot')) {
                    wrapPlot(n);
                }
                if (n.querySelectorAll) {
                    n.querySelectorAll('.js-plotly-plot').forEach(wrapPlot);
                }
            });
        });
    });

    document.addEventListener('DOMContentLoaded', function () {
        observer.observe(document.body, { childList: true, subtree: true });
        // Catch any charts already present on load
        document.querySelectorAll('.js-plotly-plot').forEach(wrapPlot);
    });
})();
