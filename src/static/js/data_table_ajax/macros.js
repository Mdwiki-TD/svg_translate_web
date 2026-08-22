
/**
 * @param {string} status
 */

function statusClass(status) {
    // mirrors your `get_status_class` Jinja filter — inline the same logic here
    const map = {
        running: "primary",
        imported: "success",
        imported_fallback: "success",
        completed: "success",
        changed: "success",
        missing: "warning",
        skipped: "warning",
        cancelled: "warning",
        failed: "danger",
        error: "danger",
        errors: "danger",
        pending: "secondary",
    };
    // @ts-ignore
    return map[status] || 'secondary';
}

/**
 * @param {string} status
 */
function renderStatus(status) {
    if (!status) return '-';
    const cls = statusClass(status);
    const label = status.charAt(0).toUpperCase() + status.slice(1);
    return `<small class="d-inline-flex px-2 py-1 fw-semibold text-${cls}-emphasis bg-${cls}-subtle border border-${cls}-subtle rounded-2">${label}</small>`;
}

/**
 * @param {string} title
 * @param {any} label
 * @return {string}
 */
function renderCommonsFileLink(title, label) {
    if (!title) return '-';
    const striped = title.replace('File:', '');

    let display_label = `File:${striped}`
    if (label && label != "display") display_label = label;

    const url = 'https://commons.wikimedia.org/wiki/File:' + encodeURIComponent(striped.replace(/ /g, '_'));
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${display_label}</a>`;
}
/**
 * @param {string} title
 */
function renderCommonsLink(title) {
    if (!title) return '-';
    const url = 'https://commons.wikimedia.org/wiki/' + encodeURIComponent(title.replace(/ /g, '_'));
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}

/**
 * @param {{
 * msg: string | null;
 * message: string | null;
 * new_value: string;
 * value: string;
 * result: string | boolean | null;
 * newrevid: number | null;
 * }} step
 */
function renderStep(step) {
    if (!step) return '<span class="text-muted">-</span>';
    const title = step.msg || step.message || step.new_value || step.value || '';
    if (step.result === true || step.result === 'updated') {
        if (step.newrevid && step.newrevid !== 0) {
            const diffUrl = `https://commons.wikimedia.org/w/index.php?diff=${step.newrevid}`;
            return `<a href="${diffUrl}" target="_blank"><span class="badge bg-success" title="${title}"><i class="bi bi-check-lg"></i> Diff</span></a>`;
        }
        return `<span class="badge bg-success" title="${title}"><i class="bi bi-check-lg"></i></span>`;
    }
    if (step.result === false || step.result === 'failed') {
        return `<span class="badge bg-danger" title="${title}"><i class="bi bi-x-lg"></i></span>`;
    }
    if (step.result === null || step.result === undefined || step.result === 'skipped') {
        return `<span class="badge bg-secondary" title="${title}"><i class="bi bi-dash"></i></span>`;
    }
    return `<span class="text-muted" title="${title}">-</span>`;
}
