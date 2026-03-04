from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx

router = APIRouter()

@router.get("/pdf-proxy")
async def pdf_proxy(url: str = Query(...)):
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="invalid url")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="fetch failed")
            data = resp.content
            headers = {
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
            return Response(content=data, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"proxy error: {e}")

@router.get("/pdf-viewer")
async def pdf_viewer(file: str = Query(None), page: int = Query(None), search: str = Query(None), q: str = Query(None)):
    # 直接返回内嵌的 PDF.js 简易查看器页面，避免 /ui 基路径带来的路由冲突
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PDF Viewer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css" />
    <style>
      html, body {{ height: 100%; margin: 0; }}
      #viewerContainer {{ position: absolute; inset: 0; overflow: auto; background: #f5f7fa; }}
      #loadingOverlay {{
        position: absolute;
        inset: 0;
        background: rgba(255,255,255,0.92);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        z-index: 10000;
        color: #606266;
        font-family: Arial, Helvetica, sans-serif;
      }}
      .spinner {{
        width: 44px;
        height: 44px;
        border: 4px solid #faad14;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.9s linear infinite;
        margin-bottom: 12px;
      }}
      @keyframes spin {{
        to {{ transform: rotate(360deg); }}
      }}
      #loadingText {{
        font-size: 14px;
      }}
      .textLayer .highlight {{
        background-color: #0d9d33 !important;
        color: #856404 !important;
        border-radius: 2px;
        padding: 0 1px;
        mix-blend-mode: normal;
      }}
      .textLayer .highlight.selected {{
        background-color: #0d9d33 !important;
      }}
    </style>
  </head>
  <body>
    <div id="viewerContainer">
      <div id="viewer" class="pdfViewer"></div>
    </div>
    <div id="loadingOverlay">
      <div class="spinner"></div>
      <div id="loadingText">正在加载…</div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.js"></script>
    <script>
      (function() {{
        // 支持从查询参数接收 file/page/search （也兼容 hash 方式）
        var file = {repr(file) if file else "null"};
        var page = {page if page and page>0 else "null"};
        var query = {repr(search or q) if (search or q) else "null"};
        if (!file) {{
          var params = new URLSearchParams(location.search);
          file = params.get('file');
          var hashParams = new URLSearchParams(location.hash.replace(/^#/, ''));
          page = page || parseInt(hashParams.get('page') || params.get('page') || '0', 10) || null;
          query = query || hashParams.get('search') || params.get('search') || params.get('q') || null;
        }}
        if (!file) {{
          document.body.innerHTML = '<div style="padding:16px;color:#606266;">缺少 file 参数</div>';
          return;
        }}
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        var eventBus = new pdfjsViewer.EventBus();
        var container = document.getElementById('viewerContainer');
        var linkService = new pdfjsViewer.PDFLinkService({{ eventBus: eventBus }});
        var findController = new pdfjsViewer.PDFFindController({{ eventBus: eventBus, linkService: linkService }});
        var viewer = new pdfjsViewer.PDFViewer({{
          container: container,
          viewer: document.getElementById('viewer'),
          eventBus: eventBus,
          linkService: linkService,
          findController: findController,
          textLayerMode: 2
        }});
        linkService.setViewer(viewer);
        eventBus.on('pagesinit', function () {{
          viewer.currentScaleValue = 'page-width';
          if (Number.isFinite(page) && page > 0) {{ viewer.currentPageNumber = page; }}
          if (query && String(query).trim()) {{
            eventBus.dispatch('find', {{
              source: window,
              type: 'find',
              query: String(query),
              phraseSearch: true,
              caseSensitive: false,
              entireWord: false,
              highlightAll: true,
              findPrevious: false
            }});
          }}
          // 隐藏加载遮罩（如果尚未隐藏）
          var overlay = document.getElementById('loadingOverlay');
          if (overlay) overlay.style.display = 'none';
        }});
        var loadingTask = pdfjsLib.getDocument({{ url: file, withCredentials: false }});
        // 进度更新
        try {{
          loadingTask.onProgress = function (e) {{
            var overlay = document.getElementById('loadingOverlay');
            var text = document.getElementById('loadingText');
            if (overlay && text && e && e.total) {{
              var pct = Math.round(e.loaded * 100 / e.total);
              text.textContent = '正在加载… ' + pct + '%';
            }}
          }};
        }} catch (_e) {{}}
        loadingTask.promise.then(function (pdfDocument) {{
          viewer.setDocument(pdfDocument);
          linkService.setDocument(pdfDocument, null);
          // 文档就绪后隐藏加载遮罩
          var overlay = document.getElementById('loadingOverlay');
          if (overlay) overlay.style.display = 'none';
        }}).catch(function (reason) {{
          // 在遮罩上提示错误
          var overlay = document.getElementById('loadingOverlay');
          var spinner = document.querySelector('.spinner');
          var text = document.getElementById('loadingText');
          if (overlay && text) {{
            if (spinner) spinner.style.display = 'none';
            text.textContent = 'PDF 加载失败：' + String(reason);
          }} else {{
            container.innerHTML = '<div style="padding:16px;color:#c45656;">PDF 加载失败：' + String(reason) + '</div>';
          }}
        }});
      }})();
    </script>
  </body>
</html>"""
    return Response(content=html, media_type="text/html")
