
const API_USER_AGENT = "Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; tools.copy-svg-langs@toolforge.org)";

function setupWikiAutocomplete(inputSelector, wikimedia_api_url) {
    // attach autocomplete behavior to input field
    $(inputSelector).autocomplete({
        delay: 300,
        minLength: 2,
        source: function (request, response) {
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
                success: function (data) {
                    // extract titles from API response and pass to autocomplete
                    var items = (data && data.query && data.query.prefixsearch) || [];
                    response($.map(items, function (item) {
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
