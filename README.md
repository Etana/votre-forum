# votre-forum

Proxy with admin permission to be able to link or show a path in a forumotion forum administration pannel.

The code is running on [votre-forum.appspot.com](https://votre-forum.appspot.com) and the administration pannel is accessible.

### Path generator

When a path is prefixed by `/path/` a page is displayed with a link in `bbcode` and `markdown` from the forum homepage to the prefixed path.

For example I can go on the forum configuration page:
  [https://votre-forum.appspot.com/admin/?mode=general&part=general&sub=general](https://votre-forum.appspot.com/admin/?mode=general&part=general&sub=general)

I prefix the path by `/path/`:
  [https://votre-forum.appspot.com/path/admin/?mode=general&part=general&sub=general](https://votre-forum.appspot.com/path/admin/?mode=general&part=general&sub=general) and this gives:

  - a full path: [`Index`](http://votre-forum.appspot.com/#/admin/,&part=general,&mode=general&sub=general) > [`Panneau d'administration`](http://votre-forum.appspot.com/admin/#&part=general,&mode=general&sub=general) > [`Général`](http://votre-forum.appspot.com/admin/?part=general#&mode=general&sub=general) > [`Forum | Configuration`](http://votre-forum.appspot.com/admin/?mode=general&part=general&sub=general)
  - a path from the start: [`Index > Panneau d'administration > Général > Forum | Configuration`](http://votre-forum.appspot.com/#/admin/,&part=general,&mode=general&sub=general)
  - a path from the end: [`Index > Panneau d'administration > Général > Forum | Configuration`](http://votre-forum.appspot.com/admin/?mode=general&part=general&sub=general)
