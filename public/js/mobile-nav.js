/**
 * モバイルナビゲーション機能
 */

document.addEventListener('DOMContentLoaded', function() {
    // ハンバーガーメニューの作成
    const nav = document.querySelector('nav');
    if (!nav) return;
    
    // ハンバーガーボタンを作成
    const hamburger = document.createElement('button');
    hamburger.className = 'hamburger';
    hamburger.setAttribute('aria-label', 'メニューを開く');
    hamburger.setAttribute('aria-expanded', 'false');
    hamburger.innerHTML = `
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
    `;
    
    // ナビゲーションラッパーを作成
    const navWrapper = document.createElement('div');
    navWrapper.className = 'nav-wrapper';
    
    // ナビゲーションの内容を移動
    while (nav.firstChild) {
        navWrapper.appendChild(nav.firstChild);
    }
    
    // 要素を配置
    nav.appendChild(hamburger);
    nav.appendChild(navWrapper);
    
    // クリックイベント
    hamburger.addEventListener('click', function() {
        const isOpen = navWrapper.classList.contains('nav-open');
        
        if (isOpen) {
            navWrapper.classList.remove('nav-open');
            hamburger.setAttribute('aria-expanded', 'false');
            hamburger.setAttribute('aria-label', 'メニューを開く');
            document.body.style.overflow = '';
        } else {
            navWrapper.classList.add('nav-open');
            hamburger.setAttribute('aria-expanded', 'true');
            hamburger.setAttribute('aria-label', 'メニューを閉じる');
            document.body.style.overflow = 'hidden';
        }
    });
    
    // メニュー外クリックで閉じる
    document.addEventListener('click', function(e) {
        if (!nav.contains(e.target) && navWrapper.classList.contains('nav-open')) {
            navWrapper.classList.remove('nav-open');
            hamburger.setAttribute('aria-expanded', 'false');
            hamburger.setAttribute('aria-label', 'メニューを開く');
            document.body.style.overflow = '';
        }
    });
    
    // ESCキーで閉じる
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navWrapper.classList.contains('nav-open')) {
            navWrapper.classList.remove('nav-open');
            hamburger.setAttribute('aria-expanded', 'false');
            hamburger.setAttribute('aria-label', 'メニューを開く');
            document.body.style.overflow = '';
            hamburger.focus();
        }
    });
});