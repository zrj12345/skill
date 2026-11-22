# -*- coding: utf-8 -*-
"""用 WPS 自己的 COM 接口导出 PDF、读取真实页数。

用法：
  python wps_export.py --doc DOC.docx --pdf OUT.pdf

环境坑：
- Word.Application 被 WPS 接管时会无限挂起，不要用 Word COM。
- PowerShell 里 New-Object -ComObject 可能被安全策略直接拦截；
  本脚本用 Python win32com，且用 DispatchEx 创建独立实例，避免连到用户已打开的 WPS。
- pywin32 / comtypes 可能未安装。若不可用，改用 pdf_patch.py 直接改已有 PDF 的内嵌图。
- 命令外层仍建议加硬超时（timeout 150），防止 COM 残留进程。
- WPS 打开文档会写回作者 admin；导出后必须重跑 strip_metadata.py。
"""
import argparse
import os
import sys

try:
    import win32com.client as win32
except ImportError:
    raise SystemExit("缺少 pywin32：pip install pywin32；或改用 scripts/pdf_patch.py")


def main():
    ap = argparse.ArgumentParser(description="WPS 导出 PDF 并读真实页数")
    ap.add_argument("--doc", required=True)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--timeout-note", action="store_true", help="打印超时建议")
    a = ap.parse_args()
    doc_path = os.path.abspath(a.doc)
    pdf_path = os.path.abspath(a.pdf)
    app = None
    doc = None
    try:
        app = win32.DispatchEx("Kwps.Application")
        app.Visible = False
        try:
            app.DisplayAlerts = 0
        except Exception:
            pass
        doc = app.Documents.Open(doc_path, False, True)  # ReadOnly
        try:
            pages = doc.ComputeStatistics(2)   # wdStatisticPages
            print("真实页数:", pages)
        except Exception:
            pass
        try:
            doc.ExportAsFixedFormat(pdf_path, 17)
        except Exception:
            doc.SaveAs2(pdf_path, 17)
        print("PDF:", pdf_path, os.path.getsize(pdf_path), "B")
    finally:
        if doc is not None:
            try:
                doc.Close(0)
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
