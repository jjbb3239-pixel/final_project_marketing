(function () {
  'use strict';

  var name = location.pathname.replace(/^\/wireframe\/blog\/?/, '').replace(/\/+$/, '') || 'index.html';
  var articleId = name.replace(/\.html?$/i, '') || 'index';
  var pageType = articleId === 'index' ? 'blog_index' : 'blog_article';
  var layoutVersion = 'blog-20261106-v2';
  var tracked = [];
  var handled = [];

  function position(a) {
    if (a.closest('footer')) return 'footer';
    if (a.closest('.site-head, header')) return 'header';
    return 'content';
  }

  function destination(a) {
    try {
      var url = new URL(a.getAttribute('href'), location.href);
      if (url.hostname === 'fireclub.liveklass.com' && /^\/classes\/274558\/classroom\/1191830\/?$/.test(url.pathname)) return 'free_lesson';
      if (url.hostname === 'fireclub.liveklass.com' && /^\/classes\/274558\/?$/.test(url.pathname)) return 'product_detail';
      if (url.origin === location.origin && /^\/(?:index\.html|wireframe\/(?:index\.html)?)?$/.test(url.pathname)) return 'landing';
    } catch (e) { return null; }
    return null;
  }

  // 0) 강의 사이트로 가는 링크에 기본 UTM을 붙여 블로그 유입임을 구분한다 (이미 UTM이 있으면 그대로 둔다).
  document.querySelectorAll('a[href]').forEach(function (a) {
    try {
      var url = new URL(a.getAttribute('href'), location.href);
      if (url.hostname !== 'fireclub.liveklass.com' || url.searchParams.get('utm_source')) return;
      url.searchParams.set('utm_source', 'petitrich_blog');
      url.searchParams.set('utm_medium', 'referral');
      url.searchParams.set('utm_campaign', 'finalproject');
      url.searchParams.set('utm_content', 'blog_' + articleId);
      a.setAttribute('href', url.toString());
    } catch (e) { /* 잘못된 주소는 건드리지 않는다. */ }
  });

  // 1) 강의·랜딩 이동 CTA: blog_cta_click (+ 노출 1초 이상이면 cta_view). 헤더 링크는 클릭만 기록한다.
  function addCta(a, withView) {
    var type = destination(a);
    if (!type || handled.indexOf(a) >= 0) return;
    var position_ = position(a);
    var details = { cta_id: 'blog_' + articleId + '_' + position_ + '_' + type, cta_location: position_,
      destination_type: type, page_type: pageType, article_id: articleId, layout_version: layoutVersion };
    handled.push(a);
    if (withView) tracked.push({ el: a, details: details, seen: false, visible: false, timer: null });
    a.addEventListener('click', function () {
      window.dataLayer.push(Object.assign({ event: 'blog_cta_click' }, details));
    });
  }
  document.querySelectorAll('.cta-row a, footer a[href]').forEach(function (a) { addCta(a, true); });
  document.querySelectorAll('.site-head a[href], header a[href]').forEach(function (a) { addCta(a, false); });

  // 2) 그 밖의 링크(관련 글, 블로그 목록, 외부 링크 등): blog_link_click. 광고 전환 이벤트(cta_click)와 분리되어 있다.
  function linkInfo(a) {
    var href = a.getAttribute('href') || '';
    if (!href || href.charAt(0) === '#' || /^(javascript|mailto|tel):/i.test(href)) return null;
    try { var self = new URL(a.href); if (self.hash && self.origin === location.origin && self.pathname === location.pathname) return null; } catch (e) { return null; } // 같은 글 안의 목차 이동은 기록하지 않는다
    var dest = destination(a);
    if (dest) return { type: 'link_' + dest, target: '' };
    try {
      var url = new URL(a.href);
      if (url.origin === location.origin) {
        var m = url.pathname.match(/^\/wireframe\/blog\/?([^\/]*?)(?:\.html?)?$/);
        if (m) return m[1] && m[1] !== 'index' ? { type: 'blog_article', target: m[1] } : { type: 'blog_index', target: '' };
        return { type: 'internal_other', target: '' };
      }
      if (/(^|\.)blog\.naver\.com$/.test(url.hostname)) return { type: 'external_naver_blog', target: '' };
      return { type: 'external_reference', target: '' };
    } catch (e) { return null; }
  }
  document.querySelectorAll('a[href]').forEach(function (a) {
    if (handled.indexOf(a) >= 0) return;
    var info = linkInfo(a);
    if (!info) return;
    var position_ = position(a);
    var details = { cta_id: 'blog_' + articleId + '_' + position_ + '_' + info.type + (info.target ? '_' + info.target : ''),
      cta_location: position_, destination_type: info.type, page_type: pageType, article_id: articleId, layout_version: layoutVersion };
    handled.push(a);
    a.addEventListener('click', function () {
      window.dataLayer.push(Object.assign({ event: 'blog_link_click' }, details));
    });
  });

  // 3) 글 스크롤 깊이: 스크롤 가능한 거리의 25/50/75/90%를 처음 지날 때 1회씩
  var marks = [25, 50, 75, 90], fired = {}, ticking = false;
  function checkScroll() {
    ticking = false;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (max <= 0) return;
    var pct = (window.pageYOffset / max) * 100;
    marks.forEach(function (mark) {
      if (fired[mark] || pct < mark) return;
      fired[mark] = true;
      window.dataLayer.push({ event: 'blog_scroll_depth', scroll_depth_percent: mark,
        page_type: pageType, article_id: articleId, layout_version: layoutVersion });
    });
  }
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(checkScroll);
  }, { passive: true });

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
