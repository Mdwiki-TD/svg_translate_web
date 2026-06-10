let _refreshTimer = null;
let _autoRefreshActive = false;

function toggleAutoRefresh() {
    const indicator = document.getElementById('auto-refresh-indicator');
    if (_autoRefreshActive) {
        clearInterval(_refreshTimer);
        _refreshTimer = null;
        _autoRefreshActive = false;
        if (indicator) indicator.classList.add('d-none');
    } else {
        _autoRefreshActive = true;
        if (indicator) indicator.classList.remove('d-none');
        _refreshTimer = setInterval(function () {
            location.reload();
        }, 5000);
    }
}
