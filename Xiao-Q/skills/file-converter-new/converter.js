#!/usr/bin/env node
/**
 * 文件格式转换工具
 * 支持：图片转换、视频转GIF、PDF处理
 */

const fs = require('fs');
const path = require('path');

// 颜色输出
const colors = {
    green: (s) => `\x1b[32m${s}\x1b[0m`,
    red: (s) => `\x1b[31m${s}\x1b[0m`,
    yellow: (s) => `\x1b[33m${s}\x1b[0m`,
    blue: (s) => `\x1b[34m${s}\x1b[0m`
};

// 帮助信息
function showHelp() {
    console.log(`
${colors.blue('=== 文件格式转换工具 ===')}

用法: node converter.js <命令> [选项]

${colors.yellow('图片转换:')}
  convert <输入> <输出>          转换图片格式
    -w, --width <像素>           调整宽度
    -h, --height <像素>          调整高度
    -q, --quality <1-100>        质量(JPG/WebP)

  compress <输入> [输出]         压缩图片
    -q, --quality <1-100>        压缩质量(默认80)

  batch <目录>                   批量转换目录下图片
    -f, --format <格式>          目标格式(jpg/png/webp)
    -q, --quality <1-100>        质量

${colors.yellow('视频转GIF:')}
  video2gif <视频> <输出.gif>    视频转GIF
    -s, --start <秒>             开始时间(默认0)
    -t, --duration <秒>          时长(默认10)
    -w, --width <像素>           宽度(默认480)
    -fps <帧率>                  帧率(默认10)

${colors.yellow('PDF操作:')}
  merge <pdf1> <pdf2> <输出>     合并PDF
  pdf2img <pdf> [输出目录]       PDF转图片
  split <pdf> [输出目录]         拆分PDF(每页一个文件)

${colors.yellow('信息:')}
  info <文件>                    查看文件信息
  formats                        列出支持的格式
  help                           显示帮助
`);
}

// 初始化 Sharp
async function getSharp() {
    try {
        return require('sharp');
    } catch (e) {
        console.log(colors.yellow('正在安装 sharp...'));
        const { execSync } = require('child_process');
        execSync('npm install sharp', { stdio: 'inherit', cwd: __dirname });
        return require('sharp');
    }
}

// 初始化 ffmpeg
async function getFfmpeg() {
    try {
        return require('fluent-ffmpeg');
    } catch (e) {
        console.log(colors.yellow('正在安装 fluent-ffmpeg...'));
        const { execSync } = require('child_process');
        execSync('npm install fluent-ffmpeg', { stdio: 'inherit', cwd: __dirname });
        return require('fluent-ffmpeg');
    }
    }

// 初始化 pdf-lib
async function getPdfLib() {
    try {
        return require('pdf-lib');
    } catch (e) {
        console.log(colors.yellow('正在安装 pdf-lib...'));
        const { execSync } = require('child_process');
        execSync('npm install pdf-lib', { stdio: 'inherit', cwd: __dirname });
        return require('pdf-lib');
    }
}

// 解析参数
function parseArgs(args) {
    const options = {};
    const positional = [];
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg.startsWith('-')) {
            const key = arg.replace(/^-+/, '');
            const value = args[i + 1] && !args[i + 1].startsWith('-') ? args[++i] : true;
            options[key] = value;
        } else {
            positional.push(arg);
        }
    }
    
    return { positional, options };
}

// 转换图片
async function convertImage(input, output, options = {}) {
    const sharp = await getSharp();
    
    if (!fs.existsSync(input)) {
        console.error(colors.red(`错误: 文件不存在 ${input}`));
        return false;
    }
    
    let pipeline = sharp(input);
    
    // 调整尺寸
    if (options.width || options.height || options.w || options.h) {
        const width = parseInt(options.width || options.w);
        const height = parseInt(options.height || options.h);
        pipeline = pipeline.resize(width || null, height || null, { 
            fit: 'inside',
            withoutEnlargement: true 
        });
    }
    
    // 获取输出格式
    const ext = path.extname(output).toLowerCase();
    const quality = parseInt(options.quality || options.q) || 80;
    
    // 根据格式设置
    if (ext === '.jpg' || ext === '.jpeg') {
        pipeline = pipeline.jpeg({ quality, progressive: true });
    } else if (ext === '.png') {
        pipeline = pipeline.png({ progressive: true });
    } else if (ext === '.webp') {
        pipeline = pipeline.webp({ quality });
    } else if (ext === '.gif') {
        // GIF需要特殊处理，这里只是保存静态图
        pipeline = pipeline.gif();
    }
    
    await pipeline.toFile(output);
    console.log(colors.green(`✓ 转换完成: ${output}`));
    
    // 显示文件大小对比
    const inputStat = fs.statSync(input);
    const outputStat = fs.statSync(output);
    console.log(`  原文件: ${formatBytes(inputStat.size)} → 新文件: ${formatBytes(outputStat.size)}`);
    
    return true;
}

// 压缩图片
async function compressImage(input, output, options = {}) {
    const sharp = await getSharp();
    
    if (!fs.existsSync(input)) {
        console.error(colors.red(`错误: 文件不存在 ${input}`));
        return false;
    }
    
    output = output || input.replace(path.extname(input), `.compressed${path.extname(input)}`);
    const quality = parseInt(options.quality || options.q) || 80;
    
    const ext = path.extname(input).toLowerCase();
    let pipeline = sharp(input);
    
    if (ext === '.jpg' || ext === '.jpeg') {
        pipeline = pipeline.jpeg({ quality, progressive: true, mozjpeg: true });
    } else if (ext === '.png') {
        pipeline = pipeline.png({ quality, progressive: true });
    } else if (ext === '.webp') {
        pipeline = pipeline.webp({ quality });
    } else {
        // 默认转为JPEG
        output = output.replace(path.extname(output), '.jpg');
        pipeline = pipeline.jpeg({ quality, progressive: true });
    }
    
    await pipeline.toFile(output);
    console.log(colors.green(`✓ 压缩完成: ${output}`));
    
    const inputStat = fs.statSync(input);
    const outputStat = fs.statSync(output);
    const ratio = ((1 - outputStat.size / inputStat.size) * 100).toFixed(1);
    console.log(`  原文件: ${formatBytes(inputStat.size)} → 新文件: ${formatBytes(outputStat.size)} (节省 ${ratio}%)`);
    
    return true;
}

// 批量转换
async function batchConvert(dir, options = {}) {
    const fs = require('fs').promises;
    const path = require('path');
    
    if (!fs.existsSync(dir)) {
        console.error(colors.red(`错误: 目录不存在 ${dir}`));
        return false;
    }
    
    const format = (options.format || options.f || 'jpg').toLowerCase();
    const quality = parseInt(options.quality || options.q) || 80;
    
    const files = await fs.readdir(dir);
    const imageFiles = files.filter(f => /\.(jpg|jpeg|png|webp|gif|bmp|tiff)$/i.test(f));
    
    if (imageFiles.length === 0) {
        console.log(colors.yellow('没有找到图片文件'));
        return false;
    }
    
    console.log(colors.blue(`找到 ${imageFiles.length} 个图片文件，开始转换...`));
    
    const outputDir = path.join(dir, `converted_${format}`);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    let success = 0;
    for (const file of imageFiles) {
        const input = path.join(dir, file);
        const output = path.join(outputDir, path.parse(file).name + '.' + format);
        
        try {
            await convertImage(input, output, { quality });
            success++;
        } catch (err) {
            console.error(colors.red(`  ✗ ${file}: ${err.message}`));
        }
    }
    
    console.log(colors.green(`\n✓ 完成: ${success}/${imageFiles.length} 个文件转换成功`));
    console.log(`输出目录: ${outputDir}`);
    
    return true;
}

// 视频转GIF
async function videoToGif(input, output, options = {}) {
    const ffmpeg = await getFfmpeg();
    
    if (!fs.existsSync(input)) {
        console.error(colors.red(`错误: 视频文件不存在 ${input}`));
        return false;
    }
    
    const start = parseFloat(options.start || options.s) || 0;
    const duration = parseFloat(options.duration || options.t) || 10;
    const width = parseInt(options.width || options.w) || 480;
    const fps = parseInt(options.fps) || 10;
    
    console.log(colors.blue(`正在转换 GIF...`));
    console.log(`  开始: ${start}s, 时长: ${duration}s, 宽度: ${width}px, 帧率: ${fps}`);
    
    return new Promise((resolve, reject) => {
        ffmpeg(input)
            .setStartTime(start)
            .setDuration(duration)
            .size(`${width}x?`)
            .fps(fps)
            .output(output)
            .on('end', () => {
                const stat = fs.statSync(output);
                console.log(colors.green(`✓ GIF 转换完成: ${output}`));
                console.log(`  文件大小: ${formatBytes(stat.size)}`);
                resolve(true);
            })
            .on('error', (err) => {
                console.error(colors.red(`错误: ${err.message}`));
                resolve(false);
            })
            .run();
    });
}

// 合并PDF
async function mergePdfs(files, output) {
    const { PDFDocument } = await getPdfLib();
    
    const mergedPdf = await PDFDocument.create();
    
    for (const file of files) {
        if (!fs.existsSync(file)) {
            console.error(colors.red(`错误: 文件不存在 ${file}`));
            continue;
        }
        
        const pdfBytes = fs.readFileSync(file);
        const pdf = await PDFDocument.load(pdfBytes);
        const pages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
        pages.forEach(page => mergedPdf.addPage(page));
        console.log(`  添加: ${file} (${pages.length}页)`);
    }
    
    const mergedBytes = await mergedPdf.save();
    fs.writeFileSync(output, mergedBytes);
    
    console.log(colors.green(`✓ PDF合并完成: ${output}`));
    return true;
}

// PDF转图片
async function pdfToImages(input, outputDir) {
    const sharp = await getSharp();
    const { pdf } = await getPdfLib();
    
    if (!fs.existsSync(input)) {
        console.error(colors.red(`错误: PDF文件不存在 ${input}`));
        return false;
    }
    
    outputDir = outputDir || path.dirname(input);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    console.log(colors.yellow('PDF转图片需要 poppler-utils，请先安装: sudo apt-get install poppler-utils'));
    console.log(colors.blue('或使用: pdftoppm input.pdf output -png'));
    
    return true;
}

// 查看文件信息
async function showInfo(file) {
    if (!fs.existsSync(file)) {
        console.error(colors.red(`错误: 文件不存在 ${file}`));
        return;
    }
    
    const stat = fs.statSync(file);
    console.log(colors.blue(`文件信息: ${file}`));
    console.log(`  大小: ${formatBytes(stat.size)}`);
    console.log(`  修改时间: ${stat.mtime.toLocaleString()}`);
    
    const ext = path.extname(file).toLowerCase();
    
    if (/\.(jpg|jpeg|png|webp|gif|bmp)$/i.test(ext)) {
        try {
            const sharp = await getSharp();
            const metadata = await sharp(file).metadata();
            console.log(`  格式: ${metadata.format}`);
            console.log(`  尺寸: ${metadata.width} x ${metadata.height}`);
            console.log(`  通道: ${metadata.channels}`);
        } catch (e) {
            console.log(`  无法读取图片信息: ${e.message}`);
        }
    } else if (/\.(mp4|avi|mov|mkv|webm)$/i.test(ext)) {
        try {
            const ffmpeg = await getFfmpeg();
            ffmpeg.ffprobe(file, (err, metadata) => {
                if (err) return;
                const video = metadata.streams.find(s => s.codec_type === 'video');
                if (video) {
                    console.log(`  格式: ${metadata.format.format_name}`);
                    console.log(`  分辨率: ${video.width} x ${video.height}`);
                    console.log(`  时长: ${formatDuration(metadata.format.duration)}`);
                    console.log(`  码率: ${(metadata.format.bit_rate / 1000).toFixed(0)} kbps`);
                }
            });
        } catch (e) {}
    }
}

// 格式化字节
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时长
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// 主函数
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0 || args[0] === 'help') {
        showHelp();
        return;
    }
    
    const command = args[0];
    const { positional, options } = parseArgs(args.slice(1));
    
    try {
        switch (command) {
            case 'convert':
                if (positional.length < 2) {
                    console.error(colors.red('用法: convert <输入> <输出> [选项]'));
                    return;
                }
                await convertImage(positional[0], positional[1], options);
                break;
                
            case 'compress':
                if (positional.length < 1) {
                    console.error(colors.red('用法: compress <输入> [输出] [选项]'));
                    return;
                }
                await compressImage(positional[0], positional[1], options);
                break;
                
            case 'batch':
                if (positional.length < 1) {
                    console.error(colors.red('用法: batch <目录> [选项]'));
                    return;
                }
                await batchConvert(positional[0], options);
                break;
                
            case 'video2gif':
                if (positional.length < 2) {
                    console.error(colors.red('用法: video2gif <视频> <输出.gif> [选项]'));
                    return;
                }
                await videoToGif(positional[0], positional[1], options);
                break;
                
            case 'merge':
                if (positional.length < 3) {
                    console.error(colors.red('用法: merge <pdf1> <pdf2> <输出>'));
                    return;
                }
                const output = positional.pop();
                await mergePdfs(positional, output);
                break;
                
            case 'pdf2img':
                if (positional.length < 1) {
                    console.error(colors.red('用法: pdf2img <pdf> [输出目录]'));
                    return;
                }
                await pdfToImages(positional[0], positional[1]);
                break;
                
            case 'info':
                if (positional.length < 1) {
                    console.error(colors.red('用法: info <文件>'));
                    return;
                }
                await showInfo(positional[0]);
                break;
                
            case 'formats':
                console.log(colors.blue('=== 支持的格式 ==='));
                console.log(colors.yellow('图片:') + ' jpg, jpeg, png, webp, gif, bmp, tiff, avif');
                console.log(colors.yellow('视频:') + ' mp4, avi, mov, mkv, webm, flv');
                console.log(colors.yellow('PDF:') + ' 合并、拆分、转图片');
                break;
                
            default:
                console.error(colors.red(`未知命令: ${command}`));
                showHelp();
        }
    } catch (err) {
        console.error(colors.red(`错误: ${err.message}`));
        process.exit(1);
    }
}

main();
