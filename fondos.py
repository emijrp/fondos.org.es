#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2017 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import math
import random
import re
import unicodedata
import urllib.parse
import urllib.request

translations = {
    "es": {
        "Africa": "África", 
        "Amphibians": "Anfibios", 
        "Antarctica": "Antártida", 
        "Architecture": "Arquitectura", 
        "Asia": "Asia", 
        "Astronomy": "Astronomía", 
        "Birds": "Aves", 
        "Europe": "Europa", 
        "Fish": "Peces", 
        "Insects": "Insectos", 
        "Mammals": "Mamíferos", 
        "Molluscs": "Moluscos", 
        "North America": "América del Norte", 
        "Objects": "Objetos", 
        "Oceania": "Oceanía", 
        "Oceans": "Océanos", 
        "Landscapes": "Paisajes", 
        "Plants": "Plantas", 
        "Reptiles": "Reptiles", 
        "South America": "América del Sur", 
        "Spiders": "Arañas", 
        "Transport": "Transporte", 
        "See info": "Ver info", 
    }, 
}
categories = {
    "Africa": ["Featured pictures of Africa"], 
    "Amphibians": ["Featured pictures of amphibians"], 
    "Antarctica": ["Featured pictures of Antarctica"], 
    "Architecture": ["Featured pictures of architecture"], 
    "Asia": ["Featured pictures of Asia"], 
    "Astronomy": ["Featured pictures of astronomy"], 
    "Birds": ["Featured pictures of birds"], 
    "Europe": ["Featured pictures of Europe"], 
    "Fish": ["Featured pictures of fish"], 
    "Insects": ["Featured pictures of insects"], 
    "Landscapes": ["Featured pictures of landscapes"], 
    "Mammals": ["Featured pictures of mammals"], 
    "Molluscs": ["Featured pictures of molluscs"], 
    "North America": ["Featured pictures of North America"], 
    "Objects": ["Featured pictures of objects"], 
    "Oceania": ["Featured pictures of Oceania"], 
    "Oceans": ["Featured pictures of oceans"], 
    "Plants": ["Featured pictures of plants"], 
    "Reptiles": ["Featured pictures of reptiles"], 
    "South America": ["Featured pictures of South America"], 
    "Spiders": ["Featured pictures of spiders"], 
    "Transport": ["Featured pictures of transport"], 
}

def removeaccents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
                  
def getAuthor(text=''):
    author = ''
    m = re.findall(r"(?im)\|\s*Author\s*=\s*(.*?)\n", text)
    if m:
        author = m[0].strip()
    author = re.sub(r"(?im)<[^<>]+?>([^<>]*?)<[^<>]+?>", r"\1", author) #<b><i>...
    author = re.sub(r"(?im)\'\'+", r"", author) #'''
    author = re.sub(r"(?im)\[\[\s*\:?\s*(Image|File)\s*:[^\[\]]*?\]\]", r"", author) #before removing [[]]
    author = re.sub(r"(?im)\[\[([^\[\]\|]*?)\|([^\[\]\|]*?)\]\]", r"\2", author)
    author = re.sub(r"(?im)\[\[([^\[\]\|]*?)\]\]", r"\1", author)
    author = re.sub(r"(?im)\[[^\[\]\| ]*? ([^\[\]\|]*?)\]", r"\1", author)
    author = re.sub(r"(?im)\{\{\s*User\s*:([^/\{\}]+?)/[^\{\}]*?\}\}", r"\1", author)
    author = re.sub(r"(?im)\{\{\s*Creator\s*:([^/\{\}]+?)\}\}", r"\1", author)
    author = re.sub(r"(?im)\{\{\s*user at project\s*\|([^|]*?)\|[^\{\}]*?\}\}", r"\1", author)
    return author.strip().strip('*').strip('.').strip()

def getThumb(url='', res=''):
    return re.sub(r"/commons/", r"/commons/thumb/", url) + '/' + res + '-' + url.split('/')[-1]

def getImagesFromCategory(commonscat=''):
    images = []
    gcmcontinue = "unknown"
    while gcmcontinue:
        query = 'https://commons.wikimedia.org/w/api.php?action=query&generator=categorymembers&gcmnamespace=6&gcmtitle='
        query += 'Category:' + re.sub(' ', '%20', commonscat)
        query += '&prop=imageinfo|revisions&iiprop=url|size&rvprop=content&format=json'
        if gcmcontinue and gcmcontinue != "unknown":
            query += '&gcmcontinue=' + gcmcontinue
        raw = getURL(query)
        if raw:
            json1 = json.loads(raw)
            if 'query' in json1:
                if 'pages' in json1['query']:
                    for page, props in json1['query']['pages'].items():
                        title = props["title"]
                        author = getAuthor(props["revisions"][0]["*"])
                        width = props["imageinfo"][0]["width"]
                        height = props["imageinfo"][0]["height"]
                        if height > width or \
                            width < 1920 or \
                            (width > height*2.5 or width < height*1.5):
                            continue
                        url = props["imageinfo"][0]["url"]
                        urldesc = props["imageinfo"][0]["descriptionurl"]
                        dic = {
                            "title": title, 
                            "url": url, 
                            "urldesc": urldesc, 
                            "urlthumb": getThumb(url=url, res='200px'), 
                            "author": author, 
                        }
                        images.append([title, dic])
            if 'continue' in json1:
                if 'gcmcontinue' in json1['continue']:
                    gcmcontinue = json1['continue']['gcmcontinue']
                    continue
        gcmcontinue = ''
    return images

def getSubcategories(commonscat=''):
    subcategories = [commonscat]
    gcmcontinue = "unknown"
    while gcmcontinue:
        query = 'https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmnamespace=14'
        query += '&cmtitle=Category:' + re.sub(' ', '%20', commonscat)
        query += '&format=json'
        if gcmcontinue and gcmcontinue != "unknown":
            query += '&gcmcontinue=' + gcmcontinue
        raw = getURL(query)
        json1 = json.loads(raw)
        if 'query' in json1:
            if 'categorymembers' in json1['query']:
                for cat in json1['query']['categorymembers']:
                    subcategories.append(cat["title"].split('Category:')[1])
        
        if 'continue' in json1:
            if 'gcmcontinue' in json1['continue']:
                gcmcontinue = json1['continue']['gcmcontinue']
                continue
        gcmcontinue = ''
    return subcategories

def getURL(url=''):
    raw = ""
    try:
        f = urllib.request.urlopen(url)
        raw = f.read()
        return raw.decode("utf-8")
    except:
        print("Error retrieving: %s" % url)
    return raw

def ga():
    ga_ = """<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-127978837-1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-127978837-1');
</script>"""
    return ga_

def main():
    lang = "es"
    menulist = []
    ctotal = set()
    maingallery = []
    gallerylimit = 25
    for catname, commonscats in categories.items():
        print(catname)
        filelabel = translations[lang][catname]
        filehtmlprefix = "%s" % (re.sub(' ', '-', translations[lang][catname].lower()))
        filehtmlprefix = removeaccents(filehtmlprefix)
        filehtml = "%s.html" % (filehtmlprefix)
        commonscats2 = commonscats
        for commonscat in commonscats2:
            commonscats = commonscats + getSubcategories(commonscat)
        commonscats = list(set(commonscats))
        commonscats.sort()
        c = 0
        gallery = []
        metacardimgsrc = ""
        for commonscat in commonscats:
            print(commonscat)
            images = getImagesFromCategory(commonscat)
            images.sort()
            for title, props in images:
                if c == 0:
                    metacardimgsrc = props["urlthumb"]
                galleryitem = """
<div class="picture">
<a href="%s" title="%s"><img src="%s" width="200px" height="140px" /></a>
<center>
<a href="%s">800px</a> · <a href="%s">1024px</a><br/>
<a href="%s">1240px</a> · <a href="%s">1440px</a><br/>
<a href="%s">1600px</a> · <a href="%s">1920px</a><br/>
<a href="%s">2048px</a> · <a href="%s">3200px</a>
</center>
<br/>
<center><a href="%s">%s</a> / Commons</center>
<br/>
</div>
""" % (props["urldesc"], props["title"], props["urlthumb"], getThumb(url=props["url"], res="800px"), getThumb(url=props["url"], res="1024px"), getThumb(url=props["url"], res="1240px"), getThumb(url=props["url"], res="1440px"), getThumb(url=props["url"], res="1600px"), getThumb(url=props["url"], res="1920px"), getThumb(url=props["url"], res="2048px"), getThumb(url=props["url"], res="3200px"), props["urldesc"], props["author"] and props["author"] or translations[lang]["See info"])
                gallery.append(galleryitem)
                if random.randint(0, 9) == 0:
                    if len(maingallery) == 0:
                        metacardimgsrcmain = props["urlthumb"]
                    maingallery.append(galleryitem)
                c += 1
                ctotal.add(title)
        #random.shuffle(gallery)
        cpage = 1
        while (cpage-1) * gallerylimit <= len(gallery):
            galleryplain = ''.join(gallery[(cpage-1) * gallerylimit:cpage * gallerylimit])
            menupages = ""
            if len(gallery) > gallerylimit:
                menupages = " ".join(['<a class="mw-ui-button mw-ui-blue" href="%s%s.html">%s</a>' % (filehtmlprefix, i != 1 and i or '', i) for i in range(1, int(math.ceil(len(gallery)/gallerylimit))+1)])
            output = """<!DOCTYPE html>
<html lang="es" dir="ltr">
<head>
    <title>Fondos de pantalla de %s</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    
    <meta name="twitter:title" content="Fondos de pantalla de %s"/>
    <meta name="keywords" content="fondos de pantalla de %s, fondos de escritorio de %s, wallpapers, imagenes de %s, fotos, pantalla, escritorio, descargar fondos, fondos gratis, fondos hd, fondos bonitos"/>
    <meta name="description" content="Una selección de los mejores fondos de pantalla de %s para tu ordenador. Revisa también nuestras otras categorías..."/>
    <meta name="twitter:description" content="Una selección de los mejores fondos de pantalla de %s para tu ordenador. Revisa también nuestras otras categorías..."/>
    <meta name="twitter:card" content="summary"/>
    <meta name="twitter:domain" content="http://fondos.org.es"/>
    <meta name="twitter:creator" content="Fondos.org.es"/>
    <meta name="twitter:image:src" content="%s"/>
    
    <link rel="stylesheet" href="style.css" />
</head>
<body>
<h1><a href="%s">Fondos de pantalla de %s</a></h1>

<p>Una selección de las mejores <b>imágenes de %s</b> extraídas de <a href="https://commons.wikimedia.org">Wikimedia Commons</a> para usarlas como fondos de escritorio. Un total de <b>%s fondos</b> de pantalla de excelente calidad con licencias libres. Haz click en las imágenes para consultar la información de autoría, licencia y descripciones.</p>

<p><a href="index.html">&lt;&lt; Volver a la portada</a></p>

<center>
%s

<div style="clear: both; float: center;margin-top: 5px;">
%s
</div>
</center>

<div class="footer">
<hr/>
<a href="http://wikis.cc">Crea tu wiki</a> · 
<a href="http://locapedia.wikis.cc">Crea una locapedia</a> · 
<a href="http://fondos.org.es">Fondos de pantalla</a> · 
<a href="http://librefind.org">LibreFind</a> · 
<a href="http://wikis.org.es">Locapedias</a>
</div>

%s
</body>
</html>""" % (translations[lang][catname], translations[lang][catname], translations[lang][catname], translations[lang][catname], translations[lang][catname], translations[lang][catname], translations[lang][catname], metacardimgsrc, filehtml, translations[lang][catname], translations[lang][catname], c, menupages, galleryplain, ga())
            if cpage == 1:
                menulist.append([filelabel, filehtml])
            filehtmlpage = filehtml
            if cpage > 1:
                filehtmlpage = filehtml.split('.html')[0] + str(cpage) + '.html'
            with open(filehtmlpage, "w") as f:
                f.write(output)
            cpage += 1
    
    #index
    menulist.sort()
    menu = ""
    menu2 = ""
    for menuitem in menulist:
        menu += '<a class="mw-ui-button mw-ui-blue" href="%s">%s</a> ' % (menuitem[1], menuitem[0])
        menu2 += '%s<a href="%s">Fondos de pantalla de %s</a>' % (menu2 and ' · ' or '', menuitem[1], menuitem[0])
    
    random.shuffle(maingallery)
    maingalleryplain = ''.join(maingallery[:gallerylimit])
    index = """<!DOCTYPE html>
<html lang="es" dir="ltr">
<head>
    <title>Los mejores fondos de pantalla</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    
    <meta name="twitter:title" content="Los mejores fondos de pantalla"/>
    <meta name="keywords" content="fondos de pantalla, fondos de escritorio, wallpapers, imagenes, fotos, pantalla, escritorio, descargar fondos, fondos gratis, fondos hd, fondos bonitos"/>
    <meta name="description" content="Una selección de los mejores fondos de pantalla para tu ordenador. Fondos de animales, arquitectura, naturaleza, paisajes, astronomía y mucho más..."/>
    <meta name="twitter:description" content="Una selección de los mejores fondos de pantalla para tu ordenador. Fondos de animales, arquitectura, naturaleza, paisajes, astronomía y mucho más..."/>
    <meta name="twitter:card" content="summary"/>
    <meta name="twitter:domain" content="http://fondos.org.es"/>
    <meta name="twitter:creator" content="Fondos.org.es"/>
    <meta name="twitter:image:src" content="%s"/>
    
    <link rel="stylesheet" href="style.css" />
</head>
<body>
<h1><a href="index.html">Fondos de pantalla</a></h1>

<p>Una selección de las <b>mejores imágenes</b> extraídas de <a href="https://commons.wikimedia.org">Wikimedia Commons</a> para usarlas como fondos de escritorio. Un total de <b>%s fondos</b> de pantalla de excelente calidad con licencias libres. Haz click en las imágenes para consultar la información de autoría, licencia y descripciones.</p>

<center>
%s

<div style="clear: both; float: center; margin-top: 5px;">
%s
</div>

<div style="clear: both; float: center; margin-top: 5px;">
%s
</div>
</center>

<div class="footer">
<hr/>
<a href="http://wikis.cc">Crea tu wiki</a> · 
<a href="http://locapedia.wikis.cc">Crea una locapedia</a> · 
<a href="http://fondos.org.es">Fondos de pantalla</a> · 
<a href="http://librefind.org">LibreFind</a> · 
<a href="http://wikis.org.es">Locapedias</a>
</div>

%s
</body>
</html>""" % (metacardimgsrcmain, len(ctotal), menu, ''.join(maingalleryplain), menu2, ga())
    with open("index.html", "w") as f:
        f.write(index)

if __name__ == '__main__':
    main()
