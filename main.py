#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from flask import Flask
from flask import render_template, request
import requests
from bs4 import BeautifulSoup, Comment


def cutting_scripts_and_css(string):
    """
        Function find style, scripts and also links tag on the page
        and then cut all contents, scripts and styles
        if scripts, style not found on the page, return original string
        :param string: entire html page
        :return: return string of modified html page
    """
    string = string.decode('utf-8', 'ignore')
    re_pattern = r'<script.+?</script>|<style.+?</style>'
    search_for_css_js = re.search(re_pattern, string)
    if search_for_css_js:
        result = re.sub(re_pattern + r'|(<link[^>]+\.(js|css).+?>)', '', string, flags=re.DOTALL)
        return result
    return string


def modify_page_link(page, url):
    """
        Function find all link tags on the page, and then prepend each tag href attribute, string with
        get_url_site function handler, for recursively modify contents page
        :param page: Beautiful soup object with html page
        :param url: url address with current modifiable html page
        :return: Beautiful soup html page object
    """
    domain_name_pattern = re.compile(r'^(http(s?):)?//(?:[a-z0-9](?:[a-z0-9-]{0,61}'
                                     r'[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]')
    get_url_site = "/get_url_site?url_site="
    for link in page.find_all('a'):
        if not link.has_attr('href'):
            continue
        domain_name = re.search(domain_name_pattern, link['href'])
        if domain_name:
            domain_name = domain_name.group()
            url_param = re.sub(domain_name, '', link['href'])
            if url_param:
                link['href'] = get_url_site + domain_name + url_param
            if domain_name.startswith('//'):
                link['href'] = get_url_site + 'http:' + domain_name + url_param
            link['href'] = get_url_site + domain_name
        else:
            domain_name = re.search(domain_name_pattern, url)
            if domain_name:
                url = domain_name.group()
            if not url.endswith('/'):
                url += '/'
            if link['href'].startswith('/'):
                link['href'] = re.sub(r'^/', '', link['href'])
            link['href'] = get_url_site + url + link['href']
    return page


def make_links_italic(page):
    """
        Function make all links on the page italic
        wrap all link tags in <i> tag
        :param page: Beautiful soup object entire html page
        :return: modified Beautiful soup object
    """
    for link in page.find_all('a'):
        link.wrap(page.new_tag('i'))
    return page


def make_bold_text(page):
    """
        Function make all word on the page greater than 5 char, bold.
        After find text element, create new tag span, add to it strings, if strings
        greater than 5 char, create tag bold, and add it to
        element span, after words is finish, replace tag, with new element span.
        :param page: Beautiful soup object entire html page
        :return: modified Beautiful soup object
    """
    for txt in page.body.find_all(text=True):
        if isinstance(txt, Comment):
            continue
        new_element = page.new_tag('span')
        for word in txt.split():
            if len(txt.split()) >= 2:
                word += ' '
            if len(word.strip()) > 5:
                new_tag = page.new_tag('b')
                new_tag.string = word
                new_element.append(new_tag)
            else:
                new_tag = page.new_tag('span')
                new_tag.string = word
                new_element.append(new_tag)
        txt.replaceWith(new_element)
    return page


def create_app():
    app = Flask(__name__, template_folder='templates')
    return app


app = create_app()


@app.route('/main', methods=['GET'])
def main():
    return render_template('index.html')


@app.route('/get_url_site', methods=['GET'])
def get_url_site():
    """
        Get url address from html form, then process html page,
        also in following, get urls address from links on the page
        :return: processed html page content
    """
    url = request.args.get('url_site')
    protocol = re.search(r'^http(s?)://', url)
    if not protocol:
        url = 'http://' + url
    req = requests.get(url)
    cut_contents = cutting_scripts_and_css(req.content)
    soup = BeautifulSoup(cut_contents, 'html.parser')
    soup = modify_page_link(soup, url)
    soup = make_bold_text(soup)
    soup = make_links_italic(soup)
    return soup.prettify()


if __name__ == '__main__':
    app.run(debug=True)
