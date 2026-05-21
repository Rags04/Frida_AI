#!/usr/bin/env python3
"""
Example Usage: APK WebView Checker with Frida Integration

This script demonstrates how to use the WebView checker tools
alongside your existing Frida automation framework.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path


class FridaWebViewWorkflow:
    """Workflow for analyzing WebView and applying Frida hooks"""

    def __init__(self, apk_path: str, package_name: str = None):
        """
        Initialize workflow

        Args:
            apk_path: Path to APK file
            package_name: Android package name (optional)
        """
        self.apk_path = apk_path
        self.package_name = package_name
        self.script_dir = os.path.dirname(__file__)
        self.webview_report = None

    def run_webview_check(self, advanced: bool = False) -> bool:
        """Run WebView checker"""
        print("[*] Running WebView analysis...")

        script = "check_webview_advanced.py" if advanced else "check_webview.py"
        script_path = os.path.join(self.script_dir, script)

        if not os.path.exists(script_path):
            print(f"[!] Script not found: {script_path}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, script_path, self.apk_path, "--json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.webview_report = json.loads(result.stdout)
                print("[+] WebView analysis completed")
                return True
            else:
                print(f"[!] Analysis failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"[!] Error running analysis: {str(e)}")
            return False

    def check_webview_vulnerabilities(self) -> dict:
        """Check for WebView vulnerabilities"""
        if not self.webview_report:
            return {}

        findings = self.webview_report.get('findings', [])
        if not findings:
            findings = [self.webview_report]

        vulnerabilities = {
            'javascript_enabled': False,
            'file_access': False,
            'javascript_interface': False,
            'dom_storage': False,
            'database_enabled': False,
        }

        for finding in findings:
            if finding.get('details'):
                details_str = ' '.join(finding['details'])

                if 'setJavaScriptEnabled' in details_str:
                    vulnerabilities['javascript_enabled'] = True

                if 'setAllowFileAccess' in details_str or 'file_access' in details_str:
                    vulnerabilities['file_access'] = True

                if 'addJavascriptInterface' in details_str:
                    vulnerabilities['javascript_interface'] = True

                if 'setDomStorageEnabled' in details_str:
                    vulnerabilities['dom_storage'] = True

                if 'setDatabaseEnabled' in details_str:
                    vulnerabilities['database_enabled'] = True

        return vulnerabilities

    def print_report(self):
        """Print WebView analysis report"""
        if not self.webview_report:
            print("[!] No report available")
            return

        print("\n" + "=" * 70)
        print("WebView Analysis Report")
        print("=" * 70)

        # Print basic info
        if 'findings' in self.webview_report:
            findings = self.webview_report['findings']
            if findings:
                finding = findings[0]
                print(f"\nWebView Found: {finding.get('webview_found', False)}")

                if finding.get('details'):
                    print("\nFindings:")
                    for detail in finding['details']:
                        print(f"  • {detail}")

        print("\n" + "=" * 70)

    def suggest_frida_hooks(self) -> list:
        """Suggest Frida hooks based on findings"""
        vulnerabilities = self.check_webview_vulnerabilities()
        hooks = []

        print("\n[*] Suggested Frida hooks for testing:")
        print("=" * 70)

        if vulnerabilities['javascript_enabled']:
            hooks.append({
                'name': 'Bypass WebView JavaScript Restrictions',
                'description': 'Hook setJavaScriptEnabled to log/bypass',
                'example': '''
// Hook JavaScript enabled check
Java.perform(function() {
    var webSettings = Java.use("android.webkit.WebSettings");
    webSettings.setJavaScriptEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] setJavaScriptEnabled called with: " + enabled);
        return this.setJavaScriptEnabled(true); // Force enable
    };
});
                '''
            })

        if vulnerabilities['file_access']:
            hooks.append({
                'name': 'Monitor File Access in WebView',
                'description': 'Hook setAllowFileAccess to monitor',
                'example': '''
// Monitor file access attempts
Java.perform(function() {
    var webSettings = Java.use("android.webkit.WebSettings");
    webSettings.setAllowFileAccess.overload('boolean').implementation = function(allow) {
        console.log("[!] File access requested: " + allow);
        send({"type": "file_access", "allowed": allow});
        return this.setAllowFileAccess(true);
    };
});
                '''
            })

        if vulnerabilities['javascript_interface']:
            hooks.append({
                'name': 'Intercept JavaScript Interface',
                'description': 'Hook addJavascriptInterface to log calls',
                'example': '''
// Log JavaScript interface calls
Java.perform(function() {
    var webView = Java.use("android.webkit.WebView");
    webView.addJavascriptInterface.implementation = function(obj, interfaceName) {
        console.log("[!] JavaScript interface added: " + interfaceName);
        console.log("[!] Object type: " + obj.getClass().getName());
        return this.addJavascriptInterface(obj, interfaceName);
    };
});
                '''
            })

        if vulnerabilities['dom_storage']:
            hooks.append({
                'name': 'Monitor DOM Storage',
                'description': 'Hook DOM storage operations',
                'example': '''
// Monitor DOM storage
Java.perform(function() {
    var webSettings = Java.use("android.webkit.WebSettings");
    webSettings.setDomStorageEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] DOM storage: " + enabled);
        return this.setDomStorageEnabled(true);
    };
});
                '''
            })

        if vulnerabilities['database_enabled']:
            hooks.append({
                'name': 'Monitor WebView Database',
                'description': 'Hook database access',
                'example': '''
// Monitor database access
Java.perform(function() {
    var webSettings = Java.use("android.webkit.WebSettings");
    webSettings.setDatabaseEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] Database enabled: " + enabled);
        return this.setDatabaseEnabled(true);
    };
});
                '''
            })

        for i, hook in enumerate(hooks, 1):
            print(f"\n[{i}] {hook['name']}")
            print(f"    Description: {hook['description']}")
            print(f"    Code:\n{hook['example']}")

        print("=" * 70)
        return hooks

    def create_frida_script(self, output_file: str = "webview_hooks.js"):
        """Create a Frida script with all suggested hooks"""
        vulnerabilities = self.check_webview_vulnerabilities()

        script = '''// Auto-generated Frida hooks for WebView analysis
// Generated by APK WebView Checker

console.log("[*] WebView Frida hooks loaded");

Java.perform(function() {
    var WebView = Java.use("android.webkit.WebView");
    var WebSettings = Java.use("android.webkit.WebSettings");

'''

        if vulnerabilities['javascript_enabled']:
            script += '''
    // Hook: setJavaScriptEnabled
    WebSettings.setJavaScriptEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] WebSettings.setJavaScriptEnabled() called with: " + enabled);
        return this.setJavaScriptEnabled(enabled);
    };

'''

        if vulnerabilities['file_access']:
            script += '''
    // Hook: setAllowFileAccess
    WebSettings.setAllowFileAccess.overload('boolean').implementation = function(allow) {
        console.log("[!] WebSettings.setAllowFileAccess() called with: " + allow);
        return this.setAllowFileAccess(allow);
    };

'''

        if vulnerabilities['javascript_interface']:
            script += '''
    // Hook: addJavascriptInterface
    WebView.addJavascriptInterface.implementation = function(obj, name) {
        console.log("[!] WebView.addJavascriptInterface() - Interface name: " + name);
        console.log("[!] Object class: " + obj.getClass().getName());
        return this.addJavascriptInterface(obj, name);
    };

'''

        if vulnerabilities['dom_storage']:
            script += '''
    // Hook: setDomStorageEnabled
    WebSettings.setDomStorageEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] WebSettings.setDomStorageEnabled() called with: " + enabled);
        return this.setDomStorageEnabled(enabled);
    };

'''

        if vulnerabilities['database_enabled']:
            script += '''
    // Hook: setDatabaseEnabled
    WebSettings.setDatabaseEnabled.overload('boolean').implementation = function(enabled) {
        console.log("[*] WebSettings.setDatabaseEnabled() called with: " + enabled);
        return this.setDatabaseEnabled(enabled);
    };

'''

        script += '''
    console.log("[+] WebView hooks initialized successfully");
});
'''

        try:
            with open(output_file, 'w') as f:
                f.write(script)
            print(f"\n[+] Frida script saved to: {output_file}")
            return True
        except Exception as e:
            print(f"[!] Failed to save script: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='WebView Analysis Workflow with Frida Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python example_workflow.py app.apk
  python example_workflow.py app.apk --advanced
  python example_workflow.py app.apk --generate-hooks webview.js
        '''
    )

    parser.add_argument('apk', help='APK file to analyze')
    parser.add_argument('-p', '--package', help='Package name (optional)')
    parser.add_argument('-a', '--advanced', action='store_true',
                       help='Use advanced analysis')
    parser.add_argument('-g', '--generate-hooks', metavar='FILE',
                       help='Generate Frida hooks script')

    args = parser.parse_args()

    # Validate APK
    if not os.path.exists(args.apk):
        print(f"[!] APK not found: {args.apk}")
        sys.exit(1)

    # Initialize workflow
    workflow = FridaWebViewWorkflow(args.apk, args.package)

    # Run analysis
    if not workflow.run_webview_check(advanced=args.advanced):
        print("[!] WebView check failed")
        sys.exit(1)

    # Print report
    workflow.print_report()

    # Check vulnerabilities
    vulns = workflow.check_webview_vulnerabilities()
    print("\nVulnerability Summary:")
    print("-" * 70)
    for vuln, found in vulns.items():
        status = "FOUND" if found else "NOT FOUND"
        symbol = "🔴" if found else "✓"
        print(f"{symbol} {vuln}: {status}")

    # Suggest hooks
    workflow.suggest_frida_hooks()

    # Generate hooks if requested
    if args.generate_hooks:
        workflow.create_frida_script(args.generate_hooks)

    print("\n[+] Analysis complete!")


if __name__ == '__main__':
    main()
