#!/usr/bin/env python3
"""
Excel 统计图生成脚本
从 Excel 文件读取数据并生成各类统计图表。

用法:
  python generate_chart.py <excel_path> --mode preview
  python generate_chart.py <excel_path> --chart-type bar --x-column "分类" --y-column "销售额"
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("错误: 缺少 pandas 库，请运行: pip install pandas openpyxl")
    sys.exit(1)


def read_excel(excel_path):
    """读取 Excel 文件，返回所有 sheet 的 DataFrame 字典"""
    excel_path = Path(excel_path)
    if not excel_path.exists():
        print(f"错误: 文件不存在: {excel_path}")
        sys.exit(1)

    try:
        xls = pd.ExcelFile(excel_path)
        sheets = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
            sheets[sheet_name] = df
        return sheets
    except Exception as e:
        print(f"错误: 无法读取 Excel 文件: {e}")
        sys.exit(1)


def preview_data(sheets):
    """预览所有 sheet 的数据结构"""
    for sheet_name, df in sheets.items():
        print(f"\n{'='*60}")
        print(f"📋 Sheet: {sheet_name}")
        print(f"{'='*60}")
        print(f"行数: {len(df)} | 列数: {len(df.columns)}")

        print(f"\n列信息:")
        for col in df.columns:
            dtype = df[col].dtype
            non_null = df[col].notna().sum()
            null_count = df[col].isna().sum()
            sample_type = "数值" if pd.api.types.is_numeric_dtype(df[col]) else "分类/文本"

            extra = ""
            if pd.api.types.is_numeric_dtype(df[col]):
                try:
                    extra = f" | 范围: {df[col].min():.2f} ~ {df[col].max():.2f} | 均值: {df[col].mean():.2f}"
                except Exception:
                    pass

            print(f"  - {col} ({sample_type}) 非空: {non_null}/{len(df)} 空值: {null_count}{extra}")

        print(f"\n前 5 行数据:")
        print(df.head().to_string(index=False))
        print()


def detect_column_types(df):
    """自动检测分类列和数值列"""
    numeric_cols = []
    categorical_cols = []
    date_cols = []

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif df[col].nunique() < min(len(df) * 0.5, 20):
            categorical_cols.append(col)
        else:
            try:
                pd.to_datetime(df[col], errors="raise")
                date_cols.append(col)
            except (ValueError, TypeError):
                categorical_cols.append(col)

    return numeric_cols, categorical_cols, date_cols


def auto_recommend_chart(numeric_cols, categorical_cols, date_cols):
    """根据列类型自动推荐图表类型"""
    if len(numeric_cols) == 0:
        return None, "没有找到数值列，无法生成图表"

    if len(numeric_cols) == 1:
        if len(date_cols) >= 1:
            return ("line", f"推荐使用折线图展示 {date_cols[0]} 与 {numeric_cols[0]} 的趋势")
        if len(categorical_cols) >= 1:
            return ("bar", f"推荐使用柱状图对比不同 {categorical_cols[0]} 的 {numeric_cols[0]}")
        return ("bar", "推荐使用柱状图展示数据分布")

    if len(numeric_cols) == 2 and len(categorical_cols) == 0:
        return ("scatter", f"推荐使用散点图展示 {numeric_cols[0]} 与 {numeric_cols[1]} 的关系")

    if len(numeric_cols) >= 2 and len(categorical_cols) >= 1:
        return ("box", f"推荐使用箱线图展示不同 {categorical_cols[0]} 下的数值分布")

    if len(numeric_cols) >= 3:
        return ("heatmap", "推荐使用热力图展示各数值列之间的相关性")

    return ("bar", "推荐使用柱状图展示数据")


def generate_chart(excel_path, sheet=None, chart_type="auto", x_column=None,
                   y_column=None, title="", subtitle="", output=None,
                   output_format="html", width=1000, height=600,
                   palette="default", horizontal=False, sort=False,
                   top=None):
    """生成图表的主函数"""
    # 读取数据
    sheets = read_excel(excel_path)

    # 选择 sheet
    if sheet is None or sheet not in sheets:
        sheet = list(sheets.keys())[0]
        print(f"使用 sheet: {sheet}")
    df = sheets[sheet]
    df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)

    if df.empty:
        print("错误: 数据为空")
        sys.exit(1)

    # 检测列类型
    numeric_cols, categorical_cols, date_cols = detect_column_types(df)
    print(f"数值列: {numeric_cols}")
    print(f"分类列: {categorical_cols}")
    print(f"日期列: {date_cols}")

    # 自动选择 X/Y 列
    if x_column is None and chart_type != "auto":
        if len(categorical_cols) > 0 and chart_type in ("bar", "pie", "box"):
            x_column = categorical_cols[0]
        elif len(date_cols) > 0 and chart_type in ("line",):
            x_column = date_cols[0]
        elif len(numeric_cols) > 0:
            x_column = numeric_cols[0]
        print(f"自动选择 X 列: {x_column}")

    if y_column is None and chart_type != "auto":
        available = [c for c in numeric_cols if c != x_column]
        if available:
            if chart_type in ("box", "heatmap"):
                y_column = ",".join(available)
                print(("使用数值列: " + y_column))
            else:
                y_column = available[0]
                print(f"自动选择 Y 列: {y_column}")

    # 自动推荐图表类型
    if chart_type == "auto":
        chart_type, reason = auto_recommend_chart(numeric_cols, categorical_cols, date_cols)
        if chart_type is None:
            print(reason)
            sys.exit(1)
        print(f"{reason}")
        # 自动选择列
        if x_column is None:
            if chart_type in ("bar", "pie", "box") and categorical_cols:
                x_column = categorical_cols[0]
            elif chart_type in ("line",) and date_cols:
                x_column = date_cols[0]
            elif numeric_cols:
                x_column = numeric_cols[0]
        if y_column is None:
            available = [c for c in numeric_cols if c != x_column]
            if chart_type in ("box", "heatmap"):
                y_column = ",".join(available if available else numeric_cols[:3])
            else:
                y_column = available[0] if available else numeric_cols[0]

    # 自动生成标题
    if not title:
        title = f"{Path(excel_path).stem} - {sheet}"
    if not subtitle:
        subtitle = f"{chart_type.upper()} 图 | X: {x_column} | Y: {y_column}"

    # 处理 top N
    y_col_list = [c.strip() for c in y_column.split(",")] if y_column else []

    if top is not None and x_column and y_col_list:
        if sort:
            df = df.sort_values(y_col_list[0], ascending=False)
        df = df.head(top)

    # 根据图表类型生成
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    color_map = {
        "default": px.colors.qualitative.Plotly,
        "vivid": px.colors.qualitative.Vivid,
        "pastel": px.colors.qualitative.Pastel,
        "dark": px.colors.qualitative.Dark2,
    }
    colors = color_map.get(palette, px.colors.qualitative.Plotly)

    fig = None

    if chart_type == "bar":
        if x_column and y_col_list:
            y_col = y_col_list[0]
            if horizontal:
                fig = px.bar(df, y=x_column, x=y_col,
                             title=f"{title}<br><sub>{subtitle}</sub>",
                             color=x_column, color_discrete_sequence=colors,
                             orientation="h")
            else:
                fig = px.bar(df, x=x_column, y=y_col,
                             title=f"{title}<br><sub>{subtitle}</sub>",
                             color=x_column, color_discrete_sequence=colors)
            if sort and y_col:
                fig.update_layout(xaxis={"categoryorder": "total descending"})

    elif chart_type == "line":
        if x_column and y_col_list:
            y_col = y_col_list[0]
            # 尝试转换 X 列为日期
            try:
                df[x_column] = pd.to_datetime(df[x_column])
            except Exception:
                pass
            fig = px.line(df, x=x_column, y=y_col,
                          title=f"{title}<br><sub>{subtitle}</sub>",
                          markers=True, color_discrete_sequence=colors)
            fig.update_traces(line=dict(width=2.5))

            # 如果 X 列是日期，自动格式化
            if pd.api.types.is_datetime64_any_dtype(df[x_column]):
                fig.update_xaxes(
                    dtick="M1",
                    tickformat="%Y-%m-%d",
                    ticklabelmode="period"
                )

    elif chart_type == "pie":
        if x_column and y_col_list:
            y_col = y_col_list[0]
            # 过滤负值
            df_pie = df[df[y_col] > 0].copy()
            if df_pie.empty:
                print("警告: 没有正数值，饼图无法展示")
                sys.exit(1)
            fig = px.pie(df_pie, names=x_column, values=y_col,
                         title=f"{title}<br><sub>{subtitle}</sub>",
                         color_discrete_sequence=colors)
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              pull=[0.03] * len(df_pie))
            # 添加环形效果
            fig.update_layout(
                annotations=[dict(text=f"{y_col}", showarrow=False, font_size=16)]
            )

    elif chart_type == "scatter":
        if x_column and y_col_list:
            y_col = y_col_list[0]
            fig = px.scatter(df, x=x_column, y=y_col,
                             title=f"{title}<br><sub>{subtitle}</sub>",
                             color=categorical_cols[0] if categorical_cols else None,
                             size=y_col if len(df) < 200 else None,
                             hover_data=df.columns,
                             color_discrete_sequence=colors)
            # 添加趋势线
            fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=1, color="white")))

    elif chart_type == "box":
        if x_column and y_col_list:
            fig = px.box(df, x=x_column, y=y_col_list[0] if len(y_col_list) == 1 else None,
                         title=f"{title}<br><sub>{subtitle}</sub>",
                         color=x_column if len(y_col_list) == 1 else None,
                         color_discrete_sequence=colors)
            if len(y_col_list) > 1:
                # 多列箱线图
                df_melt = df.melt(value_vars=y_col_list, var_name="变量", value_name="数值")
                fig = px.box(df_melt, x="变量", y="数值",
                             title=f"{title}<br><sub>{subtitle}</sub>",
                             color="变量", color_discrete_sequence=colors)

    elif chart_type == "heatmap":
        if y_col_list:
            if len(y_col_list) >= 2:
                # 相关性热力图
                corr_df = df[y_col_list].corr()
                fig = px.imshow(corr_df, text_auto=".2f",
                                title=f"{title}<br><sub>相关性热力图</sub>",
                                color_continuous_scale="RdBu_r",
                                aspect="auto",
                                width=width, height=height)
                fig.update_traces(hovertemplate="X: %{x}<br>Y: %{y}<br>相关系数: %{z:.3f}<extra></extra>")
            elif x_column:
                # 交叉表热力图
                cross = pd.crosstab(df[x_column], df[y_col_list[0]])
                fig = px.imshow(cross, text_auto=True,
                                title=f"{title}<br><sub>{subtitle}</sub>",
                                color_continuous_scale="YlOrRd",
                                aspect="auto")

    if fig is None:
        print(f"错误: 无法生成 {chart_type} 图表，请检查列名和数据类型")
        print(f"X 列: {x_column}, Y 列: {y_column}")
        sys.exit(1)

    # 图表布局美化
    fig.update_layout(
        template="plotly_white",
        width=width,
        height=height,
        font=dict(family="Microsoft YaHei, SimHei, Arial", size=13),
        title=dict(x=0.5, xanchor="center"),
        hovermode="x unified" if chart_type in ("line", "bar") else "closest",
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(title=dict(text=x_column, standoff=10)),
        yaxis=dict(title=dict(text=", ".join(y_col_list) if y_col_list else "", standoff=10)),
    )

    # 输出文件
    if output is None:
        base = Path(excel_path).stem
        output = f"{base}_{chart_type}"

    output_path = Path(output)
    if output_format == "html":
        html_path = output_path.with_suffix(".html")
        fig.write_html(str(html_path), include_plotlyjs="cdn", config={
            "displaylogo": False,
            "modeBarButtonsToAdd": ["drawline", "eraseshape"],
            "toImageButtonOptions": {"format": "png", "scale": 2},
        })
        print(f"\n✅ HTML 图表已生成: {html_path.resolve()}")
        return str(html_path.resolve())

    elif output_format == "png":
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("错误: 缺少 matplotlib 库，请运行: pip install matplotlib")
            sys.exit(1)

        png_path = output_path.with_suffix(".png")
        fig.write_image(str(png_path), width=width, height=height, scale=2)
        print(f"\n✅ PNG 图片已生成: {png_path.resolve()}")
        return str(png_path.resolve())

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Excel 统计图生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.xlsx --mode preview
  %(prog)s data.xlsx --chart-type bar --x-column "城市" --y-column "销售额"
  %(prog)s data.xlsx --chart-type line --x-column "日期" --y-column "温度" --output-format png
  %(prog)s data.xlsx --chart-type auto --top 10 --sort
        """
    )
    parser.add_argument("excel_path", help="Excel 文件路径")
    parser.add_argument("--mode", choices=["preview", "chart"], default="chart",
                        help="运行模式：preview 预览数据，chart 生成图表（默认）")
    parser.add_argument("--sheet", default=None, help="使用的 sheet 名称")
    parser.add_argument("--chart-type", default="auto",
                        choices=["bar", "line", "pie", "scatter", "box", "heatmap", "auto"],
                        help="图表类型（默认: auto）")
    parser.add_argument("--x-column", default=None, help="X 轴列名")
    parser.add_argument("--y-column", default=None, help="Y 轴列名（多个用逗号分隔）")
    parser.add_argument("--title", default="", help="图表标题")
    parser.add_argument("--subtitle", default="", help="图表副标题")
    parser.add_argument("--output", default=None, help="输出文件路径（不含扩展名）")
    parser.add_argument("--output-format", choices=["html", "png"], default="html",
                        help="输出格式（默认: html）")
    parser.add_argument("--width", type=int, default=1000, help="图表宽度（默认: 1000）")
    parser.add_argument("--height", type=int, default=600, help="图表高度（默认: 600）")
    parser.add_argument("--palette", choices=["default", "vivid", "pastel", "dark"],
                        default="default", help="配色方案")
    parser.add_argument("--horizontal", action="store_true", help="水平条形图")
    parser.add_argument("--sort", action="store_true", help="按数值排序")
    parser.add_argument("--top", type=int, default=None, help="仅显示前 N 条")

    args = parser.parse_args()

    if args.mode == "preview":
        sheets = read_excel(args.excel_path)
        preview_data(sheets)
        return

    result = generate_chart(
        excel_path=args.excel_path,
        sheet=args.sheet,
        chart_type=args.chart_type,
        x_column=args.x_column,
        y_column=args.y_column,
        title=args.title,
        subtitle=args.subtitle,
        output=args.output,
        output_format=args.output_format,
        width=args.width,
        height=args.height,
        palette=args.palette,
        horizontal=args.horizontal,
        sort=args.sort,
        top=args.top,
    )

    if result:
        print(f"输出文件: {result}")


if __name__ == "__main__":
    main()
