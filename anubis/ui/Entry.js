/**
 * Created by Nitori on 2017/1/3.
 */
__webpack_public_path__ = UiContext.cdn_prefix;

import 'jquery.transit';

import 'normalize.css/normalize.css';
import 'codemirror/lib/codemirror.css';

import {PageLoader} from './misc/PageLoader';
import delay from './util/delay';

const pageLoader = new PageLoader();

const currentPage = pageLoader.getNamedPage(document.documentElement.getAttribute('data-page'));
const includedPages = pageLoader.getAutoloadPages();

async function load() {
    const loadSequence = [
        ...includedPages.map(p => [p.beforeLoading, p]),
        [currentPage.beforeLoading, currentPage],
        ...includedPages.map(p => [p.afterLoading, p]),
        [currentPage.afterLoading, currentPage],
    ];
    for (const [func, page] of loadSequence) {
        if (typeof func !== 'function') {
            continue;
        }
        try {
            await func();
        } catch (e) {
            console.error(`Failed to load page ${page.name}\n${e.stack}`);
        }
    }
    for (const section of $('.section')) {
        const $section = $(section);
        $section.addClass('visible');
        await delay(100);
        $section.trigger('layout');
    }
}

load();