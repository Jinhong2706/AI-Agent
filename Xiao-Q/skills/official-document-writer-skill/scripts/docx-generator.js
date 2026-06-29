/**
 * GB/T 9704-2020 公文Word文档生成模板
 *
 * 使用说明：
 * 1. 将此文件复制到工作目录
 * 2. 修改content数组中的内容
 * 3. 运行: node docx-generator.js
 * 4. 输出文件: 公文_YYYYMMDD.docx
 *
 * ⚠️ 字体加粗规范（极易出错）：
 * - 只有公文标题（二号方正小标宋）加粗
 * - 一级标题、二级标题、正文全部不加粗
 */

const { Document, Packer, Paragraph, TextRun, AlignmentType, PageNumber, Footer, Header } = require('docx');
const fs = require('fs');

// ============================================================
// 格式参数（GB/T 9704-2020）
// ============================================================
const PAGE = {
    width: 11906,      // A4宽度 210mm
    height: 16838,      // A4高度 297mm
    margin: {
        top: 1326,      // 37mm
        bottom: 1250,    // 35mm
        left: 1000,     // 28mm
        right: 929       // 26mm
    }
};

const FONT_SIZE = {
    erHao: 44,    // 二号 = 22pt
    sanHao: 32,   // 三号 = 16pt
    siHao: 28     // 四号 = 14pt
};

const LINE_SPACING = { value: 560, rule: "exact" };  // 固定值28磅
const INDENT_TWO_CHARS = 1134;  // 首行缩进2字符

// ============================================================
// 段落创建函数
// ============================================================

/**
 * 创建正文段落（仿宋 三号 不加粗 固定行距 首行缩进2字）
 */
function createBodyParagraph(text) {
    return new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 0, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        indent: { firstLine: INDENT_TWO_CHARS },
        children: [new TextRun({ text, font: '仿宋_GB2312', size: FONT_SIZE.sanHao, bold: false })]
    });
}

/**
 * 创建一级标题（一、二、三…… 黑体 三号 不加粗 顶格）
 */
function createLevel1Heading(text) {
    return new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 240, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        indent: { firstLine: 0 },
        children: [new TextRun({ text, font: '黑体', size: FONT_SIZE.sanHao, bold: false })]
    });
}

/**
 * 创建二级标题（（一）（二）…… 楷体 三号 不加粗 首行缩进2字）
 */
function createLevel2Heading(text) {
    return new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 0, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        indent: { firstLine: INDENT_TWO_CHARS },
        children: [new TextRun({ text, font: '楷体_GB2312', size: FONT_SIZE.sanHao, bold: false })]
    });
}

/**
 * 创建公文标题（方正小标宋 二号 加粗 居中）
 */
function createDocTitle(title) {
    return new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        children: [new TextRun({ text: title, font: '方正小标宋简体', size: FONT_SIZE.erHao, bold: true })]
    });
}

/**
 * 创建主送机关（仿宋 三号 不加粗 顶格）
 */
function createMainRecipient(text) {
    return new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 240, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        indent: { firstLine: 0 },
        children: [new TextRun({ text, font: '仿宋_GB2312', size: FONT_SIZE.sanHao, bold: false })]
    });
}

/**
 * 创建右对齐落款（仿宋 三号 不加粗 右对齐）
 */
function createRightAlignedText(text, spacingBefore = 0) {
    return new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { before: spacingBefore, after: 0, line: LINE_SPACING.value, lineRule: LINE_SPACING.rule },
        children: [new TextRun({ text, font: '仿宋_GB2312', size: FONT_SIZE.sanHao, bold: false })]
    });
}

// ============================================================
// 公文内容（修改此处）
// ============================================================
const content = [
    // 公文标题（方正小标宋 二号 加粗 居中）
    createDocTitle('【发文机关】关于【事由】的【文种】'),

    // 主送机关（仿宋 三号 顶格）
    createMainRecipient('【主送机关名称】：'),

    // 开头段（根据文种选择不同开头语）
    // 请示："为深入贯彻落实...，现就...事项请示如下："
    // 报告："根据...部署要求，现就...情况报告如下："
    createBodyParagraph('【开头段：根据...精神，现就...情况报告如下：】'),

    // 一、（一）1. 层次结构
    createLevel1Heading('一、基本情况'),
    createLevel2Heading('（一）工作背景。'),
    createBodyParagraph('【简要说明工作背景】'),

    createLevel1Heading('二、主要做法'),
    createLevel2Heading('（一）强化组织领导。'),
    createBodyParagraph('【具体做法1】'),
    createLevel2Heading('（二）突出重点环节。'),
    createBodyParagraph('【具体做法2】'),

    createLevel1Heading('三、工作成效'),
    createBodyParagraph('【成效1：围绕...，完成...，实现...】'),
    createBodyParagraph('【成效2：针对...，采取...措施，取得...成效】'),

    createLevel1Heading('四、存在问题'),
    createBodyParagraph('【存在问题分析】'),

    createLevel1Heading('五、下一步打算'),
    createBodyParagraph('【下一步工作计划】'),

    // 结束语
    createBodyParagraph('【请示语：妥否，请批示。】'),
    createBodyParagraph('【报告语：特此报告。】'),

    // 落款（署名前空两行）
    createRightAlignedText('【发文机关全称】', 480),
    createRightAlignedText('2026年4月22日')
];

// ============================================================
// 生成文档
// ============================================================
const doc = new Document({
    sections: [{
        properties: {
            page: {
                size: { width: PAGE.width, height: PAGE.height },
                margin: PAGE.margin
            }
        },
        headers: { default: new Header({ children: [] }) },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [
                        new TextRun({ text: '— ', font: '仿宋_GB2312', size: FONT_SIZE.siHao, bold: false }),
                        new TextRun({ children: [PageNumber.CURRENT], font: '仿宋_GB2312', size: FONT_SIZE.siHao, bold: false }),
                        new TextRun({ text: ' —', font: '仿宋_GB2312', size: FONT_SIZE.siHao, bold: false })
                    ]
                })]
            })
        },
        children: content
    }]
});

// 输出
const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(`公文_${today}.docx`, buffer);
    console.log(`✅ 公文已生成：公文_${today}.docx`);
});
