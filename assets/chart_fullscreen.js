'use strict';
/**
 * Injects a fullscreen button directly into every Plotly chart's modebar.
 * Uses Plotly.react() with modeBarButtonsToAdd to add a native-looking icon.
 * A WeakSet guard prevents infinite loops from the afterplot event.
 */
(function () {

    // Expand arrows icon (fits Plotly's internal coordinate system)
    var FS_ICON = {
        width: 24,
        height: 24,
        path: [
            // top-left arrow
            'M3 3 L9 3 L9 5 L5 5 L5 9 L3 9 Z',
            // top-right arrow
            'M15 3 L21 3 L21 9 L19 9 L19 5 L15 5 Z',
            // bottom-left arrow
            'M3 15 L5 15 L5 19 L9 19 L9 21 L3 21 Z',
            // bottom-right arrow
            'M19 15 L21 15 L21 21 L15 21 L15 19 L19 19 Z',
        ].join(' ')
    };

    var EX_ICON = {
        width: 24,
        height: 24,
        path: [
            // contract arrows (pointing inward)
            'M9 3 L9 9 L3 9 L3 7 L7 7 L7 3 Z',
            'M15 3 L17 3 L17 7 L21 7 L21 9 L15 9 Z',
            'M3 15 L9 15 L9 21 L7 21 L7 17 L3 17 Z',
            'M15 15 L21 15 L21 17 L17 17 L17 21 L15 21 Z',
        ].join(' ')
    };

    // Tracks plots currently being enhanced to prevent re-entrant afterplot loops
    var enhancing = typeof WeakSet !== 'undefined' ? new WeakSet() : null;

    function isEnhancing(gd) {
        return enhancing ? enhancing.has(gd) : gd.__fsEnhancing;
    }
    function setEnhancing(gd, val) {
        if (enhancing) { val ? enhancing.add(gd) : enhancing.delete(gd); }
        else { gd.__fsEnhancing = val; }
    }

    function hasOurButton(gd) {
        return !!gd.querySelector('.modebar-btn[data-title="Fullscreen"]');
    }

    function injectButton(gd) {
        if (isEnhancing(gd)) return;   // prevent afterplot → react → afterplot loop
        if (!window.Plotly) return;
        if (hasOurButton(gd)) return;  // already injected (e.g. hover re-show)

        setEnhancing(gd, true);

        var currentIcon = document.fullscreenElement === gd ? EX_ICON : FS_ICON;

        var cfg = Object.assign({}, gd._context || {});
        // Strip any previous version of our button
        cfg.modeBarButtonsToAdd = (cfg.modeBarButtonsToAdd || []).filter(function (b) {
            return !b._isFullscreenBtn;
        }).concat([{
            _isFullscreenBtn: true,
            name: 'Fullscreen',
            title: 'Fullscreen',
            icon: currentIcon,
            click: function (gd) {
                if (!document.fullscreenElement) {
                    gd.requestFullscreen().catch(function () {});
                } else {
                    document.exitFullscreen().catch(function () {});
                }
                // Re-draw button icon and resize chart after transition
                setTimeout(function () {
                    setEnhancing(gd, false);
                    injectButton(gd);
                    if (window.Plotly) window.Plotly.Plots.resize(gd);
                }, 250);
            }
        }]);

        window.Plotly.react(gd, gd.data, gd.layout, cfg);

        // Release lock after Plotly.react fires its own afterplot
        setTimeout(function () { setEnhancing(gd, false); }, 400);
    }

    // Plotly fires this on every render (initial + Dash callback updates)
    document.addEventListener('plotly_afterplot', function (e) {
        injectButton(e.target);
    }, true /* capture phase — fires before bubble */);

    // Also catch any charts already on the page at script load time
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.js-plotly-plot').forEach(injectButton);
    });

    // Keep icon in sync when user presses Escape to exit fullscreen
    document.addEventListener('fullscreenchange', function () {
        document.querySelectorAll('.js-plotly-plot').forEach(function (gd) {
            if (window.Plotly) window.Plotly.Plots.resize(gd);
            // Force re-inject so the icon flips
            setEnhancing(gd, false);
            injectButton(gd);
        });
    });

}());
