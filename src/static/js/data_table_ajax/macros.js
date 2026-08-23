
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
 * @param {string} wiki_domain
 * @param {string} title
 * @param {string | null} label
 * @return {string}
 */

function renderWikiLink(wiki_domain, title, label = null) {
    if (!title) return '-';

    let display_label = label || title;

    const url = `https://${wiki_domain}/wiki/` + encodeURIComponent(title.replace(/ /g, '_'));
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${display_label}</a>`;
}

/**
 * @param {string} title
 * @param {any} _type
 * @param {any} _row
 * @return {string}
 */
function renderCommonsFileLinkShort(title, _type, _row) {
    if (!title) return '-';
    const striped = title.replace('File:', '');
    return renderWikiLink("commons.wikimedia.org", `File:${striped}`, "File");
}
/**
 * @param {string} title
 * @param {string} label
 * @return {string}
 */
function renderCommonsFileLink(title, label = '') {
    if (!title) return '-';
    const striped = title.replace('File:', '');
    const displayLabel = label || `File:${striped}`;

    return renderWikiLink("commons.wikimedia.org", `File:${striped}`, displayLabel);
}
/**
 * @param {string} title
 * @param {any} _type
 * @param {any} _row
 * @return {string}
 */
function renderCommonsLink(title, _type, _row) {
    return renderWikiLink("commons.wikimedia.org", title);
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
            return diffLink("commons.wikimedia.org", step.newrevid, title);
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

/**
 * @param {string} wiki_domain
 * @param {number} newrevid
 * @param {string | null} title
 */
function diffLink(wiki_domain, newrevid, title = null) {
    if (newrevid && newrevid !== 0) {
        const diffUrl = `https://${wiki_domain}/w/index.php?diff=${newrevid}`;
        const title_attr = title ? `title="${title}"` : '';
        return `<a href="${diffUrl}" target="_blank">
                    <span class="badge bg-success" ${title_attr}>
                        <i class="bi bi-check-lg"></i> Diff
                    </span>
                </a>
        `;
    }
    return `<span class="text-muted">-</span>`;
}

/**
 * Render template title, stripping "Template:OWID/" prefix.
 * @param {string} wiki_domain
 * @param {string} title
 */
function renderOwidTemplate(wiki_domain, title) {
    if (!title) return '-';
    const display = title.replace(/^Template:OWID\//, '');
    return renderWikiLink(wiki_domain, title, display);
}
