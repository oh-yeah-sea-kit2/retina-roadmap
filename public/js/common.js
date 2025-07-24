/**
 * 網膜色素変性症治療予測プロジェクト - 共通JavaScript
 * バージョン: 1.0.0
 * 作成日: 2025-01-24
 */

// DOM読み込み完了後に実行
document.addEventListener('DOMContentLoaded', function() {
  // 初期化
  initSmoothScroll();
  initTabs();
  initAccordion();
  initMobileMenu();
  initAccessibility();
});

/**
 * スムーススクロール機能
 */
function initSmoothScroll() {
  // ページ内リンクを取得
  const links = document.querySelectorAll('a[href^="#"]');
  
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      
      e.preventDefault();
      const target = document.querySelector(href);
      
      if (target) {
        const offsetTop = target.offsetTop - 100; // ヘッダー分のオフセット
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
        
        // フォーカスを移動（アクセシビリティ）
        target.setAttribute('tabindex', '-1');
        target.focus();
      }
    });
  });
}

/**
 * タブ切り替え機能
 */
function initTabs() {
  const tabContainers = document.querySelectorAll('.tab-container');
  
  tabContainers.forEach(container => {
    const tabs = container.querySelectorAll('.tab-btn');
    const contents = container.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', function() {
        // 全てのタブとコンテンツを非アクティブに
        tabs.forEach(t => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        contents.forEach(c => {
          c.classList.remove('active');
          c.setAttribute('hidden', 'true');
        });
        
        // クリックされたタブとコンテンツをアクティブに
        this.classList.add('active');
        this.setAttribute('aria-selected', 'true');
        
        const targetId = this.getAttribute('data-tab');
        const targetContent = container.querySelector(`#${targetId}`);
        if (targetContent) {
          targetContent.classList.add('active');
          targetContent.removeAttribute('hidden');
        }
        
        // URLハッシュを更新
        history.replaceState(null, null, `#${targetId}`);
      });
    });
    
    // URLハッシュに基づいて初期タブを設定
    const hash = window.location.hash.slice(1);
    if (hash) {
      const targetTab = container.querySelector(`[data-tab="${hash}"]`);
      if (targetTab) {
        targetTab.click();
      }
    }
  });
}

/**
 * アコーディオン機能
 */
function initAccordion() {
  const accordions = document.querySelectorAll('.accordion');
  
  accordions.forEach(accordion => {
    const headers = accordion.querySelectorAll('.accordion-header');
    
    headers.forEach(header => {
      header.addEventListener('click', function() {
        const content = this.nextElementSibling;
        const isOpen = this.classList.contains('active');
        
        // 同じアコーディオン内の他の項目を閉じる（オプション）
        const singleOpen = accordion.hasAttribute('data-single-open');
        if (singleOpen && !isOpen) {
          accordion.querySelectorAll('.accordion-header').forEach(h => {
            h.classList.remove('active');
            h.setAttribute('aria-expanded', 'false');
            const c = h.nextElementSibling;
            if (c) {
              c.style.maxHeight = null;
              c.setAttribute('hidden', 'true');
            }
          });
        }
        
        // クリックされた項目をトグル
        this.classList.toggle('active');
        
        if (content) {
          if (isOpen) {
            content.style.maxHeight = null;
            content.setAttribute('hidden', 'true');
            this.setAttribute('aria-expanded', 'false');
          } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.removeAttribute('hidden');
            this.setAttribute('aria-expanded', 'true');
          }
        }
      });
    });
  });
}

/**
 * モバイルメニュー機能
 */
function initMobileMenu() {
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  const nav = document.querySelector('nav');
  
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', function() {
      nav.classList.toggle('mobile-open');
      const isOpen = nav.classList.contains('mobile-open');
      
      this.setAttribute('aria-expanded', isOpen);
      this.textContent = isOpen ? '閉じる' : 'メニュー';
    });
    
    // メニュー外クリックで閉じる
    document.addEventListener('click', function(e) {
      if (!nav.contains(e.target) && !menuToggle.contains(e.target)) {
        nav.classList.remove('mobile-open');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.textContent = 'メニュー';
      }
    });
  }
}

/**
 * アクセシビリティ機能
 */
function initAccessibility() {
  // Escキーでフォーカスをリセット
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.activeElement.blur();
    }
  });
  
  // tabindexが設定された要素のフォーカス後にtabindexを削除
  document.addEventListener('focus', function(e) {
    if (e.target.getAttribute('tabindex') === '-1') {
      e.target.removeAttribute('tabindex');
    }
  }, true);
  
  // 画像の遅延読み込み
  if ('IntersectionObserver' in window) {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver(function(entries, observer) {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });
    
    images.forEach(img => imageObserver.observe(img));
  }
}

/**
 * ユーティリティ関数
 */

// デバウンス関数
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// スロットル関数
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// URLパラメータ取得
function getUrlParameter(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

// クッキー管理
const Cookie = {
  set: function(name, value, days) {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
  },
  
  get: function(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  },
  
  delete: function(name) {
    document.cookie = name + '=; Max-Age=-99999999;';
  }
};

// エクスポート（必要に応じて）
window.RPUtils = {
  debounce,
  throttle,
  getUrlParameter,
  Cookie
};