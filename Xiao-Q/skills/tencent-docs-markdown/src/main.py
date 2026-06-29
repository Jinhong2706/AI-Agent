"""
Tencent Docs Markdown Skill - Main Entry

This is the main entry point that provides natural language command processing
for Tencent Docs Markdown operations.
"""

import json
import os
import re
import sys
from pathlib import Path

import click

from .auth import ensure_login, force_re_login
from .api import (
    create_document,
    delete_document,
    read_document,
    write_document,
    get_document_info,
    rename_document,
    parse_pad_id_from_url,
    resolve_real_pad_id,
    DEFAULT_DOMAIN_ID,
)


def handle_create(title: str, content: str | None = None) -> dict:
    """
    Create a new Markdown document.

    Args:
        title: Document title
        content: Optional initial content
    """
    print('📝 Creating Markdown document...')
    try:
        cookies = ensure_login()
        result = create_document(cookies, title)
        print(f"✅ Document created: {result['title']}")
        print(f"  📄 URL: {result['docUrl']}")
        print(f"  🆔 Pad ID: {result['padId']}")

        # If content is provided, write it to the document
        if content:
            print('   Writing content...')
            write_document(cookies, result['globalPadId'], content)
            print('✅ Content written successfully.')

        return result
    except Exception as err:
        print(f"❌ Create failed: {err}")
        raise


def handle_create_and_write(title: str, content: str) -> dict:
    """
    Create a new Tencent Docs Markdown document and write content to it.

    Args:
        title: Document title
        content: Markdown content to write

    Returns:
        dict with keys: docUrl, padId, globalPadId, title
    """
    print('📝 Creating Markdown document on Tencent Docs...')
    try:
        if not title:
            raise ValueError('Document title is required')
        if not content:
            raise ValueError('Markdown content is required')

        cookies = ensure_login()

        # Step 1: Create a new Markdown document
        print('   Creating document...')
        result = create_document(cookies, title)

        # Step 2: Write Markdown content to the document
        print('   Writing Markdown content...')
        write_document(cookies, result['globalPadId'], content)

        print(f"✅ Document created and content written: {title}")
        print(f"  📄 URL: {result['docUrl']}")
        print(f"  🆔 Pad ID: {result['padId']}")

        return result
    except Exception as err:
        print(f"❌ Create and write failed: {err}")
        raise


def handle_download(doc_url: str, output_path: str | None = None) -> dict:
    """
    Download a Tencent Docs Markdown document to local file.

    Args:
        doc_url: Tencent Docs URL
        output_path: Optional output file path
    """
    print('📥 Downloading Markdown document...')
    try:
        cookies = ensure_login()

        # Resolve the real padId from the document page
        print('   Resolving document ID...')
        doc_meta = resolve_real_pad_id(cookies, doc_url)
        global_pad_id = doc_meta['globalPadId']
        doc_title = doc_meta.get('title', '')
        pad_id = doc_meta['padId']

        # Read content
        print('   Reading document content...')
        content = read_document(cookies, global_pad_id)

        # Determine output path
        save_path = output_path
        if not save_path:
            name = doc_title or pad_id
            save_path = re.sub(r'[/\\?%*:|"<>]', '_', name) + '.md'

        # Ensure .md extension
        if not save_path.endswith('.md'):
            save_path += '.md'

        resolved_path = str(Path(save_path).resolve())
        with open(resolved_path, 'w', encoding='utf-8') as f:
            f.write(content)

        size = len(content.encode('utf-8'))
        print(f"✅ Downloaded to: {resolved_path}")
        print(f"  📦 Size: {size} bytes")

        return {'path': resolved_path, 'content': content}
    except Exception as err:
        print(f"❌ Download failed: {err}")
        raise


def handle_delete(doc_url: str) -> dict:
    """
    Delete a Tencent Docs Markdown document.

    Args:
        doc_url: Tencent Docs URL
    """
    print('🗑️  Deleting Markdown document...')
    try:
        cookies = ensure_login()

        # Resolve the real padId from the document page
        print('   Resolving document ID...')
        doc_meta = resolve_real_pad_id(cookies, doc_url)
        pad_id = doc_meta['padId']

        if not pad_id:
            raise RuntimeError(f'Cannot resolve real pad ID from URL: {doc_url}')

        delete_document(cookies, pad_id)

        print(f"✅ Document deleted (moved to trash): {pad_id}")
        return {'padId': pad_id, 'deleted': True}
    except Exception as err:
        print(f"❌ Delete failed: {err}")
        raise


def handle_read(doc_url: str) -> str:
    """
    Read and display document content.

    Args:
        doc_url: Tencent Docs URL
    """
    print('📖 Reading Markdown document...')
    try:
        cookies = ensure_login()

        # Resolve the real padId from the document page
        print('   Resolving document ID...')
        doc_meta = resolve_real_pad_id(cookies, doc_url)
        global_pad_id = doc_meta['globalPadId']

        content = read_document(cookies, global_pad_id)

        print('✅ Document content retrieved.')
        print('─' * 60)
        print(content)
        print('─' * 60)

        return content
    except Exception as err:
        print(f"❌ Read failed: {err}")
        raise


def handle_update(doc_url: str, content_or_path: str) -> dict:
    """
    Update document content from a local file or text.

    Args:
        doc_url: Tencent Docs URL
        content_or_path: Markdown content or path to .md file
    """
    print('📝 Updating Markdown document...')
    try:
        cookies = ensure_login()

        # Resolve the real padId from the document page
        print('   Resolving document ID...')
        doc_meta = resolve_real_pad_id(cookies, doc_url)
        global_pad_id = doc_meta['globalPadId']
        pad_id = doc_meta['padId']

        # Determine if content_or_path is a file path or direct content
        content = content_or_path
        resolved_path = str(Path(content_or_path).resolve())
        if os.path.exists(resolved_path) and resolved_path.endswith('.md'):
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   Updating from file: {resolved_path}")

        write_document(cookies, global_pad_id, content)

        print('✅ Document updated successfully.')
        return {'padId': pad_id, 'updated': True}
    except Exception as err:
        print(f"❌ Update failed: {err}")
        raise


def handle_rename(doc_url: str, new_title: str) -> dict:
    """
    Rename a document.

    Args:
        doc_url: Tencent Docs URL
        new_title: New title
    """
    print('✏️  Renaming document...')
    try:
        cookies = ensure_login()

        # Resolve the real padId from the document page
        print('   Resolving document ID...')
        doc_meta = resolve_real_pad_id(cookies, doc_url)
        pad_id = doc_meta['padId']

        if not pad_id:
            raise RuntimeError(f'Cannot resolve real pad ID from URL: {doc_url}')

        result = rename_document(cookies, pad_id, new_title)

        print(f"✅ Document renamed to: {new_title}")
        return {'padId': pad_id, 'newTitle': new_title, 'raw': result}
    except Exception as err:
        print(f"❌ Rename failed: {err}")
        raise


def handle_info(doc_url: str) -> dict:
    """
    Get document information.

    Args:
        doc_url: Tencent Docs URL
    """
    print('ℹ️  Getting document info...')
    try:
        cookies = ensure_login()
        pad_id = parse_pad_id_from_url(doc_url)

        if not pad_id:
            raise RuntimeError(f'Cannot parse document ID from URL: {doc_url}')

        info = get_document_info(cookies, pad_id)
        print('✅ Document info retrieved.')
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return info
    except Exception as err:
        print(f"❌ Info failed: {err}")
        raise


def handle_login(force: bool = False) -> None:
    """Login / re-login."""
    if force:
        force_re_login()
    else:
        ensure_login()


# ── CLI Entry ────────────────────────────────────────

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Tencent Docs Markdown CLI Tool"""
    pass


@cli.command()
@click.option('--force', is_flag=True, help='Force re-login (clear existing cookies)')
def login(force):
    """Login via QR code scanning."""
    handle_login(force)


@cli.command()
@click.argument('title')
@click.option('-c', '--content', default=None, help='Initial Markdown content')
def create(title, content):
    """Create a new Markdown document."""
    handle_create(title, content)


@cli.command()
@click.argument('title')
@click.argument('content')
def write(title, content):
    """Create a new Tencent Docs Markdown and write content to it."""
    handle_create_and_write(title, content)


@cli.command()
@click.argument('url')
@click.option('-o', '--output', default=None, help='Output file path')
def download(url, output):
    """Download a Tencent Docs Markdown document to local."""
    handle_download(url, output)


@cli.command()
@click.argument('url')
def delete(url):
    """Delete a Tencent Docs Markdown document."""
    handle_delete(url)


@cli.command()
@click.argument('url')
def read(url):
    """Read and display document content."""
    handle_read(url)


@cli.command()
@click.argument('url')
@click.argument('content')
def update(url, content):
    """Update document content (text or .md file path)."""
    handle_update(url, content)


@cli.command()
@click.argument('url')
@click.argument('title')
def rename(url, title):
    """Rename a document."""
    handle_rename(url, title)


@cli.command()
@click.argument('url')
def info(url):
    """Get document information."""
    handle_info(url)


if __name__ == '__main__':
    cli()
