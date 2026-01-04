"""
前端页面视图 - SPA 模式
"""
import json
from pathlib import Path
from django.shortcuts import render
from django.conf import settings


def get_vite_assets():
    """读取 Vite manifest 获取构建后的资源路径"""
    manifest_path = Path(settings.BASE_DIR) / 'static' / '.vite' / 'manifest.json'
    if not manifest_path.exists():
        return {}

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # 查找入口文件
    entry = manifest.get('index.html', {})
    return {
        'js_file': entry.get('file', ''),
        'css_files': entry.get('css', []),
    }


def spa_view(request, path=''):
    """SPA 入口视图 - 所有前端路由都返回同一个 HTML"""
    context = {
        'debug': settings.DEBUG,
    }

    if not settings.DEBUG:
        assets = get_vite_assets()
        context['assets'] = assets

    return render(request, 'index.html', context)
