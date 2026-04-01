

class SvgTranslateApi {
    async get(file_name) {
        const API_AGENT = "Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; tools.copy-svg-langs@toolforge.org)";
        const end_point = 'https://svgtranslate.toolforge.org/api/languages/';
        const url = `${end_point}${file_name}`
        const res = await fetch(url, {
            headers: {
                'SvgTranslateApi-User-Agent': API_AGENT
            }
        });
        if (!res.ok) {
            throw new Error(`HTTP error ${res.status}`);
        }
        return res.json();
    }
}

async function getFileTranslations(fileName) {
    // return object { error, langs }
    if (!fileName) return { error: 'Empty fileName', langs: null };

    const normalizedName = fileName.replace(/^File:/i, '').trim();
    const api = new SvgTranslateApi();
    let data;
    try {
        // ["abr","ar","ca","cs","es","eu","fallback","gpe","id","pt","si","uk"]
        data = await api.get(normalizedName);

    } catch (err) {
        console.error('SvgTranslateApi error:', err);
        return { error: 'API error', langs: null };
    }

    const langs = data;
    if (!langs) return { error: 'Unexpected API response', langs: null };

    // If the file exists on Commons (shared repository)
    console.log(`ℹ️ File ${normalizedName} exists on Wikimedia Commons.`);

    // remove 'fallback' from langs
    if (langs.includes('fallback')) {
        langs.splice(langs.indexOf('fallback'), 1);
    }
    if (langs && langs.length) {
        return { error: null, langs: langs || ["en"] };
    }

    return { error: null, langs: ["en"] };
}

// Main per-item worker. Accepts jQuery-wrapped element
async function oneFile(item) {
    // const itemSpan = item.find("span") || item;
    const itemSpan = item;
    itemSpan.text("");
    const fileName = item.attr('data-file');

    if (!fileName || fileName === "" || fileName === "{{{1}}}") {
        itemSpan.text('Error: Could not find file name');
        return;
    }

    itemSpan.text('Loading languages');

    const { error, langs } = await getFileTranslations(fileName);
    if (!langs || langs.length === 0) {
        console.error(error);
        itemSpan.text(error || 'Error: Could not find file langs');
        return;
    }

    const result = (!langs || langs.length === 0)
        ? 'No languages found'
        : ' ' + langs.join(', ');

    itemSpan.text(result);
}

// Initialize: process all .get_languages elements concurrently but wait for all
async function initGetLanguages() {
    const divs = $('.get_languages');
    console.log('start initGetLanguages, get_languages divs: ', divs.length);

    if (!divs.length) return;

    // one by one
    divs.forEach(element => {
        oneFile($(element));
    });
    // convert to array of promises and run them concurrently
    // const promises = divs.toArray().map(el => oneFile($(el)));
    // await Promise.allSettled(promises);
}

// Document ready and load MediaWiki modules, then init
$(document).ready(function () {
    initGetLanguages();
});
