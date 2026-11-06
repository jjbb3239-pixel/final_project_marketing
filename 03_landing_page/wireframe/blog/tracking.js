(function () {
  'use strict';

  var name = location.pathname.replace(/^\/wireframe\/blog\/?/, '').replace(/\/+$/, '') || 'index.html';
  var articleId = name.replace(/\.html?$/i, '') || 'index';
  var pageType = articleId === 'index' ? 'blog_index' : 'blog_article';
  var layoutVersion = 'blog-20261106-v1';
  var links = document.querySelectorAll('.cta-row a, footer a[href]');
  var tracked = [];

  function destination(a) {
    try {
      var url = new URL(a.getAttribute('href'), location.href);
      if (url.hostname === 'fireclub.liveklass.com' && /^\/classes\/274558\/classroom\/1191830\/?$/.test(url.pathname)) return 'free_lesson';
      if (url.hostname === 'fireclub.liveklass.com' && /^\/classes\/274558\/?$/.test(url.pathname)) return 'product_detail';
      if (url.origin === location.origin && /^\/wireframe\/(?:index\.html)?$/.test(url.pathname)) return 'landing';
    } catch (e) { return null; }
    return null;
  }

  links.forEach(function (a) {
    var type = destination(a);
    if (!type) return;
    var position = a.closest('footer') ? 'footer' : 'content';
    var details = { cta_id: 'blog_' + articleId + '_' + position + '_' + type, cta_location: position,
      destination_type: type, page_type: pageType, article_id: articleId, layout_version: layoutVersion };
    tracked.push({ el: a, details: details, seen: false, visible: false, timer: null });
    a.addEventListener('click', function () {
      window.dataLayer.push(Object.assign({ event: 'blog_cta_click' }, details));
    });
  });

  if ('IntersectionObserver' in window) {
    var cancel = function (state) { if (state.timer) { clearTimeout(state.timer); state.timer = null; } };
    var start = function (state) {
      if (state.seen || !state.visible || document.hidden || state.timer) return;
      state.timer = setTimeout(function () {
        state.timer = null;
        if (state.seen || !state.visible || document.hidden) return;
        state.seen = true;
        window.dataLayer.push(Object.assign({ event: 'cta_view' }, state.details));
        observer.unobserve(state.el);
      }, 1000);
    };
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var state = tracked.find(function (item) { return item.el === entry.target; });
        if (!state) return;
        state.visible = entry.isIntersecting && entry.intersectionRatio >= 0.5;
        if (state.visible) start(state); else cancel(state);
      });
    }, { threshold: [0, 0.5] });
    tracked.forEach(function (state) { observer.observe(state.el); });
    document.addEventListener('visibilitychange', function () {
      tracked.forEach(function (state) { if (document.hidden) cancel(state); else start(state); });
    });
  }
})();
