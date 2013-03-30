# -*- coding: utf-8 -*- 

import re

templates_can_use= {}
var_in_templates= {}
all_templates_can_use= []

def isboucle(var):
    return False if re.search('[A-Z]',var) and var not in ("IMGS","POSTER","TOPIC") else True

def expandvar(content,name=""):
    for kaboum in re.findall('\{\{(tpl|subsilver|punbb)/([a-z0-9_]+)\}\}', content):
        content= re.sub('\{\{('+kaboum[0]+"/"+kaboum[1]+')\}\}','[`'+kaboum[1]+'`](https://github.com/Etana/template/blob/master/tpl/var/'+kaboum[1]+'.md#readme)', content)
    for var in re.findall('\{\{[A-Za-z._0-9-]+\}\}', content):
        var= var[2:-2]
        if not isboucle(var):
            content= re.sub('\{\{('+var.replace('.','\.').replace('-','\-')+')\}\}','[`{\\1}`](https://github.com/Etana/template/blob/master/var/\\1.md#readme)', content)
        else:
            attr= var.split(".")[-1]
            content= re.sub('\{\{('+var.replace('.','\.').replace('-','\-')+')\}\}','[`<!-- BEGIN '+attr+' -->...<!-- END '+attr+' -->`](https://github.com/Etana/template/blob/master/var/\\1.md#readme)', content)

    for kaboum in re.findall('\{%([a-z0-9_]*)%\}', content):
        content= re.sub('\{%'+kaboum+'%\}', '', content)
        if name:
            if kaboum=="":
                if name not in all_templates_can_use:
                    all_templates_can_use.append(name)
            else:
                if name not in var_in_templates:
                    var_in_templates[name]= [kaboum]
                else:
                    var_in_templates[name].append(kaboum)

                if kaboum not in templates_can_use:
                    templates_can_use[kaboum]= [name]
                else:
                    templates_can_use[kaboum].append(name)

    content= re.sub('(^\s+|\s+$)','',content)

    return content

