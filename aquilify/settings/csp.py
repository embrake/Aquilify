import importlib.util

class CSPConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_csp_config(self):
        try:
            settings = self._load_settings_module()

            csp_directives = getattr(settings, "CSP_DIRECTIVES", { 'default-src': ["'self'"] })
            report_uri = getattr(settings, "CSP_REPORT_URI", '')
            report_only = getattr(settings, "CSP_REPORT_ONLY", False)
            enable_violation_handling = getattr(settings, "CSP_ENABLE_VIOLATION_HANDLING", False)
            report_sample_weight = getattr(settings, "CSP_REPORT_SAMPLE_WEIGHT", 0.0)
            violation_report_endpoint = getattr(settings, "CSP_VIOLATION_REPORT_ENDPOINT", '/violation-report')
            log_file_path = getattr(settings, "CSP_LOG_FILE_PATH", 'csp_report.log')
            security_headers = getattr(settings, "CSP_SECURITY_HEADERS", None)
            nonce_length = getattr(settings, "CSP_NONCE_LENGTH", 16)
            nonce_algorithm = getattr(settings, "CSP_NONCE_ALGORITHM", 'sha256')
            referrer_policy = getattr(settings, "CSP_REFERRER_POLICY", 'strict-origin-when-cross-origin')
            hsts_max_age = getattr(settings, "CSP_HSTS_MAX_AGE", 31536000)
            hsts_include_subdomains = getattr(settings, "CSP_HSTS_INCLUDE_SUBDOMAINS", True)
            hsts_preload = getattr(settings, "CSP_HSTS_PRELOAD", False)
            feature_policy = getattr(settings, "CSP_FEATURE_POLICY", None)
            x_content_type_options = getattr(settings, "CSP_X_CONTENT_TYPE_OPTIONS", 'nosniff')
            x_frame_options = getattr(settings, "CSP_X_FRAME_OPTIONS", 'SAMEORIGIN')
            x_xss_protection = getattr(settings, "CSP_X_XSS_PROTECTION", '1; mode=block')
            expect_ct = getattr(settings, "CSP_EXPECT_CT", None)
            cross_origin_opener_policy = getattr(settings, "CSP_CROSS_ORIGIN_OPENER_POLICY", None)
            cross_origin_embedder_policy = getattr(settings, "CSP_CROSS_ORIGIN_EMBEDDER_POLICY", None)
            force_https = getattr(settings, "CSP_FORCE_HTTPS", False)
            referrer_policy_feature = getattr(settings, "CSP_REFERRER_POLICY_FEATURE", False)
            referrer_policy_no_referer = getattr(settings, "CSP_REFERRER_POLICY_NO_REFERER", False)
            referrer_policy_no_referrer_when_downgrade = getattr(settings, "CSP_REFERRER_POLICY_NO_REFERRER_WHEN_DOWNGRADE", False)

            csp_settings = {
                "csp_directives": csp_directives,
                "report_uri": report_uri,
                "report_only": report_only,
                "enable_violation_handling": enable_violation_handling,
                "report_sample_weight": report_sample_weight,
                "violation_report_endpoint": violation_report_endpoint,
                "log_file_path": log_file_path,
                "security_headers": security_headers,
                "nonce_length": nonce_length,
                "nonce_algorithm": nonce_algorithm,
                "referrer_policy": referrer_policy,
                "hsts_max_age": hsts_max_age,
                "hsts_include_subdomains": hsts_include_subdomains,
                "hsts_preload": hsts_preload,
                "feature_policy": feature_policy,
                "x_content_type_options": x_content_type_options,
                "x_frame_options": x_frame_options,
                "x_xss_protection": x_xss_protection,
                "expect_ct": expect_ct,
                "cross_origin_opener_policy": cross_origin_opener_policy,
                "cross_origin_embedder_policy": cross_origin_embedder_policy,
                "force_https": force_https,
                "referrer_policy_feature": referrer_policy_feature,
                "referrer_policy_no_referer": referrer_policy_no_referer,
                "referrer_policy_no_referrer_when_downgrade": referrer_policy_no_referrer_when_downgrade
            }
            return csp_settings

        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings
    
    def fetch(self):
        data = self._fetch_csp_config()
        return data

