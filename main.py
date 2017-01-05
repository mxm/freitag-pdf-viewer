from pprint import pprint
from urllib import parse
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from flask import Flask, Response, render_template_string, url_for
import os

app = Flask(__name__)

user = os.environ['FREITAG_USER']
password = os.environ['FREITAG_PASS']

GENERAL_POST = {
    'apikey': 'BsAvuNIFHuEXbvqPpApIhLkscQbdPYypkYPuGirSLRXkmfVLLSfdoNKBcEQDkZEH',
    'vs' : '2.0',
}

GENERAL_HEADERS = {
    "User-Agent" : "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.6.01001",
    "Referer" : "https://digital.freitag.de/"
}


class LoginContext:

    def __init__(self, session_secret):
        self.session_secret = session_secret
        self.headers = GENERAL_HEADERS.copy()
        self.headers['Cookie'] = "boSession=%s" % session_secret

    def _url_request(self, url):
        request = Request(url, urlencode(GENERAL_POST).encode(), self.headers)
        return urlopen(request)

    def list_issues(self):
        issues_url = "https://digital.freitag.de/padnity/issues?callback=blub"

        response2 = self._url_request(issues_url)
        json_response = response2.read().decode()[5:-1]
        json_response = json.loads(json_response)
        pprint(json_response)
        return json_response

    def get_download_link(self, i, issues_list = None):
        if not issues_list:
            issues_list = self.list_issues()
        return issues_list[i]['download_link']

    def list_download_links(self):
        issues_list = self.list_issues()
        for i, issue in enumerate(issues_list):
            print(i, self.get_download_link(i, issues_list))

    def logout(self):
        request = self._url_request("https://digital.freitag.de/padnity/sso/logout?callback=blub")
        request.close()

@app.route('/')
def index():
    login_context = login()
    issues = login_context.list_issues()

    return render_template_string("""
        <h1>Welcome to Freitag Viewer!</h1>
        Here are all available issues:
            <ul>
                {% for issue in issues %}
                    <li>
                        {% if issue.download_link != '' %}
                        <a href="{{ url_for('download', cookie=login_context.session_secret, name=issue.name, url=issue.download_link) }}">
                        {% endif %}
                            {{ issue.published }} - {{ issue.name }}
                        {% if issue.download_link != '' %}
                        </a>
                        {% endif %}
                    </li>
                {% endfor %}
            <ul>
    """, issues=issues, login_context=login_context)

@app.route('/download/<string:cookie>/<string:name>/<path:url>')
def download(cookie, name, url):
    login_context = LoginContext(cookie)

    request = login_context._url_request(url)
    headers = {
        "Content-Type" : "application/pdf",
        "Content-Disposition" : "attachment; filename*=UTF-8'%s.pdf" % parse.quote_plus(name)
    }
    def generate():
        while True:
            bytes = request.read(128)
            if len(bytes) != 0:
                yield bytes
            else:
                login_context.logout()
                break
    return Response(generate(), headers=headers)


def login():
    login_url = "https://digital.freitag.de/padnity/sso/login?callback=blub"
    post_fields = GENERAL_POST.copy()
    post_fields.update({
        'username' : user,
        'userpass' : password,
    })
    request = Request(login_url, urlencode(post_fields).encode())
    response = urlopen(request)
    json_response = response.read().decode()[5:-1]
    json_response = json.loads(json_response)
    print(json_response)

    boSession = json_response['sso_session_id']
    print(boSession)

    return LoginContext(boSession)


if __name__ == '__main__':
    app.run("0.0.0.0", 9999)