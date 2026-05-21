#!/usr/bin/env python3
"""
APK WebView Checker - Command line tool to detect and analyze WebView usage in APK files
Includes VulnLab test cases (11.1-11.9) from OWASP Mobile Top 10
"""

import zipfile
import os
import sys
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field
import tempfile
import shutil


# ============================================================================
# VULNERABILITY DATABASE - VulnLab OWASP Mobile Top 10 Test Cases
# ============================================================================

VULNERABILITY_DATABASE = {
    "11.1": {
        "name": "Component Exposure & Insecure IPC",
        "cvss": 9.1,
        "description": "Exported Activity without proper permissions",
        "test_keywords": ["exported", "activity", "intent-filter", "android:exported"]
    },
    "11.2": {
        "name": "Intent Redirection & PendingIntent Misuse",
        "cvss": 8.3,
        "description": "Intent redirection or PendingIntent vulnerabilities",
        "test_keywords": ["intent-filter", "scheme", "PendingIntent", "redirect"]
    },
    "11.3": {
        "name": "ContentProvider SQL Injection & Path Traversal",
        "cvss": 9.8,
        "description": "SQL injection or path traversal in ContentProvider",
        "test_keywords": ["ContentProvider", "query", "selection", "File"]
    },
    "11.4": {
        "name": "Deep Link Parameter Injection & OAuth Token Hijacking",
        "cvss": 8.1,
        "description": "Deep links accepting untrusted parameters",
        "test_keywords": ["deep-link", "android:scheme", "android:host", "oauth"]
    },
    "11.5": {
        "name": "Broadcast Receiver Hijack",
        "cvss": 7.4,
        "description": "Unprotected BroadcastReceiver allowing hijacking",
        "test_keywords": ["BroadcastReceiver", "intent-filter", "onReceive"]
    },
    "11.6": {
        "name": "Insecure Data Storage",
        "cvss": 7.5,
        "description": "Sensitive data stored without encryption",
        "test_keywords": ["SharedPreferences", "MODE_WORLD_READABLE", "getSharedPreferences"]
    },
    "11.7": {
        "name": "Cryptography Failures",
        "cvss": 7.5,
        "description": "Hardcoded keys, weak algorithms (MD5, ECB), predictable IVs",
        "test_keywords": ["Cipher", "ECB", "MD5", "DES", "hardcoded"]
    },
    "11.8": {
        "name": "Insecure WebView + JS Bridge",
        "cvss": 9.3,
        "description": "WebView with enabled JavaScript bridge (addJavascriptInterface)",
        "test_keywords": ["WebView", "addJavascriptInterface", "setJavaScriptEnabled"]
    },
    "11.9": {
        "name": "Dynamic Code Loading",
        "cvss": 8.8,
        "description": "Dynamic code loading from untrusted sources",
        "test_keywords": ["DexClassLoader", "loadClass", "Plugin", "ClassLoader"]
    }
}


@dataclass
class WebViewFinding:
    """Data class for WebView findings"""
    activity: str
    webview_found: bool
    javascript_enabled: Optional[bool] = None
    file_access: Optional[bool] = None
    dom_storage: Optional[bool] = None
    database_enabled: Optional[bool] = None
    mixed_content_mode: Optional[str] = None
    custom_client: Optional[bool] = None
    details: List[str] = field(default_factory=list)
    vulnerabilities_detected: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.details is None:
            self.details = []


class APKWebViewChecker:
    """Main class for analyzing WebView usage in APK files"""

    def __init__(self, apk_path: str, verbose: bool = False):
        """
        Initialize the checker

        Args:
            apk_path: Path to the APK file
            verbose: Enable verbose output
        """
        self.apk_path = apk_path
        self.verbose = verbose
        self.temp_dir = None
        self.manifest_content = None
        self.dex_files = []
        self.findings: List[WebViewFinding] = []
        self.vulnerabilities: Dict[str, Dict] = {}

    def log(self, message: str, level: str = "INFO"):
        """Log messages"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")

    def extract_apk(self) -> bool:
        """Extract APK file"""
        try:
            if not os.path.exists(self.apk_path):
                self.log(f"APK file not found: {self.apk_path}", "ERROR")
                return False

            self.temp_dir = tempfile.mkdtemp()
            self.log(f"Extracting APK to {self.temp_dir}")

            with zipfile.ZipFile(self.apk_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)

            self.log("APK extracted successfully")
            return True

        except Exception as e:
            self.log(f"Failed to extract APK: {str(e)}", "ERROR")
            return False

    def parse_manifest(self) -> bool:
        """Parse AndroidManifest.xml"""
        try:
            manifest_path = os.path.join(self.temp_dir, "AndroidManifest.xml")

            if not os.path.exists(manifest_path):
                self.log("AndroidManifest.xml not found", "WARNING")
                return False

            with open(manifest_path, 'rb') as f:
                self.manifest_content = f.read()

            self.log("AndroidManifest.xml parsed")
            return True

        except Exception as e:
            self.log(f"Failed to parse manifest: {str(e)}", "ERROR")
            return False

    def find_dex_files(self) -> List[str]:
        """Find all DEX files in APK"""
        dex_files = []
        try:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file.endswith('.dex'):
                        dex_path = os.path.join(root, file)
                        dex_files.append(dex_path)
                        self.log(f"Found DEX file: {file}")

            return dex_files

        except Exception as e:
            self.log(f"Error finding DEX files: {str(e)}", "ERROR")
            return []

    def search_webview_in_dex(self, dex_path: str) -> Dict[str, List[str]]:
        """Search for WebView references in DEX file"""
        findings = {}

        try:
            with open(dex_path, 'rb') as f:
                content = f.read()

            # Search for WebView class references
            webview_patterns = [
                b'android/webkit/WebView',
                b'WebViewClient',
                b'WebChromeClient',
                b'setJavaScriptEnabled',
                b'addJavascriptInterface',
                b'setAllowFileAccess',
                b'setMixedContentMode',
                b'setDomStorageEnabled',
                b'setDatabaseEnabled',
                b'loadUrl',
                b'evaluateJavascript'
            ]

            for pattern in webview_patterns:
                if pattern in content:
                    pattern_name = pattern.decode('latin1')
                    if pattern_name not in findings:
                        findings[pattern_name] = []
                    findings[pattern_name].append(dex_path)

            return findings

        except Exception as e:
            self.log(f"Error searching in DEX: {str(e)}", "ERROR")
            return {}

    def extract_activities_from_manifest(self) -> List[str]:
        """Extract activity names from manifest (binary XML)"""
        activities = []

        try:
            # Simple string search in binary manifest for activity class names
            manifest_str = self.manifest_content.decode('latin1', errors='ignore')

            # Look for activity declarations
            activity_pattern = r'android\.app\.Activity|<activity\s+android:name="([^"]+)"'
            matches = re.findall(activity_pattern, manifest_str, re.IGNORECASE)

            for match in matches:
                if match and match not in activities:
                    activities.append(match)

            return list(set(activities))

        except Exception as e:
            self.log(f"Error extracting activities: {str(e)}", "ERROR")
            return []

    def test_owasp_vulnerabilities(self) -> Dict[str, Dict]:
        """Test for OWASP Mobile Top 10 vulnerabilities from VulnLab"""
        vulnerabilities_found = {}

        try:
            # Read manifest as string
            manifest_str = self.manifest_content.decode('latin1', errors='ignore')

            # Test each vulnerability
            for vuln_id, vuln_info in VULNERABILITY_DATABASE.items():
                detected = False
                keywords_found = []

                # Check for vulnerability keywords
                for keyword in vuln_info.get("test_keywords", []):
                    if keyword.lower() in manifest_str.lower():
                        detected = True
                        keywords_found.append(keyword)

                if detected:
                    vulnerabilities_found[vuln_id] = {
                        'name': vuln_info['name'],
                        'cvss': vuln_info['cvss'],
                        'detected': True,
                        'keywords': keywords_found,
                        'description': vuln_info['description']
                    }
                    self.log(f"[{vuln_id}] DETECTED: {vuln_info['name']} (CVSS: {vuln_info['cvss']})")

            return vulnerabilities_found

        except Exception as e:
            self.log(f"Error testing vulnerabilities: {str(e)}", "ERROR")
            return {}

    def analyze_webview_usage(self) -> List[WebViewFinding]:
        """Analyze WebView usage in the APK"""
        self.findings = []

        # Search in DEX files
        dex_files = self.find_dex_files()
        webview_found = False
        all_findings = {}

        for dex_file in dex_files:
            dex_findings = self.search_webview_in_dex(dex_file)
            for key, value in dex_findings.items():
                if key not in all_findings:
                    all_findings[key] = []
                all_findings[key].extend(value)
                webview_found = True

        # Create main finding
        main_finding = WebViewFinding(
            activity="WebView Usage",
            webview_found=webview_found,
            details=[]
        )

        # Add details about what was found
        for pattern, locations in all_findings.items():
            main_finding.details.append(f"{pattern} - found in {len(locations)} location(s)")

            # Check for security-relevant patterns
            if 'setJavaScriptEnabled' in pattern:
                main_finding.javascript_enabled = True
                main_finding.details.append("  ⚠️  JavaScript is enabled in WebView")

            if 'setAllowFileAccess' in pattern:
                main_finding.file_access = True
                main_finding.details.append("  ⚠️  File access is allowed in WebView")

            if 'addJavascriptInterface' in pattern:
                main_finding.details.append("  ⚠️  JavaScript interface exposed")

            if 'setDomStorageEnabled' in pattern:
                main_finding.dom_storage = True
                main_finding.details.append("  ⚠️  DOM storage is enabled")

            if 'setDatabaseEnabled' in pattern:
                main_finding.database_enabled = True
                main_finding.details.append("  ⚠️  Database is enabled in WebView")

            if 'setMixedContentMode' in pattern:
                main_finding.mixed_content_mode = "DETECTED"
                main_finding.details.append("  ⚠️  Mixed content mode configuration found")

            if 'WebViewClient' in pattern or 'WebChromeClient' in pattern:
                main_finding.custom_client = True
                main_finding.details.append(f"  ℹ️  Custom {pattern.replace('/', '.')} implementation")

        self.findings.append(main_finding)
        return self.findings

    def generate_report(self, output_format: str = "text") -> str:
        """Generate analysis report"""
        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """Generate text report"""
        report = []
        report.append("=" * 70)
        report.append("APK WebView Analysis Report")
        report.append("VulnLab OWASP Mobile Top 10 Test Cases")
        report.append("=" * 70)
        report.append(f"APK Path: {self.apk_path}")
        report.append("")

        # OWASP Vulnerability Test Results
        if self.vulnerabilities:
            report.append("=" * 70)
            report.append("OWASP MOBILE TOP 10 VULNERABILITIES (VulnLab)")
            report.append("=" * 70)
            report.append(f"Vulnerabilities Detected: {len(self.vulnerabilities)}\n")

            # Sort by CVSS score
            sorted_vulns = sorted(self.vulnerabilities.items(), 
                                 key=lambda x: x[1]['cvss'], reverse=True)

            for vuln_id, vuln_info in sorted_vulns:
                severity_icon = "🔴" if vuln_info['cvss'] >= 9.0 else "🔴" if vuln_info['cvss'] >= 7.0 else "🟠"
                report.append(f"[{vuln_id}] {severity_icon} {vuln_info['name']}")
                report.append(f"  CVSS Score: {vuln_info['cvss']}")
                report.append(f"  Description: {vuln_info['description']}")
                if vuln_info.get('keywords'):
                    report.append(f"  Keywords Found: {', '.join(vuln_info['keywords'])}")
                report.append("")

        if not self.findings:
            report.append("No WebView usage detected in this APK")
        else:
            report.append("=" * 70)
            report.append("WEBVIEW ANALYSIS")
            report.append("=" * 70 + "\n")

            for finding in self.findings:
                report.append(f"Component: {finding.activity}")
                report.append(f"WebView Found: {'✓ YES' if finding.webview_found else '✗ NO'}")

                if finding.javascript_enabled is not None:
                    report.append(
                        f"JavaScript Enabled: {'✓ YES (SECURITY RISK)' if finding.javascript_enabled else '✗ NO'}"
                    )

                if finding.file_access is not None:
                    report.append(
                        f"File Access: {'✓ YES (SECURITY RISK)' if finding.file_access else '✗ NO'}"
                    )

                if finding.dom_storage is not None:
                    report.append(
                        f"DOM Storage: {'✓ YES' if finding.dom_storage else '✗ NO'}"
                    )

                if finding.database_enabled is not None:
                    report.append(
                        f"Database Enabled: {'✓ YES' if finding.database_enabled else '✗ NO'}"
                    )

                if finding.mixed_content_mode:
                    report.append(f"Mixed Content Mode: {finding.mixed_content_mode}")

                if finding.custom_client is not None:
                    report.append(
                        f"Custom WebView Client: {'✓ YES' if finding.custom_client else '✗ NO'}"
                    )

                if finding.details:
                    report.append("\nDetailed Findings:")
                    for detail in finding.details:
                        report.append(f"  {detail}")

                report.append("")

        report.append("=" * 70)
        report.append("Security Recommendations:")
        report.append("=" * 70)
        report.append("1. Disable JavaScript if not required: setJavaScriptEnabled(false)")
        report.append("2. Disable file access: setAllowFileAccess(false)")
        report.append("3. Be cautious with addJavascriptInterface() - potential XSS vector")
        report.append("4. Validate and sanitize all URLs loaded in WebView")
        report.append("5. Use HTTPS only for remote content")
        report.append("6. Implement proper certificate pinning")
        report.append("7. For OWASP vulnerabilities 11.1-11.9, see VulnLab documentation")
        report.append("   GitHub: https://github.com/anpa1200/Vulnerable-APK")
        report.append("=" * 70)

        return "\n".join(report)

    def _generate_json_report(self) -> str:
        """Generate JSON report"""
        report = {
            "apk_path": self.apk_path,
            "findings": [asdict(finding) for finding in self.findings],
            "vulnerabilities": self.vulnerabilities,
            "vulnerability_count": len(self.vulnerabilities)
        }
        return json.dumps(report, indent=2)

    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.log("Temporary files cleaned up")
            except Exception as e:
                self.log(f"Failed to clean up temp files: {str(e)}", "WARNING")

    def check(self) -> bool:
        """Run complete check"""
        try:
            if not self.extract_apk():
                return False

            if not self.parse_manifest():
                return False

            self.analyze_webview_usage()
            self.vulnerabilities = self.test_owasp_vulnerabilities()
            return True

        except Exception as e:
            self.log(f"Check failed: {str(e)}", "ERROR")
            return False

        finally:
            self.cleanup()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Check WebView usage and security issues in APK files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python check_webview.py app.apk
  python check_webview.py app.apk --json
  python check_webview.py app.apk -v
  python check_webview.py app.apk --output report.json
        '''
    )

    parser.add_argument('apk', help='Path to APK file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-j', '--json', action='store_true', help='Output in JSON format')
    parser.add_argument('-o', '--output', help='Save report to file')

    args = parser.parse_args()

    # Validate APK file
    if not os.path.exists(args.apk):
        print(f"Error: APK file not found: {args.apk}")
        sys.exit(1)

    if not args.apk.lower().endswith('.apk'):
        print("Warning: File does not have .apk extension")

    # Run checker
    checker = APKWebViewChecker(args.apk, verbose=args.verbose)

    print(f"Analyzing {args.apk}...")

    if not checker.check():
        print("Analysis failed")
        sys.exit(1)

    # Generate report
    output_format = "json" if args.json else "text"
    report = checker.generate_report(output_format)

    # Output report
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            sys.exit(1)
    else:
        print(report)

    sys.exit(0)


if __name__ == '__main__':
    main()
