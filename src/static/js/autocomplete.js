
// @ts-ignore
const API_USER_AGENT = "Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; tools.copy-svg-langs@toolforge.org)";

/**
 * @param {any} inputSelector
 * @param {any} wikimedia_api_url
 */
function setupWikiAutocomplete(inputSelector, wikimedia_api_url) {
    // attach autocomplete behavior to input field
    $(inputSelector).autocomplete({
        delay: 300,
        minLength: 2,
        source: function (/** @type {{ term: any; }} */ request, /** @type {(arg0: any[]) => void} */ response) {
            // make AJAX request to Wikipedia API
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
                    psnamespace: 0,
                    psbackend: "CirrusSearch",
                    cirrusUseCompletionSuggester: "yes"
                },
                success: function (/** @type {{ query: { prefixsearch: any; }; }} */ data) {
                    // extract titles from API response and pass to autocomplete
                    var items = (data && data.query && data.query.prefixsearch) || [];
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
