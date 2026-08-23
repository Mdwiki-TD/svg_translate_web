import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(
    new URL('../../../src/static/js/data_table_ajax/macros.js', import.meta.url),
    'utf8',
);
const context = {};
vm.createContext(context);
vm.runInContext(source, context);

const { renderCommonsFileLink } = context;
const expectedUrl = 'https://commons.wikimedia.org/wiki/File:Direct_democracy_index%2C_AGO.svg';

test('renders the file title when DataTables passes a metadata object as the fourth renderer argument', () => {
    const dataTablesMeta = { row: 0, col: 1, settings: {} };
    const result = renderCommonsFileLink(
        'Direct democracy index, AGO.svg',
        'display',
        { title: 'Direct democracy index, AGO.svg' },
        dataTablesMeta,
    );

    assert.equal(
        result,
        `<a href="${expectedUrl}" target="_blank" rel="noopener noreferrer">File:Direct democracy index, AGO.svg</a>`,
    );
    assert.doesNotMatch(result, /\[object Object\]/);
});

test('preserves explicit text labels supplied by direct callers', () => {
    const result = renderCommonsFileLink('File:Example.svg', null, null, 'Cropped');

    assert.equal(
        result,
        '<a href="https://commons.wikimedia.org/wiki/File:Example.svg" target="_blank" rel="noopener noreferrer">Cropped</a>',
    );
});

test('keeps the existing placeholder for an empty title', () => {
    assert.equal(renderCommonsFileLink('', 'display', {}, { row: 0 }), '-');
});
