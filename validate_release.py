"""
ChroLens_Mimic 發布驗證工具
用於檢查版本號一致性、Zip 檔案格式、GitHub API 可用性
"""

import os
import sys
import json
import zipfile
import re
import requests
from pathlib import Path

# 顏色輸出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")


class ReleaseValidator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.main_dir = self.base_dir / "main"
        self.errors = []
        self.warnings = []
        self.version = None
    
    def check_version_consistency(self):
        """檢查所有檔案中的版本號是否一致"""
        print_header("檢查版本號一致性")
        
        versions = {}
        
        # 1. ChroLens_Mimic.py
        mimic_file = self.main_dir / "ChroLens_Mimic.py"
        if mimic_file.exists():
            with open(mimic_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    versions['ChroLens_Mimic.py'] = match.group(1)
                    print_info(f"ChroLens_Mimic.py: {match.group(1)}")
                else:
                    self.errors.append("找不到 ChroLens_Mimic.py 中的 VERSION 變數")
        else:
            self.errors.append(f"找不到檔案: {mimic_file}")
        
        # 2. version_info.txt
        version_file = self.main_dir / "version_info.txt"
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 匹配 filevers=(2, 7, 1, 0) 格式
                match = re.search(r'filevers=\((\d+),\s*(\d+),\s*(\d+),\s*\d+\)', content)
                if match:
                    version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                    versions['version_info.txt'] = version
                    print_info(f"version_info.txt: {version}")
                else:
                    self.errors.append("找不到 version_info.txt 中的 filevers")
        else:
            self.warnings.append(f"找不到檔案: {version_file}")
        
        # 3. pack_safe.py
        pack_file = self.main_dir / "pack_safe.py"
        if pack_file.exists():
            with open(pack_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'self\.version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    versions['pack_safe.py'] = match.group(1)
                    print_info(f"pack_safe.py: {match.group(1)}")
                else:
                    self.warnings.append("找不到 pack_safe.py 中的 self.version（可能使用動態讀取）")
        else:
            self.warnings.append(f"找不到檔案: {pack_file}")
        
        # 檢查一致性
        unique_versions = set(versions.values())
        if len(unique_versions) == 1:
            self.version = list(unique_versions)[0]
            print_success(f"所有檔案版本號一致: {self.version}")
            return True
        elif len(unique_versions) > 1:
            self.errors.append(f"版本號不一致: {versions}")
            print_error("版本號不一致!")
            for file, ver in versions.items():
                print(f"  {file}: {ver}")
            return False
        else:
            self.errors.append("無法找到任何版本號")
            return False
    
    def check_zip_file(self, zip_path=None):
        """檢查 Zip 檔案格式和內容"""
        print_header("檢查更新包（Zip 檔案）")
        
        if zip_path:
            zip_file = Path(zip_path)
        else:
            # 自動尋找符合格式的 zip
            if not self.version:
                print_error("請先執行 --check-version 取得版本號")
                return False
            
            expected_name = f"ChroLens_Mimic_{self.version}.zip"
            zip_file = self.main_dir / expected_name
            
            if not zip_file.exists():
                # 嘗試在父目錄尋找
                zip_file = self.base_dir / expected_name
        
        if not zip_file.exists():
            print_error(f"找不到 Zip 檔案: {zip_file}")
            self.errors.append(f"找不到更新包: {zip_file.name}")
            return False
        
        print_info(f"檢查檔案: {zip_file.name}")
        
        # 檢查檔案名稱格式
        expected_pattern = r'ChroLens_Mimic_\d+\.\d+\.\d+\.zip'
        if not re.match(expected_pattern, zip_file.name):
            self.errors.append(f"檔案名稱格式錯誤: {zip_file.name}")
            print_error(f"檔案名稱必須符合格式: ChroLens_Mimic_X.Y.Z.zip")
            return False
        else:
            print_success("檔案名稱格式正確")
        
        # 檢查檔案大小
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print_info(f"檔案大小: {size_mb:.2f} MB")
        
        if size_mb < 10:
            self.warnings.append(f"檔案大小過小 ({size_mb:.2f} MB)，可能缺少檔案")
            print_warning("檔案大小似乎偏小")
        elif size_mb > 100:
            self.warnings.append(f"檔案大小過大 ({size_mb:.2f} MB)，可能包含不必要的檔案")
            print_warning("檔案大小似乎偏大")
        else:
            print_success("檔案大小正常")
        
        # 檢查 Zip 內容
        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                files = zf.namelist()
                print_info(f"包含 {len(files)} 個檔案")
                
                # 檢查必要檔案
                required_files = ['ChroLens_Mimic.exe']
                required_dirs = ['images/', 'docs/']
                
                for req_file in required_files:
                    if req_file in files or any(f.endswith(req_file) for f in files):
                        print_success(f"找到必要檔案: {req_file}")
                    else:
                        self.errors.append(f"缺少必要檔案: {req_file}")
                        print_error(f"缺少必要檔案: {req_file}")
                
                for req_dir in required_dirs:
                    if any(f.startswith(req_dir) for f in files):
                        print_success(f"找到必要目錄: {req_dir}")
                    else:
                        self.warnings.append(f"可能缺少目錄: {req_dir}")
                        print_warning(f"可能缺少目錄: {req_dir}")
                
            print_success("Zip 檔案結構正常")
            return True
            
        except zipfile.BadZipFile:
            self.errors.append("Zip 檔案損壞")
            print_error("Zip 檔案無法開啟或已損壞")
            return False
    
    def check_github_api(self):
        """檢查 GitHub API 可用性和最新版本資訊"""
        print_header("檢查 GitHub Release API")
        
        api_url = "https://api.github.com/repos/Lucienwooo/ChroLens_Mimic/releases/latest"
        print_info(f"API 端點: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 404:
                self.errors.append("GitHub 上沒有任何 Release")
                print_error("GitHub 上沒有任何 Release，請先發布第一個版本")
                return False
            
            response.raise_for_status()
            data = response.json()
            
            # 解析版本
            tag = data.get('tag_name', '')
            version = tag.lstrip('v').lstrip('V')
            print_success(f"最新 Release 標籤: {tag}")
            print_info(f"解析版本: {version}")
            
            # 檢查是否為最新
            if data.get('prerelease'):
                print_warning("這是預發布版本（Pre-release）")
            else:
                print_success("標記為正式版本（Latest release）")
            
            # 檢查資產
            assets = data.get('assets', [])
            print_info(f"包含 {len(assets)} 個資產檔案:")
            
            zip_found = False
            expected_name = f"ChroLens_Mimic_{version}.zip"
            
            for asset in assets:
                name = asset.get('name', '')
                size = asset.get('size', 0) / (1024 * 1024)
                download_url = asset.get('browser_download_url', '')
                
                print(f"  - {name} ({size:.2f} MB)")
                
                if name.endswith('.zip') and 'ChroLens_Mimic' in name:
                    zip_found = True
                    if name == expected_name:
                        print_success(f"    ✓ 檔案名稱完全符合預期: {expected_name}")
                    else:
                        print_warning(f"    ⚠ 檔案名稱不完全符合，預期: {expected_name}")
                        print_info(f"    下載網址: {download_url}")
            
            if zip_found:
                print_success("找到更新包（.zip 檔案）")
            else:
                self.errors.append("GitHub Release 中找不到 .zip 更新包")
                print_error("找不到更新包（.zip 檔案）")
                print_info("請確認已上傳正確命名的 Zip 檔案")
            
            # 檢查版本一致性
            if self.version and version != self.version:
                self.warnings.append(f"GitHub 版本 ({version}) 與本地版本 ({self.version}) 不一致")
                print_warning(f"GitHub 版本與本地版本不一致: {version} vs {self.version}")
            
            return zip_found
            
        except requests.exceptions.RequestException as e:
            self.errors.append(f"無法連接 GitHub API: {str(e)}")
            print_error(f"API 請求失敗: {str(e)}")
            return False
    
    def generate_report(self):
        """產生總結報告"""
        print_header("驗證報告")
        
        if not self.errors and not self.warnings:
            print_success("所有檢查通過！可以發布 ✓")
            return True
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}警告 ({len(self.warnings)} 項):{Colors.ENDC}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if self.errors:
            print(f"\n{Colors.RED}錯誤 ({len(self.errors)} 項):{Colors.ENDC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print(f"\n{Colors.RED}請修復上述錯誤後再發布{Colors.ENDC}")
            return False
        
        if self.warnings and not self.errors:
            print(f"\n{Colors.YELLOW}有警告但沒有錯誤，建議檢查後再發布{Colors.ENDC}")
            return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ChroLens_Mimic 發布驗證工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 檢查版本號一致性
  python validate_release.py --check-version
  
  # 檢查指定的 Zip 檔案
  python validate_release.py --check-zip ChroLens_Mimic_2.7.1.zip
  
  # 檢查 GitHub API
  python validate_release.py --check-api
  
  # 執行完整檢查
  python validate_release.py --full
        """
    )
    
    parser.add_argument('--check-version', action='store_true',
                        help='檢查版本號一致性')
    parser.add_argument('--check-zip', metavar='PATH',
                        help='檢查 Zip 檔案（可指定路徑，或自動尋找）')
    parser.add_argument('--check-api', action='store_true',
                        help='檢查 GitHub Release API')
    parser.add_argument('--full', action='store_true',
                        help='執行完整檢查（所有項目）')
    
    args = parser.parse_args()
    
    # 如果沒有指定任何參數，顯示說明
    if not any([args.check_version, args.check_zip, args.check_api, args.full]):
        parser.print_help()
        return
    
    validator = ReleaseValidator()
    
    # 執行檢查
    if args.full or args.check_version:
        validator.check_version_consistency()
    
    if args.full or args.check_zip is not None:
        zip_path = args.check_zip if isinstance(args.check_zip, str) else None
        validator.check_zip_file(zip_path)
    
    if args.full or args.check_api:
        validator.check_github_api()
    
    # 產生報告
    success = validator.generate_report()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
