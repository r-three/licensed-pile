# Wiki Scrapes
##

These tools are designed for getting data from mediawiki wikis that don't publish dumps.

## Data Download

These steps are to be completed for each wiki that we are scraping.

1. Find all the namespaces that pages are listed under with `python get_namespaces.py --wiki ${wiki_url}`. This saves a mapping of namespace names to id's in `data/${wiki_name}/namespaces.json`.
2. Get all the pages under each namespace by following pagenation links using `python list_pages.py --wiki ${wiki_url} -ns 0 -ns 1...`. The namespaces we want to scrape are generally:
  * `(Main)`: 0
  * `Talk`: 1
  * `UserTalk`: 3
Either the integer or the name can be used as input. This generates lists of page titles at `data/${wiki_name}/pages/${ns}.txt`.
3. Copy these page titles (`cat data/${wiki_name}/pages/* | xclip -sel clip`) and paste them into the `add pages manually` textbox at `${wiki_url}/Special:Export`. **Uncheck `Include only the current revision, not the full history`** and **click Export**.

This will return an xml file with information about each page we included in the textbox.  By getting the full history we will be able to get the full author list for each page by looking at revision data.

**TODO**: Figure out how to programatically do the export step instead of using the web browser.
