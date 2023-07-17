# Pelican Smart Links

A plugin for [Pelican](getpelican.com). It allows to insert links in posts/pages without specifying their full URLs. Instead, specify keywords in the href bit.

For example, supposing the site has an article with slug `tutorials-punctuation-commas`, repeteadly containing the words `commas` and `tutorial`, the link in the following sentence

```md
My three favorite things are eating my family and not using [commas](commas tutorial).
```

gets rewritten in the Pelican HTML output to

```html
My three favorite things are eating my family and not using <a href="/tutorials-punctuation-commas">commas</a>.
```

The plugin leaves the source untouched, but can optionally edit the markdown source if `SMART_LINKS_REWRITE_MD` is set to `True` in settings.
