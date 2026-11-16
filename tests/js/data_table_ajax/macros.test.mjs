import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(
    new URL('../../../www/python/src/static/js/data_table_ajax/macros.js', import.meta.url),
    'utf8',
);
const context = {};
vm.createContext(context);
vm.runInContext(source, context);

const { renderCommonsFileLink, renderStep } = context;
const expectedUrl = 'https://commons.wikimedia.org/wiki/File%3ADirect_democracy_index%2C_AGO.svg';

// This mirrors each DataTables column wrapper: only the title is forwarded.
const renderFileColumn = (title) => renderCommonsFileLink(title);

test('renders the file title when DataTables supplies additional renderer metadata', () => {
    const dataTablesMeta = { row: 0, col: 1, settings: {} };
    const result = renderFileColumn(
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

test('uses an explicit label supplied as the second argument', () => {
    const result = renderCommonsFileLink('File:Example.svg', 'Cropped');

    assert.equal(
        result,
        '<a href="https://commons.wikimedia.org/wiki/File%3AExample.svg" target="_blank" rel="noopener noreferrer">Cropped</a>',
    );
});

test('keeps the existing placeholder for an empty title', () => {
    assert.equal(renderCommonsFileLink(''), '-');
});

test('renderStep links the diff when newrevid is a top level field', () => {
    const result = renderStep({ result: true, msg: 'Updated page: File:Example.svg', newrevid: 123 });

    assert.match(result, /href="https:\/\/commons.wikimedia.org\/w\/index.php\?diff=123"/);
    assert.match(result, /Diff/);
});

test('renderStep links the diff when newrevid is kept inside details', () => {
    const result = renderStep({
        result: true,
        msg: 'Updated page: File:Example.svg',
        details: { langs: ['ar'], newrevid: 1301773342, summary: 'Insert Svg lang (ar)' },
    });

    assert.match(result, /href="https:\/\/commons.wikimedia.org\/w\/index.php\?diff=1301773342"/);
    assert.match(result, /title="Updated page: File:Example.svg"/);
});

test('renderStep falls back to the success badge without a revision id', () => {
    const result = renderStep({ result: true, msg: 'ok', details: null });

    assert.match(result, /badge bg-success/);
    assert.doesNotMatch(result, /\?diff=/);
});

test('renderStep renders the placeholder for a missing step (old jobs)', () => {
    assert.equal(renderStep(undefined), '<span class="text-muted">-</span>');
});
