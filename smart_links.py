import logging
import os
import re
from bs4 import BeautifulSoup
from pelican import signals, generators

log = logging.getLogger(__name__)


def get_pattern_relevance(pattern, content):
    pattern_pieces = pattern.split()
    if len(pattern_pieces) == 1:  # a simple method then
        relevance = content.lower().count(pattern)
    else:  # otherwise, a ~sloppy~ fancy regex thingy
        relevance = 0
        regex = r''
        i = 0
        while i < len(pattern_pieces):
            regex += r'\b' + pattern_pieces[i]
            i += 1
            if i < len(pattern_pieces):
                regex += '(.*?)'
        matches = re.findall(regex, content.lower(), re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                match = (match,)  # force to tuple
            if '. ' in ' '.join(match):  # ignore matches across sentences. Could exclude in the regex directly
                continue
            for separating_chars_group in match:
                # match relevance decreases depending on number of chars in between pattern pieces
                partial = 20 - len(separating_chars_group)**(4/5)
                if partial > 0:
                    relevance += partial
    return relevance


def get_best_match(href, all_generators, current_slug):
    result = []
    for entry in all_generators:
        if entry.slug == current_slug:
            continue
        url = entry.metadata.get('url') if entry.metadata.get('url') else entry.slug
        relevance = get_pattern_relevance(href, entry._content + entry.metadata['title'])
        result.append((relevance, entry.metadata))
    result.sort(key=lambda x: x[0], reverse=True)
    best = result[0]
    if best[0] > 0:
        return best[1]
    else:
        return False


def rewrite_link(entry, link, linked_entry):
    new_path = linked_entry['path_no_ext']
    new_href = '/' + new_path
    new_link = str(link).replace(link.attrs['href'], new_href)
    entry._content = entry._content.replace(str(link), new_link)  # rewrite html output
    if SMART_LINKS_REWRITE_MD:
        with open(entry.source_path, 'r+') as f:  # rewrite md source
            current_md = f.read()
            f.seek(0)
            f.write(re.sub(r"\[("+link.contents[0]+")\]\("+link.attrs['href']+"\)", fr"[\1]({new_href})", current_md))
            f.truncate()
    print(f"Replaced '{str(link)}' with '{new_path}'")


def parse_links(entry, all_generators):
    doc = BeautifulSoup(entry._content, features='lxml')
    links = doc.findAll('a')
    for l in links:
        # A link that does NOT start with http(s) or with / is a link we're gonna inspect
        if re.search(r'(https?://)|^/', l.attrs['href']) == None:
            best_match = get_best_match(l.attrs['href'], all_generators, entry.slug)
            if best_match != False:
                rewrite_link(entry, l, best_match)
            else:
                logging.warning(f"No match found for link '{str(l)}', leaving unchanged.")


def process_links(content_generators):
    # To group together all possible content to browse through when looking for
    # the best match. Allow cross links between posts and pages.
    all_generators = []
    for generator in content_generators:
        if isinstance(generator, generators.ArticlesGenerator):
            all_generators += generator.articles + generator.translations + generator.drafts
        elif isinstance(generator, generators.PagesGenerator):
            all_generators += generator.pages

    # Apply cross linking to posts and pages
    for generator in content_generators:
        if isinstance(generator, generators.ArticlesGenerator):
            for article in (
                    generator.articles +
                    generator.translations +
                    generator.drafts):
                parse_links(article, all_generators)
        elif isinstance(generator, generators.PagesGenerator):
            for page in generator.pages + generator.hidden_pages:
                parse_links(page, all_generators)


def pelican_init(pelican):
    global SMART_LINKS_REWRITE_MD
    SMART_LINKS_REWRITE_MD = pelican.settings.get('SMART_LINKS_REWRITE_MD', False)


def register():
    signals.initialized.connect(pelican_init)
    signals.all_generators_finalized.connect(process_links)
