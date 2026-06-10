let _refreshTimer = null;
let _autoRefreshActive = false;

function startAutoRefresh() {
    _autoRefreshActive = true;
    const indicator = document.getElementById('auto-refresh-indicator');
    if (indicator) indicator.classList.remove('d-none');
    _refreshTimer = setInterval(function () {
        location.reload();
    }, 5000);
}

function stopAutoRefresh() {
    clearInterval(_refreshTimer);
    _refreshTimer = null;
    _autoRefreshActive = false;
    const indicator = document.getElementById('auto-refresh-indicator');
    if (indicator) indicator.classList.add('d-none');
}

function toggleAutoRefresh() {
    if (_autoRefreshActive) {
        stopAutoRefresh();
        history.replaceState(null, '', window.location.pathname + window.location.search);
    } else {
        location.hash = 'AutoRefresh';
        startAutoRefresh();
    }
}

(function () {
    if (window.location.hash === '#AutoRefresh') {
        startAutoRefresh();
    }
})();
