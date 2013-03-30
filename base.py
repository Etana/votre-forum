# -*- coding: utf-8 -*-

import webapp2, cookielib, urllib2, re, urllib, datetime,cgi

from core import *

from bs4 import BeautifulSoup
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext import ndb

from ident import ident
'''
# file ident.py to add in current directory not included, with forum adress and admin identification, e.g :
ident = {'forum': 'http://forum.forumactif.com', 'username':'Gizmo', 'password': 'What did you expect?'}
'''

TARGET_URL = 'https://votre-forum.appspot.com'

TID=0
COOKIES=1

class P(ndb.Model):
    h= ndb.PickleProperty()
    c= ndb.PickleProperty()

class L(ndb.Model):
    l= ndb.StringProperty(repeated=True)
    t= ndb.StringProperty(repeated=True)

def connect(force=False):
    # garder les cookies
    connected= memcache.get('session')
    if force or connected is None:
        # connexion au forum
        page= urlfetch.fetch(
            ident['forum']+"/login.forum",
            payload=urllib.urlencode({
                'username': ident['username'], 'password': ident['password'],
                'login': 1, 'redirect': '/admin/', 'admin': 1,
            }),
            method=urlfetch.POST,
            follow_redirects = False
        )

        cookies= {"cookie": ";".join([ cookie for cookie in page.header_msg.getheaders('set-cookie') if "deleted" not in cookie ])}

        page= urlfetch.fetch(ident["forum"]+"/admin", headers=cookies, follow_redirects = False)

        tid= page.headers.get('location')[56:]
        connected= [tid, cookies]
        memcache.set('session', connected, 3540)
    return connected

def cleanurl(path_qs):

    if "%" in path_qs:
        path_qs= path_qs.split("%",1)[0]
    if '"' in path_qs:
        path_qs= path_qs.split('"',1)[0]

    if "?" in path_qs:
        path, query= path_qs.split("?",1)
    else:
        path= path_qs
        query=""

    if path[1:2]=="t":
        path="/t13-indexation-d-une-section"


    transforms= (('/admin/index.forum','/admin/'),('/admin','/admin/'))
    noattr= ('/abuse',)

    for transform in transforms:
        if transform[0]==path:
            path=transform[1]

    if path in noattr:
        return path

    parts= {}
    nparts={}
    if query:
        for part in query.split('&'):

            if part=="part=admin":
                continue

            if "=" in part:
                parts[part.split("=")[0]]= part.split("=")[1]
            else:
                parts[part]= None

        for attr in ("pid", "tid","admin_css_size","admin_style","change_display","extended_admin","key","search_keywords","username","report","no_editor","nohtmleditor","sort_method","Array","mark","move","ord","ord2","str","str2","l","order","submit","change_theme","theme_id","unwatch","search_where","start","watch","change_temp","change_version","keep_theme","restoration_theme","sortby","sort_order","theme","mark","highlight","avatarcategory","avatargallery","new_position","old_position","time","search_username","_","id", "action"):
            if attr in parts:
                if attr=="action" and parts[attr]!="duplicate":
                    continue
                if attr=="l" and parts[attr]=="miscvars":
                    continue
                elif attr=="id" and path=="/search":
                    continue
                del parts[attr]

        if len(parts):
            path+="?"+"&".join([ attr if parts[attr] is None else attr+"="+parts[attr] for attr in sorted(parts.keys(),cmp=attr_compare) ])

    return path

def attr_compare(x,y):
    ordered= ("p",)
    if x in ordered:
        if y in ordered:
            return -1 if ordered.index(x) < ordered.index(y) else 1
        else:
            return -1
    elif y in ordered:
        return 1
    else:
        return cmp(x,y)

class Path(webapp2.RequestHandler):
    def get(self):

        if self.request.headers.get('If-None-Match'):
            self.response.headers['Cache-Control'] = 'public'
            self.response.set_status(304)
            return

        path= cleanurl(self.request.path_qs[5:])
        if path != self.request.path_qs[5:]:
            self.redirect('/path'+path)
            return

        root= None

        paths= {path:None,"/":None}

        link= L.get_by_id(path)

        if link:
            currents= (link,)
        else:
            currents= ()

        while len(currents):

            newcurrents= []

            for current in currents:
                for i in range(len(current.l)):
                    if current.l[i] not in paths:
                        paths[current.l[i]]= ( current.t[i], current.key.id() )
                        newcurrents.append(current.l[i])
                    elif current.l[i]=="/":
                        paths["/"]= ( current.t[i], current.key.id() )
                        break
                if paths["/"]:
                   break

            if paths["/"]:
                break

            if len(newcurrents):
                newcurrents= ndb.get_multi([ ndb.Key("L",str(current))  for current in newcurrents ])
            else:
                newcurrents=()

            currents= []

            for current in newcurrents:
                if current:
                    currents.append(current)

        data= ""

        current= paths["/"]

        nodes= [("Index","/")]

        if current:
            while current:
                nodes.append((current[0],current[1]))
                prev= current
                current= paths[current[1]]

        bbcode= []
        markdown= []
        text= []
        fragments= []

        prev= nodes[0]

        for node in nodes:

            if node[1]==prev[1]:
                continue

            splitted_prev= prev[1].split('?',1)
            if len(splitted_prev)==1:
                splitted_prev.append([])
            else:
                splitted_prev[1]= splitted_prev[1].split('&')

            splitted_current= node[1].split('?',1)
            if len(splitted_current)==1:
                splitted_current.append([])
            else:
                splitted_current[1]= splitted_current[1].split('&')

            if splitted_prev[0]!=splitted_current[0]:
                new_fragment= node[1]
            else:
                passed=True
                for split in splitted_prev[1]:
                    if split not in splitted_current[1]:
                        passed=False
                        break

                if passed:
                    new_fragment='&'+'&'.join([ split for split in splitted_current[1] if split not in splitted_prev[1] ])
                else:
                    new_fragment='?'+'&'.join(splitted_current[1])

            fragments.append(urllib.quote(new_fragment, safe='$&~()*+;=!:@/?\''))
            prev= node

        i= 0
        for node in nodes:

            fragment= ','.join(fragments[i:])
            if fragment:
                fragment="#"+fragment

            text.append(node[0])
            bbcode.append('[url='+TARGET_URL+node[1]+fragment+']'+node[0]+'[/url]')
            markdown.append('[`'+node[0]+'`]('+TARGET_URL+node[1]+fragment+')')
            i += 1

        data+='<table><tr><th>Type</th><th class="third">BBCode</th><th class="third">Markdown</th></tr>'

        if paths["/"] is not None:
            data+='<tr><td>Complet</td><td><input value="'+' &gt; '.join(bbcode)+'" /></td>'
            data+='<td><input value="'+' &gt; '.join(markdown)+'" /></td></tr>'

            fragment= ','.join(fragments[0:])
            if fragment:
                fragment="#"+fragment

            data+='<tr><td>D&eacute;part</td><td><input value="[url='+TARGET_URL+fragment+']'+' &gt; '.join(text)+'[/url]" /></td>'
            data+='<td><input value="[`'+' &gt; '.join(text)+'`]('+TARGET_URL+fragment+')" /></td></tr>'

        url= TARGET_URL+path

        data+='<tr><td>Arriv&eacute;e</td><td><input value="[url='+url+']'+' &gt; '.join(text)+'[/url]" /></td>'
        data+='<td><input value="[`'+' &gt; '.join(text)+'`]('+url+')" /></td></tr></table>'

        path_content= data

        datemodif= datetime.datetime.now() - datetime.timedelta(365)
        self.response.headers['Last-Modified'] = datemodif.strftime("%a, %d %b %Y %H:%M:00 GMT")
        self.response.headers['Cache-Control'] = 'public'
        date= datetime.datetime.now() + datetime.timedelta(365)
        self.response.headers['Expires'] = date.strftime("%a, %d %b %Y %H:%M:00 GMT")

        self.response.write(path_template.format(path=path,path_content=data.encode('utf-8')))

class Proxy(webapp2.RequestHandler):
    def get(self):
        if self.request.headers.get('If-Modified-Since'):
            self.response.set_status(304)
            return

        goodpath= cleanurl(self.request.path_qs)


        path= goodpath

        if path != self.request.path_qs:
            self.redirect(path)
            return

        if goodpath=="/improvedsearch.xml":
            datemodif= datetime.datetime.now() - datetime.timedelta(365)
            self.response.headers['Last-Modified'] = datemodif.strftime("%a, %d %b %Y %H:%M:00 GMT")
            self.response.headers['Cache-Control'] = 'public'
            date= datetime.datetime.now() + datetime.timedelta(365)
            self.response.headers['Expires'] = date.strftime("%a, %d %b %Y %H:%M:00 GMT")
            return
        elif goodpath=="/robots.txt":
            self.response.content_type= "text/plain"
            datemodif= datetime.datetime.now() - datetime.timedelta(365)
            self.response.headers['Last-Modified'] = datemodif.strftime("%a, %d %b %Y %H:%M:00 GMT")
            self.response.headers["ETag"]= "1"
            self.response.headers['Cache-Control'] = 'public'
            date= datetime.datetime.now() + datetime.timedelta(365)
            self.response.headers['Expires'] = date.strftime("%a, %d %b %Y %H:%M:00 GMT")
            return



        page= P.get_by_id(goodpath)
        if page:
            if "location" in page.h:
                self.redirect(page.h["location"])
                return
            self.response.headers= page.h
            self.response.write(page.c)
            return

        session= connect()

        if self.request.path=="/admin/" or self.request.path=="/modcp":
            if self.request.query_string:
                path+="&"
            else:
                path+="?"
            path+="tid="+session[TID]

        page= urlfetch.fetch('http://votre-forum.forumactif.com'+path,follow_redirects = False, headers=session[COOKIES])
        if "location" in page.headers and page.headers['location'].startswith('http://votre-forum.forumactif.com/login?redirect='):
            session = connect(True)
            page= urlfetch.fetch('http://votre-forum.forumactif.com'+path,follow_redirects = False, headers=session[COOKIES])

        content= page.content

        tid= re.findall('tid=([a-f0-9]{32})',page.content)

        if not tid:
            re.findall('<input name="tid" type="hidden" value="([a-f0-9]{32})"',page.content)


        if tid:
            if session[TID]!=tid[0]:
                session[TID]= tid[0]
                memcache.set('session', session, 3540)
            content= content.replace(session[TID],'TID')

        content= re.sub('\\d{1,3}\.\\d{1,3}\.\\d{1,3}\.\\d{1,3}','127.0.0.1', content)

        for header in ("set-cookie","cache-control","pragma","last-modified","x-xss-protection","x-content-type-options","via","p3p","age"):
            if header in page.headers: del page.headers[header]

        if "location" in page.headers:
            loc= re.sub('^http://votre-forum\.forumactif\.com', '', page.headers["location"])
            if len(loc) and loc[0]=="/":
                tid= re.findall('tid=([a-f0-9]{32})',loc)
                if tid:
                    if session[TID]!=tid[0]:
                        session[TID]= tid[0]
                        memcache.set('session', session, 3540)
                loc= cleanurl(loc)
                if loc == goodpath:
                    connect(True)
                    self.response.write("Page non visitable (location)")
                    return
                loc= self.request.host_url+loc
            page.headers["location"]= loc
            if not loc.startswith('/login?redirect='):
                P(id=goodpath,h=page.headers,c=content).put()
            self.redirect(page.headers["location"])
            return

        if 'META HTTP-EQUIV' in content:
            connect(True)
            self.response.write("Page non visitable (meta)")
            return

        page.headers['Cache-Control'] = 'public'
        datemodif= datetime.datetime.now() - datetime.timedelta(365)
        page.headers['Last-Modified'] = datemodif.strftime("%a, %d %b %Y %H:%M:00 GMT")
        date= datetime.datetime.now() + datetime.timedelta(365)
        page.headers['Expires'] = date.strftime("%a, %d %b %Y %H:%M:00 GMT")

        self.response.headers= page.headers

        headclose= content.find('</head>')
        if(headclose!=-1):
            content=content[:headclose]+'<script src="/s.js"></script>'+content[headclose:]

            if self.request.path=="/admin/":
                content= content.replace('>forumactif<','>appspot<').replace(ident['forum'].rpartition('/')[2],TARGET_URL.rpartition('/')[2]).replace('.forumactif.com<input type="hidden" value="forumactif.com"','.appspot.com<input type="hidden" value="appspot.com"')
            if self.request.path=="/abuse":
                content= content.replace(ident['forum'],TARGET_URL)

            soup = BeautifulSoup(content)


            # retirer pub
            elem= soup.find('div', {'id':'main-content'})
            if elem and elem.contents and elem.contents[0] and elem.contents[0].has_key('class'):
                    del elem.contents[0]

            for a in soup.find_all("form",action=True):
                if len(a["action"]) > 1 and a["action"][0]=="/" and a["action"][1]!="/":
                    a["action"]= cleanurl(a["action"])
                    submit = a.find_all(type='submit')
                    if a["action"]!=goodpath and submit:
                        txt= unicode(submit[0].get('value') or submit[0].get_text()).strip().encode('utf-8')

                        link= L.get_by_id(a["action"])

                        if not link:
                            link= L(id=a["action"])

                        if goodpath not in link.l:
                            link.l.append(goodpath)
                            link.t.append(txt)
                            link.put()
                        elif txt != "" and link.t[link.l.index(goodpath)]=="":
                            link.t[link.l.index(goodpath)]= txt
                            link.put()

            for a in soup.find_all("a",href=True):
                if len(a["href"]) > 1 and a["href"][0]=="/" and a["href"][1]!="/":

                    a["href"]= cleanurl(a["href"])
                    if a["href"]!=goodpath:
                        prepend=""
                        if "/admin/" == a["href"] or "/admin/?" == a["href"][0:8]:
                            if a.parent.has_key('id') and a.parent["id"]=="activesubmenu" or a.parent.has_key('class') and a.parent["class"][0]=="submenu":
                                prepend=a.parent.parent.previous_sibling.previous_sibling.get_text().strip().encode('utf-8')+" | "
                        txt= prepend+a.get_text().strip().encode('utf-8')

                        link= L.get_by_id(a["href"])

                        if not link:
                            link= L(id=a["href"])

                        if goodpath not in link.l:
                            link.l.append(goodpath)
                            link.t.append(txt)
                            link.put()
                        elif txt != "" and link.t[link.l.index(goodpath)]=="":
                            link.t[link.l.index(goodpath)]= txt
                            link.put()

            for a in soup.find_all("iframe",src=True):
                if len(a["src"]) > 1 and a["src"][0]=="/" and a["src"][1]!="/":
                    a["src"]= cleanurl(a["src"])

            content = soup.prettify(formatter=None)
            #content = str(soup)


        P(id=goodpath,h=page.headers,c=content).put()
        self.response.write(content)
    def post(self):
        self.redirect(self.request.url)

class Flush(webapp2.RequestHandler):
    def get(self):
        results = P.query().fetch(keys_only=True)
        for key in results:
            key.delete()

        results = L.query().fetch(keys_only=True)
        for key in results:
            key.delete()
        # ndb.delete_multi(results)
        self.response.write("emptied datastore")


app = webapp2.WSGIApplication([('/__FLUSHALL__',Flush),('/path/.*',Path),('/.*', Proxy)],
                              debug=True)

path_template='''<html>
<head>
    <title>{path}</title>
    <link rel="stylesheet" type="text/css" href="http://fa-tvars.appspot.com/github.css" />
    <style>
        button{{color:#FFF;background-color:#6199df;border:1px solid #4d90fe;font-weight:700;}}
         button,textarea{{padding:6px 10px;}}
        textarea{{border:1px solid #bbb; width: 100%; display: block; height: 200px;}}
        textarea,body{{color:#333;font-family:arial,serif;}}
        a{{color:#15c;}}
        h1{{font-weight:700;}}
        table {{ table-layout: fixed; width: 99%; }}
        td {{ vertical-align: top; width: 50%; }}
        .third {{ width: 45%; }}
        .note {{ color: #777; font-size: 0.8em; font-style: italic; }}
        .markdown-body {{ border: 1px solid #CACACA; margin: 5px; margin-top:0; padding: 10px; overflow: auto; }}
        .preview .markdown-body, .preview textarea {{ height: 100px; padding: 0; }}
        table {{ margin-top: 20px; }} th{{color:#FFF;background-color:#6199df;border:1px solid #4d90fe;font-weight:700;}}th,td{{padding:6px 10px;}}td{{border:1px solid #bbb;}}table{{border-collapse:collapse;text-align:left;font-size:13px;}}body{{color:#333;font-family:arial,serif;}}a{{color:#15c;}}h2{{font-weight:700;color:#404040;margin-top:1em;}} td input {{ width: 100%; border: 0; color: #555; font-family: Consolas, "Liberation Mono", Courier, monospace; }}
    </style>
</head>
<body>
    <h1><a href="{path}">{path}</a></h1>
    <h2>Chemins</h2>
    {path_content}
    <div id="footer"><div class="container"><ul id="legal"><li><a href="/">Index</a></li><li><a href="/admin/">Panneau d'administration</a></li><li><a href="http://forum.forumactif.com/t78679-listing-des-questions-reponses-frequentes#2328325">Questions fréquentes</a></li><li><a href="http://forum.forumactif.com/t94973-listing-des-trucs-astuces#2353857">Trucs et Astuces</a></li><li><a href="https://github.com/Etana/template#readme">Github</a></li></ul></div></div>
</body>
</html>'''

