
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
    return map[status] || 'secondary';
}

function renderStatus(status) {
    if (!status) return '-';
    const cls = statusClass(status);
    const label = status.charAt(0).toUpperCase() + status.slice(1);
    return `<small class="d-inline-flex px-2 py-1 fw-semibold text-${cls}-emphasis bg-${cls}-subtle border border-${cls}-subtle rounded-2">${label}</small>`;
}

function renderCommonsLink(title) {
    if (!title) return '-';
    const striped = title.replace('File:', '');
    const url = 'https://commons.wikimedia.org/wiki/File:' + encodeURIComponent(striped.replace(/ /g, '_'));
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">File:${striped}</a>`;
}

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

/**
 * @param {string} tableId
 * @param {boolean} show_download
 * @param {boolean} show_nested
 * @param {boolean} err_colmn
 */
function initServerTable(
    tableId,
    show_download = false,
    show_nested = true,
    err_colmn = false,
    show_status = false,
) {
    const $table = $(`#${tableId}`);
    const baseUrl = $table.data('ajax-url');
    const listName = tableId.replace(/^table-/, ''); // "table-files_skipped" -> "files_skipped"

    let columns = [
        {
            data: null,
            render: function (data, type, row, meta) {
                return meta.row + 1;
            },
        },
        {
            data: 'title', render: renderCommonsLink

        },
        {
            data: 'status',
            render: renderStatus,
            visible: show_status
        },
        {
            data: 'steps.download', render: renderStep, orderable: false,
            visible: show_download
        },
        {
            data: 'steps.nested', render: renderStep, orderable: false,
            visible: show_nested
        },
        {
            data: null,
            orderable: false,
            render: (row) =>
                row.steps?.translations?.details?.inserted ??
                row.steps?.inject?.details?.inserted_translations ?? ''
        },
        {
            data: null,
            orderable: false,
            render: (row) =>
                row.steps?.translations?.details?.updated ??
                row.steps?.inject?.details?.updated_translations ?? ''
        },
        {
            data: 'steps.inject',
            orderable: false,
            render: renderStep

        },
        {
            data: 'steps.upload',
            orderable: false,
            render: renderStep
        },
        {
            data: 'error',
            render: undefined,
            visible: err_colmn
        }
    ];

    $table.DataTable({
        responsive: true,
        serverSide: true,
        processing: true,
        columnDefs: [
            { targets: '_all', className: 'align-middle' }
        ],
        ajax: {
            url: baseUrl,
            type: 'GET',
            dataSrc: 'data',
            data: function (d) {
                // Remap DataTables' param names to your endpoint's names.
                // Drop this if you update the Flask view to accept start/length natively.
                d.limit = d.length;
                d.page = Math.floor(d.start / d.length) + 1;
            }
        },
        columns: columns,
        drawCallback: function (settings) {
            const total = settings.json?.recordsTotal ?? 0;
            $(`#${listName}-title-total`).text(`(${total})`);
        },
    });
}
