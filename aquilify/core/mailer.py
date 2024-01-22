import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import ssl
import sys
import logging
from typing import List

from aquilify.settings import settings

class Mailer:
    def __init__(self, config_name=None):
        """
        Initialize the Mailer.

        Args:
            config_name (str, optional): The name of the email configuration.

        Usage:
            mailer = Mailer(config_name='config_name')
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        try:
            self.configurations = settings.BASE_MAILER
            if config_name:
                self.config = next((config for config in self.configurations if config['NAME'] == config_name), None)
                if not self.config:
                    self.logger.error(f"Configuration '{config_name}' not found.")
                    sys.exit(1)
            else:
                self.config = self.configurations[0]
        except ImportError:
            self.logger.error("No settings.py found.")
            sys.exit(1)

    def _send_email(self, message, timeout=None):
        context = ssl.create_default_context() if self.config['SSL'] else None
        
        try:
            with smtplib.SMTP(self.config['SMTP'], self.config['PORT'], timeout=timeout) as server:
                if self.config['SSL']:
                    server.starttls(context=context)
                server.login(self.config['USERNAME'], self.config['PASSWORD'])
                server.sendmail(message['From'], message['To'], message.as_string())
            return True
        except Exception as e:
            self.logger.error("Error sending email:", exc_info=True)
            return False

    def send_email(self, to_email, subject, body=None, html_body=None, from_email=None, cc=None, bcc=None,
                   reply_to=None, attachments=None, inline_images=None, headers=None, charset='utf-8', timeout=None):
        """
        Send an email.

        Args:
            to_email (str): The recipient's email address.
            subject (str): The email subject.
            body (str, optional): The plain text email body.
            html_body (str, optional): The HTML email body.
            from_email (str, optional): The sender's email address.
            cc (str, optional): The CC email addresses.
            bcc (str, optional): The BCC email addresses.
            reply_to (str, optional): The reply-to email address.
            attachments (List[str], optional): List of file paths for email attachments.
            inline_images (List[str], optional): List of file paths for inline images.
            headers (dict, optional): Additional email headers.
            charset (str, optional): The character encoding.
            timeout (int, optional): Timeout for sending the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.

        Usage:
            success = mailer.send_email(
                to_email='recipient@example.com',
                subject='Test Email',
                body='This is a test email.',
                from_email='sender@example.com',
                cc='cc@example.com',
                bcc='bcc@example.com',
                reply_to='reply@example.com',
                attachments=['file1.txt', 'file2.pdf'],
                inline_images=['image1.png', 'image2.jpg'],
                headers={'X-Custom-Header': 'Custom Value'},
                charset='utf-8',
                timeout=30
            )
        """
        if not body and not html_body:
            self.logger.error("Both 'body' and 'html_body' cannot be None.")
            return

        if not from_email:
            from_email = self.config['DEFAULT_SENDER']

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc
        if reply_to:
            msg.add_header('reply-to', reply_to)

        if headers:
            for key, value in headers.items():
                msg.add_header(key, value)

        if html_body:
            msg.attach(MIMEText(html_body, 'html', charset))
        elif body:
            msg.attach(MIMEText(body, 'plain', charset))

        if attachments:
            for attachment in attachments:
                with open(attachment, 'rb') as file:
                    part = MIMEApplication(file.read(), Name=attachment)
                    part['Content-Disposition'] = f'attachment; filename="{attachment}"'
                    msg.attach(part)

        if inline_images:
            for inline_image in inline_images:
                with open(inline_image, 'rb') as file:
                    img = MIMEImage(file.read(), name=inline_image)
                    img.add_header('Content-ID', f'<{inline_image}>')
                    img.add_header('Content-Disposition', 'inline', filename=inline_image)
                    msg.attach(img)

        return self._send_email(msg, timeout=timeout)

    def send_bulk_email(self, to_emails: List[str], subject, body=None, html_body=None, from_email=None,
                        cc=None, bcc=None, reply_to=None, attachments=None, inline_images=None,
                        headers=None, charset='utf-8', timeout=None):
        """
        Send bulk email to multiple recipients.

        Args:
            to_emails (List[str]): List of recipient email addresses.
            subject (str): The email subject.
            body (str, optional): The plain text email body.
            html_body (str, optional): The HTML email body.
            from_email (str, optional): The sender's email address.
            cc (str, optional): The CC email addresses.
            bcc (str, optional): The BCC email addresses.
            reply_to (str, optional): The reply-to email address.
            attachments (List[str], optional): List of file paths for email attachments.
            inline_images (List[str], optional): List of file paths for inline images.
            headers (dict, optional): Additional email headers.
            charset (str, optional): The character encoding.
            timeout (int, optional): Timeout for sending the email.

        Returns:
            int: The number of successful email sends.

        Usage:
            success_count = mailer.send_bulk_email(
                to_emails=['recipient1@example.com', 'recipient2@example.com'],
                subject='Bulk Test Email',
                body='This is a bulk test email.',
                from_email='sender@example.com',
                attachments=['file1.txt', 'file2.pdf'],
                charset='utf-8',
                timeout=30
            )
        """
        success_count = 0
        for to_email in to_emails:
            if self.send_email(to_email, subject, body, html_body, from_email, cc, bcc, reply_to,
                               attachments, inline_images, headers, charset, timeout):
                success_count += 1
        return success_count

    def send_email_timeout(self, to_email, subject, body=None, html_body=None, from_email=None, cc=None, bcc=None,
                          reply_to=None, attachments=None, inline_images=None, headers=None, charset='utf-8',
                          timeout=30):
        """
        Send an email with a specified timeout.

        Args:
            to_email (str): The recipient's email address.
            subject (str): The email subject.
            body (str, optional): The plain text email body.
            html_body (str, optional): The HTML email body.
            from_email (str, optional): The sender's email address.
            cc (str, optional): The CC email addresses.
            bcc (str, optional): The BCC email addresses.
            reply_to (str, optional): The reply-to email address.
            attachments (List[str], optional): List of file paths for email attachments.
            inline_images (List[str], optional): List of file paths for inline images.
            headers (dict, optional): Additional email headers.
            charset (str, optional): The character encoding.
            timeout (int, optional): Timeout for sending the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.

        Usage:
            success = mailer.send_email_timeout(
                to_email='recipient@example.com',
                subject='Test Email',
                body='This is a test email.',
                from_email='sender@example.com',
                attachments=['file1.txt', 'file2.pdf'],
                charset='utf-8',
                timeout=30
            )
        """
        return self.send_email(to_email, subject, body, html_body, from_email, cc, bcc, reply_to, attachments,
                               inline_images, headers, charset, timeout)

    def send_template_email(self, to_email, subject, template_path, context=None, from_email=None, cc=None,
                            bcc=None, reply_to=None, attachments=None, inline_images=None, headers=None,
                            charset='utf-8', timeout=None):
        """
        Send an email using an HTML template.

        Args:
            to_email (str): The recipient's email address.
            subject (str): The email subject.
            template_path (str): The path to the HTML email template.
            context (dict, optional): The context for template rendering.
            from_email (str, optional): The sender's email address.
            cc (str, optional): The CC email addresses.
            bcc (str, optional): The BCC email addresses.
            reply_to (str, optional): The reply-to email address.
            attachments (List[str], optional): List of file paths for email attachments.
            inline_images (List[str], optional): List of file paths for inline images.
            headers (dict, optional): Additional email headers.
            charset (str, optional): The character encoding.
            timeout (int, optional): Timeout for sending the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.

        Usage:
            success = mailer.send_template_email(
                to_email='recipient@example.com',
                subject='Template Email',
                template_path='template.html',
                context={'name': 'John Doe'},
                from_email='sender@example.com',
                attachments=['file1.txt', 'file2.pdf'],
                charset='utf-8',
                timeout=30
            )
        """
        if not context:
            context = {}

        with open(template_path, 'r') as template_file:
            template = template_file.read()

        html_body = template.format(**context)
        return self.send_email(to_email, subject, html_body=html_body, from_email=from_email, cc=cc, bcc=bcc,
                               reply_to=reply_to, attachments=attachments, inline_images=inline_images,
                               headers=headers, charset=charset, timeout=timeout)
