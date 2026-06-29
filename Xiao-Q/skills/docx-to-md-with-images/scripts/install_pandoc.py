import subprocess, sys, os, platform

def install_pandoc():
    system = platform.system()

    if system == 'Darwin':
        # macOS
        try:
            subprocess.run(['brew', '--version'], check=True, capture_output=True)
            print("Installing pandoc via Homebrew...")
            subprocess.run(['brew', 'install', 'pandoc'], check=True)
            return True
        except FileNotFoundError:
            print("Homebrew not found. Install it from https://brew.sh or install pandoc manually.")
            return False

    elif system == 'Linux':
        # Try apt, yum, or pacman
        for pkg_mgr in [['apt-get', 'update'], ['apt-get', 'install', '-y'],
                        ['yum', 'install', '-y'], ['pacman', '-S', '--noconfirm']]:
            try:
                cmd = pkg_mgr[:1]
                if 'update' in pkg_mgr:
                    subprocess.run(cmd, check=True, capture_output=True)
                    continue
                print(f"Installing pandoc via {pkg_mgr[0]}...")
                subprocess.run(pkg_mgr + ['pandoc'], check=True)
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        print("No supported package manager found. Install pandoc manually from https://pandoc.org/installing.html")
        return False

    elif system == 'Windows':
        # Try winget, then scoop, then direct download
        try:
            print("Installing pandoc via winget...")
            result = subprocess.run(
                ['winget', 'install', '--id', 'JohnMacFarlane.Pandoc', '-e', '--accept-package-agreements', '--accept-source-agreements'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("Pandoc installed via winget.")
                return True
        except FileNotFoundError:
            pass

        try:
            print("Installing pandoc via scoop...")
            result = subprocess.run(['scoop', 'install', 'pandoc'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Pandoc installed via scoop.")
                return True
        except FileNotFoundError:
            pass

        # Fallback: download MSI from GitHub
        print("winget and scoop not available. Downloading pandoc from GitHub...")
        import urllib.request
        url = "https://github.com/jgm/pandoc/releases/latest/download/pandoc-3.9-windows-x86_64.msi"
        msi_path = os.path.join(os.environ.get('TEMP', '.'), 'pandoc.msi')
        print(f"Downloading from {url}")
        try:
            urllib.request.urlretrieve(url, msi_path)
            print(f"Downloaded to {msi_path}")
            print(f"Installing via msiexec...")
            subprocess.run(['msiexec', '/i', msi_path, '/qn', '/norestart'], check=True)
            pandoc_path = r'C:\Program Files\Pandoc'
            if os.path.isdir(pandoc_path):
                current_path = os.environ.get('PATH', '')
                if pandoc_path not in current_path:
                    subprocess.run(
                        ['setx', 'PATH', f'{current_path};{pandoc_path}'],
                        capture_output=True
                    )
                    os.environ['PATH'] = f'{current_path};{pandoc_path}'
                print(f"Pandoc installed to {pandoc_path}")
                return True
        except Exception as e:
            print(f"Download/install failed: {e}")
            print("Please install pandoc manually from https://github.com/jgm/pandoc/releases/latest")
            return False

    else:
        print(f"Unsupported platform: {system}")
        return False

if __name__ == '__main__':
    success = install_pandoc()
    if success:
        print("Pandoc is ready.")
    else:
        print("Pandoc installation failed. Please install manually.")
        sys.exit(1)
