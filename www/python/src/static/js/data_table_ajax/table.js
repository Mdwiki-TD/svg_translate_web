
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
    // log to console if table not found
    if (!$table.length) {
        console.error(`Table with id ${tableId} not found`);
        return;
    }
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
                delete d.columns; // Erases extensive column definitions from the string
                delete d.order; // Erases extensive column definitions from the string
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
