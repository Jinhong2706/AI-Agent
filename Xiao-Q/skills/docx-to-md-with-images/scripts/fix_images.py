import os, shutil, re, sys

def fix_images(md_path):
    """Flatten img/media/ to img/ and fix all image paths in markdown."""
    # Step 1: Flatten img/media to img/
    src = './img/media'
    dst = './img'

    if os.path.isdir(src):
        for f in os.listdir(src):
            src_path = os.path.join(src, f)
            if os.path.isfile(src_path):
                shutil.move(src_path, os.path.join(dst, f))
        os.removedirs(src)
        print(f"Flattened images from img/media/ to img/")
    else:
        print("No img/media/ directory found, skipping flatten step.")

    # Step 2: Fix image paths in markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    def replace_img_tag(m):
        filename = m.group(1)
        return f'![{filename}](./img/{filename})'

    # Convert <img src=".../imageX.ext" ... /> to ![imageX.ext](./img/imageX.ext)
    content = re.sub(
        r'<img\s+src="[^"]*?/(image\d+\.\w+)"[^>]*>',
        replace_img_tag,
        content
    )

    # Convert ![](absolute/path/imageX.ext) to ![imageX.ext](./img/imageX.ext)
    content = re.sub(
        r'!\[\]\([^)]*?/(image\d+\.\w+)\)',
        r'![\1](./img/\1)',
        content
    )

    # Remove leftover style attributes after image refs
    content = re.sub(
        r'(\!\[.*?\]\(\./img/.*?\))\s*style="[^"]*"\s*/?>',
        r'\1',
        content
    )

    # Remove stray <p> tags wrapping images
    content = re.sub(
        r'<p>(!\[.*?\]\(\./img/.*?\))</p>',
        r'\1',
        content
    )

    content = re.sub(
        r'<p>(!\[.*?\]\(\./img/.*?\))',
        r'\1',
        content
    )

    # Remove trailing /> after style removal
    content = re.sub(
        r'(\!\[.*?\]\(\./img/.*?\))\s*/>',
        r'\1',
        content
    )

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Count results
    img_refs = len(re.findall(r'!\[.*?\]\(\./img/', content))
    leftover_tags = len(re.findall(r'<img src=', content))
    print(f"Fixed image paths: {img_refs} references, {leftover_tags} leftover <img> tags")

if __name__ == '__main__':
    md_file = sys.argv[1] if len(sys.argv) > 1 else 'output.md'
    fix_images(md_file)
