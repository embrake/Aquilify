import json
import logging
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Union, List, Optional

from ..wrappers import Request, Response
from ..exception.__handler import handle_exception
from ..responses import HTMLResponse
from ..settings.csp import CSPConfigSettings

_settings = CSPConfigSettings().fetch()

class CSPMiddleware:
    def __init__(
        self
    ) -> None:
        self.csp_directives = _settings.get('csp_directives') or { 'default-src': ["'self'"] }
        self.report_uri = _settings.get('report_uri') or ''
        self.report_only = _settings.get('report_only') or False
        self.enable_violation_handling = _settings.get('enable_violation_handling') or False
        self.report_sample_weight = _settings.get('report_sample_weight') or 0.0
        self.violation_report_endpoint = _settings.get('violation_report_endpoint') or '/violation-report'
        self.log_file_path = Path(_settings.get('log_file_path')) or Path('csp_violation_reports.log')
        self.security_headers = _settings.get('security_headers') or {}
        self._setup_violation_log_file()
        self.logger = self._setup_logging()
        self.violation_reports = [],
        self.nonce_length: int = _settings.get('nonce_length') or 16
        self.nonce_algorithm: str = _settings.get('nonce_algorithm') or 'sha256'
        self.referrer_policy: str = _settings.get("referrer_policy") or 'strict-origin-when-cross-origin'
        self.hsts_max_age: int = _settings.get('hsts_max_age') or 31536000
        self.hsts_include_subdomains: bool = _settings.get('hsts_include_subdomains') or True
        self.hsts_preload: bool = _settings.get('hsts_preload') or False
        self.feature_policy: Dict[str, str] = _settings.get('feature_policy') or {}
        self.x_content_type_options: str = _settings.get('x_content_type_options') or 'nosniff'
        self.x_frame_options: str = _settings.get('x_frame_options') or 'DENY'
        self.x_xss_protection: str = _settings.get('x_xss_protection') or '1; mode=block'
        self.expect_ct: Optional[str] = _settings.get('expect_ct') or None
        self.cross_origin_opener_policy: Optional[str] = _settings.get('cross_origin_opener_policy') or None
        self.cross_origin_embedder_policy: Optional[str] = _settings.get('cross_origin_embedder_policy') or None
        self.force_https: bool = _settings.get('force_https') or False
        self.referrer_policy_feature: bool = _settings.get('referrer_policy_feature') or False
        self.referrer_policy_no_referer: bool = _settings.get('referrer_policy_no_referer') or False
        self.referrer_policy_no_referrer_when_downgrade: bool = _settings.get('referrer_policy_no_referrer_when_downgrade') or False

    async def __call__(self, request: Request, response: Response) -> Response:
        try:
            if self.force_https and request.scheme != "https":
                    response = HTMLResponse('<h1>Bad Request | HTTPS Connection Required | 400</h1>', status=400)
                    return response
            
            if self._is_violation_report_request(request):
                await self._handle_violation_reports(request)
                return Response(content='Violation report received and logged.', status_code=200)
            response = self._set_csp_header(response)
            response = self._set_additional_security_headers(response)

            if self.expect_ct:
                response['headers']["Expect-CT"] = self.expect_ct

            if self.cross_origin_opener_policy:
                response['headers']["Cross-Origin-Opener-Policy"] = self.cross_origin_opener_policy

            if self.cross_origin_embedder_policy:
                response['headers']["Cross-Origin-Embedder-Policy"] = self.cross_origin_embedder_policy

            response.headers["Referrer-Policy"] = self.referrer_policy

            if self.referrer_policy_feature:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "features"

            if self.referrer_policy_no_referer:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "no-referer"

            if self.referrer_policy_no_referrer_when_downgrade:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "no-referrer-when-downgrade"
                
            hsts_directive = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_directive += "; includeSubDomains"
            if self.hsts_preload:
                hsts_directive += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_directive

            if self.feature_policy:
                feature_policy_directives = " ".join([f"{key} {value}" for key, value in self.feature_policy.items()])
                response.headers["Feature-Policy"] = feature_policy_directives

            response.headers["X-Content-Type-Options"] = self.x_content_type_options
            response.headers["X-Frame-Options"] = self.x_frame_options
            response.headers["X-XSS-Protection"] = self.x_xss_protection
            return response
        except Exception as e:
            await handle_exception(e)
        return response

    def _is_violation_report_request(self, request: Request) -> bool:
        return request.scope['path'] == self.violation_report_endpoint and request.method == 'POST'

    def _set_csp_header(self, response: Response) -> Response:
        csp_header_value = self._generate_csp_header()
        response.headers['Content-Security-Policy' if not self.report_only else 'Content-Security-Policy-Report-Only'] = csp_header_value
        if self.report_uri:
            response.headers['Content-Security-Policy-Report-Only'] = f"{csp_header_value}; report-uri {self.report_uri}"
        return response

    def _generate_csp_header(self) -> str:
        csp_directive_strings = [f"{directive} {self._generate_directive_value(directive)}" for directive in self.csp_directives.keys()]
        return "; ".join(csp_directive_strings)

    def _generate_directive_value(self, directive: str) -> str:
        value = self.csp_directives[directive]
        return self._join_values(self._generate_nonce_for_inline(value) if self._is_inline_directive(directive) else value)

    def _generate_nonce_for_inline(self, directives: Union[str, List[str]]) -> Union[str, List[str]]:
        return [self._generate_nonce() if "'nonce'" in directive else directive for directive in directives] if isinstance(directives, list) else self._generate_nonce() if "'nonce'" in directives else directives

    def _generate_nonce(self) -> str:
        nonce = secrets.token_urlsafe(self.nonce_length)
        if self.nonce_algorithm:
            hash_func = getattr(hashlib, self.nonce_algorithm, hashlib.sha256)
            hashed_nonce = hash_func(nonce.encode()).digest()
            return hashed_nonce.hex()
        return nonce

    def _is_inline_directive(self, directive: str) -> bool:
        return directive in ['script-src', 'style-src']

    def _join_values(self, value: Union[str, List[str]]) -> str:
        return " ".join(value) if isinstance(value, list) else value

    def _setup_violation_log_file(self) -> None:
        if not self.log_file_path.is_file():
            self.log_file_path.touch()

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('CSPViolationLogger')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _handle_violation_reports(self, request: Request) -> None:
        violation_report = await request.json()
        self._store_violation_report(violation_report)
        self.logger.info(json.dumps(violation_report))
        self.violation_reports.append(violation_report)
        if self.enable_violation_handling:
            self._process_violation_reports()

    def _store_violation_report(self, violation_report: dict) -> None:
        with self.log_file_path.open(mode='a') as file:
            file.write(json.dumps(violation_report) + '\n')

    def _process_violation_reports(self) -> None:
        num_reports = len(self.violation_reports)
        if num_reports > 0:
            weighted_reports = int(self.report_sample_weight * num_reports)
            reports_to_process = self.violation_reports[:weighted_reports]

    def _set_additional_security_headers(self, response: Response) -> Response:
        for header, value in self.security_headers.items():
            response.headers[header] = value
        return response
