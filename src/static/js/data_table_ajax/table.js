
/**
 * @param {string} tableId
 * @param {any} columns
 */
function initServerTable(
    tableId,
    columns,
) {
    // @ts-ignore
    const $table = $(`#${tableId}`);
    const baseUrl = $table.data('ajax-url');
    const listName = tableId.replace(/^table-/, ''); // "table-files_skipped" -> "files_skipped"

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
            // @ts-ignore
            data: function (d) {
                // Remap DataTables' param names to your endpoint's names.
                // Drop this if you update the Flask view to accept start/length natively.
                d.limit = d.length;
                d.page = Math.floor(d.start / d.length) + 1;
            }
        },
        columns: columns,
        drawCallback: function (/** @type {{ json: { recordsTotal: number; }; }} */ settings) {
            const total = settings.json?.recordsTotal ?? 0;
            // @ts-ignore
            $(`#${listName}-title-total`).text(`(${total})`);
        },
    });
}
