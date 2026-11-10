
// @ts-ignore
const API_USER_AGENT = "toolforge tool/1.0 (https://tool.toolforge.org; tool@toolforge.org)";

/**
 * @param {any} inputSelector
 * @param {any} wikimedia_api_url
 */
function setupWikiAutocomplete(inputSelector, wikimedia_api_url, psnamespace="*") {
    // attach autocomplete behavior to input field
    // @ts-ignore
    $(inputSelector).autocomplete({
        delay: 300,
        minLength: 2,
        source: function (/** @type {{ term: any; }} */ request, /** @type {(arg0: any[]) => void} */ response) {
            // make AJAX request to Wikipedia API
            // @ts-ignore
            $.ajax({
                url: wikimedia_api_url,
                headers: {
                    'Api-User-Agent': API_USER_AGENT
                },
                dataType: "jsonp",
                data: {
                    action: "query",
                    list: "prefixsearch",
                    format: "json",
                    pssearch: request.term,
                    psnamespace: psnamespace,
                    psbackend: "CirrusSearch",
                    cirrusUseCompletionSuggester: "yes"
                },
                success: function (/** @type {{ query: { prefixsearch: any; }; }} */ data) {
                    // extract titles from API response and pass to autocomplete
                    var items = (data && data.query && data.query.prefixsearch) || [];
                    // @ts-ignore
                    response($.map(items, function (/** @type {{ title: any; }} */ item) {
                        return item.title;
                    }));
                },
                error: function () {
                    // On error, just show no suggestions
                    response([]);
                }
            });
        }
    });
}
