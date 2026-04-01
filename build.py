import os
import requests
import feedparser
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone
import html

FEEDS = {
    "https://sriya-g.github.io/": "https://sriya-g.github.io/atom.xml",
    "https://adhithirumala.com": "https://adhithirumala.com/rss.xml"
}

def get_feed_url(site_url):
    site_url = site_url.rstrip('/')
    for k, v in FEEDS.items():
        if k.rstrip('/') == site_url:
            return v
    
    try:
        res = requests.get(site_url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        link = soup.find('link', type='application/rss+xml') or soup.find('link', type='application/atom+xml')
        if link and link.get('href'):
            href = link.get('href')
            if href.startswith('http'):
                return href
            else:
                return site_url + '/' + href.lstrip('/')
    except:
        pass
    return None

def to_iso8601(struct_time):
    if not struct_time: 
        return datetime.now(timezone.utc).isoformat()
    dt = datetime.fromtimestamp(time.mktime(struct_time), tz=timezone.utc)
    return dt.isoformat()

def main():
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    members = soup.find_all('div', class_='member')
    all_entries = []

    for member in members:
        site_link = member.find('div', class_='site').find('a')
        if not site_link: continue
        site_url = site_link['href']
        
        feed_url = get_feed_url(site_url)
        if not feed_url: continue
        
        old_latest = member.find('div', class_='latest-post')
        if old_latest:
            old_latest.decompose()
            
        print(f"Fetching {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                latest = feed.entries[0]
                
                for entry in feed.entries[:5]:
                    all_entries.append((entry, site_url))
                
                latest_post_div = soup.new_tag('div', attrs={'class': 'latest-post'})
                latest_post_div['style'] = 'margin-top: 8px; font-size: 0.9em; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
                
                prefix = soup.new_tag('span')
                prefix.string = "Latest: "
                latest_post_div.append(prefix)
                
                link_tag = soup.new_tag('a', href=latest.link, target='_blank')
                link_tag.string = latest.title
                latest_post_div.append(link_tag)
                
                member.append(latest_post_div)
        except Exception as e:
            print(f"Error parsing {feed_url}: {e}")

    def get_date(entry):
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return entry.published_parsed
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return entry.updated_parsed
        return time.gmtime(0)
        
    all_entries.sort(key=lambda x: get_date(x[0]), reverse=True)
    
    entries_xml = ""
    for entry, site_url in all_entries[:20]:
        title = html.escape(entry.title)
        link = html.escape(entry.link)
        updated = to_iso8601(get_date(entry))
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
        
        entries_xml += f"""
  <entry>
    <title>{title}</title>
    <link href="{link}"/>
    <id>{link}</id>
    <updated>{updated}</updated>
    <summary><![CDATA[{summary}]]></summary>
  </entry>"""

    atom_template = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>CS+Ling Webring</title>
  <link href="https://csplusling.github.io/feed.xml" rel="self"/>
  <link href="https://csplusling.github.io/"/>
  <updated>{datetime.now(timezone.utc).isoformat()}</updated>
  <id>https://csplusling.github.io/</id>
  <author>
    <name>CS+Ling Webring</name>
  </author>{entries_xml}
</feed>
"""
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(atom_template)

    # Format the HTML nicely (optional, but good to keep it readable)
    # Actually bs4 formatter can mess up some custom stuff. We'll just write string.
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

if __name__ == '__main__':
    main()
