
# Aquilify devops / Test _CSP @noql :: 3217

import json
import logging
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Union, List, Optional

from ..wrappers import Request, Response
from ..exception.__handler import handle_exception

class CSPMiddleware:
    def __init__(
        self,
        csp_directives: Dict[str, Union[str, List[str]]],
        report_uri: str = '',
        report_only: bool = False,
        enable_violation_handling: bool = False,
        report_sample_weight: float = 0.0,
        violation_report_endpoint: str = '/violation-report',
        log_file_path: str = 'csp_violation_reports.log',
        security_headers: Dict[str, str] = None,
        nonce_length: int = 16,
        nonce_algorithm: str = 'sha256',
        referrer_policy: str = 'strict-origin-when-cross-origin',
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        feature_policy: Optional[Dict[str, str]] = None,
        x_content_type_options: str = 'nosniff',
        x_frame_options: str = 'DENY',
        x_xss_protection: str = '1; mode=block',
        expect_ct: Optional[str] = None,
        cross_origin_opener_policy: Optional[str] = None,
        cross_origin_embedder_policy: Optional[str] = None,
        force_https: bool = False,
        referrer_policy_feature: bool = False,
        referrer_policy_no_referer: bool = False,
        referrer_policy_no_referrer_when_downgrade: bool = False,
    ) -> None:
        self.csp_directives = csp_directives
        self.report_uri = report_uri
        self.report_only = report_only
        self.enable_violation_handling = enable_violation_handling
        self.report_sample_weight = report_sample_weight
        self.violation_report_endpoint = violation_report_endpoint
        self.log_file_path = Path(log_file_path)
        self.security_headers = security_headers or {}
        self._setup_violation_log_file()
        self.logger = self._setup_logging()
        self.violation_reports = [],
        self.nonce_length: int = nonce_length
        self.nonce_algorithm: str = nonce_algorithm
        self.referrer_policy: str = referrer_policy
        self.hsts_max_age: int = hsts_max_age
        self.hsts_include_subdomains: bool = hsts_include_subdomains
        self.hsts_preload: bool = hsts_preload
        self.feature_policy: Dict[str, str] = feature_policy if feature_policy else {}
        self.x_content_type_options: str = x_content_type_options
        self.x_frame_options: str = x_frame_options
        self.x_xss_protection: str = x_xss_protection
        self.expect_ct: Optional[str] = expect_ct
        self.cross_origin_opener_policy: Optional[str] = cross_origin_opener_policy
        self.cross_origin_embedder_policy: Optional[str] = cross_origin_embedder_policy
        self.force_https: bool = force_https
        self.referrer_policy_feature: bool = referrer_policy_feature
        self.referrer_policy_no_referer: bool = referrer_policy_no_referer
        self.referrer_policy_no_referrer_when_downgrade: bool = referrer_policy_no_referrer_when_downgrade

    async def __call__(self, request: Request, response: Response) -> Response:
        try:
            if self.force_https and await request.scheme() != "https":
                    response.status_code = 400
                    response.content = "<h1>400 | Bad Request - HTTPS Required!</h1>"
                    response.content_type = 'text/html'
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

            if self.referrer_policy_feature:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "features"

            if self.referrer_policy_no_referer:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "no-referer"

            if self.referrer_policy_no_referrer_when_downgrade:
                response.headers["Referrer-Policy"] = self.referrer_policy + ", " + "no-referrer-when-downgrade"

            response.headers["Referrer-Policy"] = self.referrer_policy
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
