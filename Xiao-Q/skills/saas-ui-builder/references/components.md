# 组件规范 (Components)

## 按钮 (Button)

### 主按钮
```css
.btnPrimary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  background: #2249F8;
  color: #FFFFFF;
  border: none;
  cursor: pointer;
  transition: background 150ms ease;
}

.btnPrimary:hover {
  background: #647FFA;
}
```

### 次要按钮
```css
.btnSecondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  background: #F5F7FF;
  color: #2249F8;
  border: 1px solid #2249F8;
  cursor: pointer;
  transition: background 150ms ease;
}

.btnSecondary:hover {
  background: #E8EDFF;
}
```

### 图标按钮
```css
.iconBtn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #666666;
  cursor: pointer;
  transition: all 150ms ease;
}

.iconBtn:hover {
  background: #f5f5f5;
  color: #333333;
}
```

### 页面操作按钮组
```css
.pageActions {
  display: flex;
  align-items: center;
  gap: 16px;
}
```

## 输入框 (Input)

### 基础输入框
```css
.input {
  height: 32px;
  padding: 0 12px;
  border: 1px solid #EEEEEE;
  border-radius: 2px;
  font-size: 14px;
  color: #333333;
  background: #FFFFFF;
  outline: none;
  transition: border-color 150ms ease;
}

.input:focus {
  border-color: #2249F8;
}

.input::placeholder {
  color: #999999;
}
```

### 筛选输入框
```css
.filterInput {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 14px;
  color: #333333;
  background: transparent;
  border: none;
  outline: none;
}
```

## 下拉选择 (Select)

### 筛选下拉选择器
```css
.filterSelect {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  gap: 8px;
  font-size: 14px;
  color: #999999;
  cursor: pointer;
}

.filterChevron {
  width: 16px;
  height: 16px;
  color: #999999;
}
```

### 顶栏下拉选择器
```css
.headerSelectGroup {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  background: transparent;
  border: none;
  cursor: pointer;
}

.headerSelectGroup:hover {
  background: #f5f5f5;
}

/* 不同宽度变体 */
.headerSelectGroup.selectWide {
  width: 96px;
}

.headerSelectGroup.selectNarrow {
  width: 82px;
}

.headerSelectGroup.selectMedium {
  width: 104px;
}
```

## 表格 (Table)

### 表格容器
```css
.tableContainer {
  width: 100%;
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 12px 16px;
  text-align: left;
  font-size: 14px;
}

.table th {
  background: #F7F8F9;
  color: #333333;
  font-weight: 500;
  border-bottom: 1px solid #EEEEEE;
}

.table td {
  color: #666666;
  border-bottom: 1px solid #EEEEEE;
}
```

## 卡片 (Card)

### 基础卡片
```css
.card {
  background: #FFFFFF;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cardHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.cardTitle {
  font-size: 16px;
  font-weight: 700;
  color: #333333;
}
```

## 模态框 (Modal)

### 模态框遮罩
```css
.modalOverlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #FFFFFF;
  border-radius: 8px;
  padding: 24px;
  min-width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
}

.modalHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.modalTitle {
  font-size: 18px;
  font-weight: 700;
  color: #333333;
}
```

## 表单 (Form)

### 表单字段
```css
.formField {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.formLabel {
  font-size: 14px;
  color: #666666;
}

.formInput {
  height: 32px;
  padding: 0 12px;
  border: 1px solid #EEEEEE;
  border-radius: 2px;
  font-size: 14px;
  outline: none;
}

.formInput:focus {
  border-color: #2249F8;
}
```

### 表单行
```css
.formRow {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
```

## 标签 (Tag)

### 状态标签
```css
.tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 500;
}

.tagSuccess {
  background: #EDFBF6;
  color: #35C476;
}

.tagWarning {
  background: #FFF5F0;
  color: #F79E36;
}

.tagError {
  background: rgba(228, 17, 33, 0.1);
  color: #E41121;
}

.tagInfo {
  background: #F5F7FF;
  color: #2249F8;
}
```

## 空状态 (Empty State)

### 空状态卡片
```css
.emptyState {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.emptyCard {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.emptyIcon {
  width: 48px;
  height: 48px;
  color: #CCCCCC;
}

.emptyTitle {
  font-size: 14px;
  color: #9e9e9e;
  margin: 0;
}

.emptyDesc {
  font-size: 12px;
  color: #9e9e9e;
  margin: 0;
}
```

## 面包屑 (Breadcrumb)

```css
.breadcrumb {
  height: 22px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 22px;
  color: #666666;
}

.breadcrumbSep {
  color: #999999;
}

.breadcrumbCurrent {
  color: #333333;
  font-weight: 500;
}
```

## 内容区域 (Content Area)

```css
.contentCanvas {
  flex: 1;
  overflow-y: auto;
}

.textContent h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333333;
  margin: 24px 0 12px;
  line-height: 26px;
}

.textContent h3:first-child {
  margin-top: 0;
}

.textContent p {
  font-size: 14px;
  line-height: 24px;
  color: #666666;
  margin: 0 0 12px;
}

.textContent strong {
  color: #333333;
  font-weight: 600;
}
```
