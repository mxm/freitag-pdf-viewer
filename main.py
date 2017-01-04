from pprint import pprint
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from flask import Flask, Response
import os

app = Flask(__name__)

user = os.environ['FREITAG_USER']
password = os.environ['FREITAG_PASS']

GENERAL_POST = {
    'apikey': 'BsAvuNIFHuEXbvqPpApIhLkscQbdPYypkYPuGirSLRXkmfVLLSfdoNKBcEQDkZEH',
    'vs' : '2.0',
}

HEADERS = {
    "User-Agent" : "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.6.01001",
    "Referer" : "https://digital.freitag.de/"
}

CACHED_LINKS = {}

def url_request(url, headers = {}, **kwargs):
    request = Request(url, urlencode(kwargs).encode(), headers)
    return urlopen(request)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/download/<int:offset>')
def download(offset):
    global CACHED_LINKS
    if not offset in CACHED_LINKS.keys():
        link = get_download_link(offset, list_issues(login()))
        CACHED_LINKS[offset] = link

    request = url_request(link, HEADERS, **GENERAL_POST)
    headers = {
        "Content-Type" : "application/pdf",
        "Content-Disposition" : "attachment; filename*=UTF-8'%s.pdf" % offset
    }
    def generate():
        while True:
            bytes = request.read(128)
            if len(bytes) != 0:
                yield bytes
            else:
                break
    return Response(generate(), headers=headers, mimetype="")


def login():
    login_url = "https://digital.freitag.de/padnity/sso/login?callback=blub"
    post_fields = GENERAL_POST.copy()
    post_fields.update({
        'username' : user,
        'userpass' : password,
    })
    response = url_request(login_url, **post_fields)
    json_response = response.read().decode()[5:-1]
    json_response = json.loads(json_response)
    print(json_response)

    boSession = json_response['sso_session_id']
    HEADERS.update ({
        'Cookie': "boSession=%s" % boSession
    })

    print(boSession)
    return boSession

def list_issues(boSession):
    issues_url = "https://digital.freitag.de/padnity/issues?callback=blub"

    response2 = url_request(issues_url, HEADERS, **GENERAL_POST)
    json_response = response2.read().decode()[5:-1]
    json_response = json.loads(json_response)
    pprint(json_response)
    return json_response

def get_download_link(i, issues_list):
    return issues_list[i]['download_link']

def list_download_links(issues_list):
    for i, issue in enumerate(issues_list):
        print(i, get_download_link(i, issues_list))


if __name__ == '__main__':
    # list_download_links(list_issues(login()))

    app.run("0.0.0.0", 9999)