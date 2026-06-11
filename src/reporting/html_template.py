#!/usr/bin/env python3
"""
共通HTMLテンプレート
"""

from src.reporting.html_utils import get_responsive_table_css


def get_html_template(title, description=""):
    """共通HTMLテンプレートを返す"""
    
    if not description:
        description = "網膜色素変性症（RP）の治療法承認時期を予測。最速2027年（米国）、2032年（日本）。15種類の治療法が開発中。"
    
    template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    
    <!-- OGPタグ -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/images/CDF.png">
    
    <!-- Twitter Card -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="{title}">
    <meta property="twitter:description" content="{description}">
    
    <!-- CSS -->
    <link rel="stylesheet" href="css/common.css">
    
    <!-- モバイルナビゲーション用JavaScript -->
    <script src="js/mobile-nav.js" defer></script>
</head>
<body>
    <!-- スキップリンク -->
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>
    
    <div class="container">
        <!-- ナビゲーション -->
        <nav role="navigation" aria-label="サイト内ナビゲーション">
            <ul>
                <li><a href="index.html">🏠 ホーム</a></li>
                <li><a href="report.html">📊 詳細レポート</a></li>
                <li><a href="reality_and_actions.html">🎯 今できること</a></li>
                <li><a href="regional_approval_timeline.html">🌍 地域別予測</a></li>
                <li><a href="faq.html">❓ FAQ</a></li>
                <li><a href="medical_info.html">👨‍⚕️ 医療従事者向け</a></li>
                <li><a href="patient_guide.html">👥 患者・家族向け</a></li>
            </ul>
        </nav>
        
        <main id="main-content" role="main" class="content-wrapper">
            {{content}}
        </main>
    </div>
    
    <!-- 下部固定ナビゲーション（モバイル用） -->
    <nav class="bottom-nav" role="navigation" aria-label="モバイル用ナビゲーション">
        <ul>
            <li>
                <a href="index.html">
                    <span class="bottom-nav-icon">🏠</span>
                    <span>ホーム</span>
                </a>
            </li>
            <li>
                <a href="report.html">
                    <span class="bottom-nav-icon">📊</span>
                    <span>レポート</span>
                </a>
            </li>
            <li>
                <a href="patient_guide.html">
                    <span class="bottom-nav-icon">👥</span>
                    <span>患者向け</span>
                </a>
            </li>
            <li>
                <a href="faq.html">
                    <span class="bottom-nav-icon">❓</span>
                    <span>FAQ</span>
                </a>
            </li>
        </ul>
    </nav>
    
    <footer role="contentinfo">
        <p>アクセシビリティについて：このサイトは網膜色素変性症の方々にも利用しやすいよう配慮して作成されています。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""
    
    return template


def get_landing_page_template():
    """ランディングページ用のテンプレート"""
    
    template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網膜色素変性症の治療はいつ？ - RPトリートメントロードマップ</title>
    <meta name="description" content="網膜色素変性症（RP）の治療法承認時期を予測。最速2027年（米国）、2032年（日本）。15種類の治療法が開発中。患者・家族・医療従事者向けの包括的情報。">
    
    <!-- OGPタグ -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/">
    <meta property="og:title" content="網膜色素変性症の治療はいつ？">
    <meta property="og:description" content="RP治療を、進行を遅らせる治療と視力再建・根治を目指す治療に分けて整理。">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/images/CDF.png">
    
    <!-- Twitter Card -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="網膜色素変性症の治療はいつ？">
    <meta property="twitter:description" content="最新の臨床試験データに基づく治療承認時期予測。">
    
    <!-- CSS -->
    <link rel="stylesheet" href="css/common.css">
    
    <!-- モバイルナビゲーション用JavaScript -->
    <script src="js/mobile-nav.js" defer></script>
    <style>
        /* ランディングページ専用スタイル */
        .hero {
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: var(--radius);
            margin-bottom: 40px;
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 2rem;
            border-bottom: none;
        }
        
        @media screen and (max-width: 768px) {
            .hero h1 {
                font-size: 2rem;
            }
        }
        
        .key-numbers {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 40px;
        }
        
        .number-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-width: 200px;
            transition: transform 0.3s ease;
        }
        
        .number-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        .paths {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 60px 0;
        }
        
        .path-card {
            text-align: center;
            padding: 40px 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .path-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        
        .path-card.patient {
            border-top: 5px solid var(--primary-color);
        }
        
        .path-card.medical {
            border-top: 5px solid var(--secondary-color);
        }
        
        .path-card.researcher {
            border-top: 5px solid #95a5a6;
        }
        
        .path-card h2 {
            margin-top: 0;
            border: none;
            padding: 0;
        }
        
        @media screen and (max-width: 768px) {
            .paths {
                gap: 20px;
            }
            
            .path-card {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <!-- スキップリンク -->
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>
    
    <div class="container">
        <main id="main-content" role="main">
            {content}
        </main>
    </div>
    
    <!-- 下部固定ナビゲーション（モバイル用） -->
    <nav class="bottom-nav" role="navigation" aria-label="モバイル用ナビゲーション">
        <ul>
            <li>
                <a href="index.html">
                    <span class="bottom-nav-icon">🏠</span>
                    <span>ホーム</span>
                </a>
            </li>
            <li>
                <a href="report.html">
                    <span class="bottom-nav-icon">📊</span>
                    <span>レポート</span>
                </a>
            </li>
            <li>
                <a href="patient_guide.html">
                    <span class="bottom-nav-icon">👥</span>
                    <span>患者向け</span>
                </a>
            </li>
            <li>
                <a href="faq.html">
                    <span class="bottom-nav-icon">❓</span>
                    <span>FAQ</span>
                </a>
            </li>
        </ul>
    </nav>
    
    <footer role="contentinfo">
        <p>アクセシビリティについて：このサイトは網膜色素変性症の方々にも利用しやすいよう配慮して作成されています。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""
    
    return template
