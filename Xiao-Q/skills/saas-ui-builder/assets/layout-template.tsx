'use client';

import { useState } from 'react';
import styles from './layout-template.module.css';

// ============================================
// PNG Logo 组件 - 使用 public 目录的图片
// 重要：将 assets/ 目录下的 header-logo.png, logo-brand.png, user-avatar.png
//      复制到目标项目的 public/ 目录
// ============================================
const HeaderLogoImg = () => (
  <img src="/header-logo.png" alt="碳擎 Logo" className={styles.headerLogo} />
);

const BrandLogoImg = () => (
  <img src="/logo-brand.png" alt="Brand Logo" className={styles.logoIcon} />
);

const UserAvatarImg = () => (
  <img src="/user-avatar.png" alt="User Avatar" className={styles.userAvatar} />
);

// 导航菜单项配置
const NAV_ITEMS = [
  { id: 'order-manage', label: '订单管理', icon: 'folder', hasArrow: true, hasSub: true,
    children: [
      { id: 'data-list', label: '数据列表' },
      { id: 'analysis', label: '分析评价' },
    ]
  },
];

// 图标 SVG 映射
const ICONS: Record<string, JSX.Element> = {
  home: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
    </svg>
  ),
  edit: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L11 14.586V8z" clipRule="evenodd" />
    </svg>
  ),
  folder: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a2 2 0 00-2-2H5z" clipRule="evenodd" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
    </svg>
  ),
  document: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
    </svg>
  ),
  grid: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>
  ),
  upload: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  ),
  chevronRight: (
    <svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10">
      <path d="M6.22 4.22a.75.75 0 011.06 0l3.25 3.25a.75.75 0 010 1.06l-3.25 3.25a.75.75 0 01-1.06-1.06L8.94 8 6.22 5.28a.75.75 0 010-1.06z" />
    </svg>
  ),
  chevronLeft: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  ),
  help: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/>
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
      <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
    </svg>
  ),
};

export default function Page() {
  const [expandedMenus, setExpandedMenus] = useState<Record<string, boolean>>({});
  const [activeSubItem, setActiveSubItem] = useState<string | null>(null);

  const toggleMenu = (id: string) => {
    setExpandedMenus((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className={styles.layout}>
      {/* === Header 顶栏 (70px) === */}
      <header className={styles.header}>
        <HeaderLogoImg />
        <div className={styles.headerRight}>
          <button type="button" className={styles.workbenchBtn}>
            工作台
          </button>

          <button type="button" className={`${styles.headerSelectGroup} ${styles.selectWide}`}>
            <span>产品库</span>
          </button>

          <button type="button" className={`${styles.headerSelectGroup} ${styles.selectNarrow}`}>
            <span>工具</span>
          </button>

          <button type="button" className={`${styles.headerSelectGroup} ${styles.selectMedium}`}>
            <span>企业信息</span>
          </button>

          <button type="button" className={styles.iconBtn} aria-label="帮助">
            {ICONS.help}
          </button>

          <button type="button" className={styles.iconBtn} aria-label="消息通知">
            {ICONS.bell}
          </button>

          <div className={styles.userInfo}>
            <UserAvatarImg />
            <span className={styles.companyName}>江苏擎天工业互联网有限公司</span>
          </div>
        </div>
      </header>

      {/* === 内容区 === */}
      <div className={styles.body}>
        {/* === Sidebar 侧栏 (220px) === */}
        <aside className={styles.sidebar}>
          {/* 顶部 Logo + 产品标题 */}
          <div className={styles.sidebarHeader}>
            <div className={styles.sidebarHeaderInner}>
              <BrandLogoImg />
              <h1 className={styles.productTitle}>产品碳足迹3.0</h1>
            </div>
          </div>

          {/* 导航菜单列表 */}
          <nav className={styles.navList}>
            {NAV_ITEMS.map((item) => (
              <div key={item.id}>
                <div
                  className={styles.navItem}
                  onClick={() => item.hasArrow && toggleMenu(item.id)}
                >
                  <div className={styles.navItemIcon}>
                    {ICONS[item.icon]}
                  </div>
                  <span className={styles.navItemLabel}>{item.label}</span>
                  {item.hasArrow && (
                    <div className={`${styles.navItemArrow} ${expandedMenus[item.id] ? styles.expanded : ''}`}>
                      {ICONS.chevronRight}
                    </div>
                  )}
                </div>
                {/* 子菜单：同时只能有一个子菜单被选中 */}
                {item.hasArrow && (
                  <div className={`${styles.subMenu} ${expandedMenus[item.id] ? styles.open : ''}`}>
                    {item.children?.map((sub) => (
                      <div
                        key={sub.id}
                        className={`${styles.subMenuItem} ${activeSubItem === sub.id ? styles.subActive : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveSubItem(sub.id);
                        }}
                      >
                        <span className={styles.subMenuItemLabel}>{sub.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* 底部收起导航 */}
          <div className={styles.sidebarFooter}>
            <div className={styles.collapseBtn}>
              {ICONS.chevronLeft}
              <span>收起导航</span>
            </div>
          </div>
        </aside>

        {/* === 主内容区 === */}
        <div className={styles.mainColumn}>
          <nav className={styles.breadcrumb} aria-label="面包屑">
            <span>首页</span>
            <span className={styles.breadcrumbSep}>/</span>
            <span>订单管理</span>
            <span className={styles.breadcrumbSep}>/</span>
            <span className={styles.breadcrumbCurrent}>数据列表</span>
          </nav>

          {/* 主内容画布 */}
          <main className={styles.mainContent}>
            <div className={styles.pageHeader}>
              <h2 className={styles.pageTitle}>数据列表</h2>
              <div className={styles.pageActions}>
                <button type="button" className={styles.btnPrimary}>
                  新建订单
                </button>
                <button type="button" className={styles.btnSecondary}>
                  导出数据
                </button>
              </div>
            </div>

            {/* 内容区 / 空状态 */}
            <div className={styles.contentCanvas}>
              <div className={styles.emptyState}>
                <div className={styles.emptyCard}>
                  <svg className={styles.emptyIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <p className={styles.emptyTitle}>暂无数据</p>
                  <p className={styles.emptyDesc}>点击「新建订单」按钮开始创建</p>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
