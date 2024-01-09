"""
Module for testing CRUD (Create, Read, Update, Delete) operations via an API
using AQUILIFY's ClientSession module.

This script simulates HTTP requests to specified API routes and endpoints to test
the CRUD functionality. Users can customize payloads and test scenarios as needed.

Classes:
- RequestSender: Handles sending HTTP requests for CRUD operations.

Methods:
- create_payload: Generates payloads based on the provided endpoint path.
- send_request: Sends a POST request to a specific API route and endpoint with a generated payload.
- send_requests: Iterates through routes and endpoints, sending requests accordingly.

Usage:
1. Customize payload data in the create_payload method as required.
2. Set the AQUILIFY_SETTINGS_MODULE environment variable appropriately.
3. Run the script to initiate requests to desired API routes and endpoints.
"""

import os
from typing import Dict, List, Union
from aquilify.core.http.client import ClientSession

class RequestSender:
    def __init__(self):
        os.environ.setdefault('AQUILIFY_SETTINGS_MODULE', 'ax-orm.settings')
        self.session = ClientSession()

    def create_payload(self, path: str) -> Dict[str, Union[str, int]]:
        """
        Generates payloads for different CRUD operations based on the provided endpoint path.

        Args:
        - path (str): The API endpoint path.

        Returns:
        - Dict[str, Union[str, int]]: Generated payload for the specified endpoint.
        """
        # Customize payload data based on the endpoint path
        if path == "/update":
            return {
                "up_name": "update_dummy",
                "email": "dummy@gmail.com",
                "password": "Dummy@1234"
            }
        else:
            return {
                "name": "dummy",
                "email": "dummy@gmail.com",
                "password": "Dummy@1234"
            }

    def send_request(self, route: str, path: str) -> None:
        """
        Sends a POST request to the specified API route and endpoint with a generated payload.

        Args:
        - route (str): The API route.
        - path (str): The API endpoint path.

        Returns:
        - None
        """
        try:
            base_url = f"http://localhost:8000{route}"
            url = f"{base_url}{path}"
            
            payload = self.create_payload(path)

            response = self.session.post(url, json_data=payload)
            response_body = response.body()

            print(f"Request to {url} - Status: {response.status_code}, Response: {response_body}")
        except Exception as e:
            print(f"Error occurred while processing {path} on route {route}: {e}")

    def send_requests(self, routes: List[str], paths: List[str]) -> None:
        """
        Sends requests to multiple API routes and endpoints.

        Args:
        - routes (List[str]): List of API routes.
        - paths (List[str]): List of API endpoint paths.

        Returns:
        - None
        """
        for route in routes:
            for path in paths:
                self.send_request(route, path)

if __name__ == "__main__":
    sender = RequestSender()
    routes = ['/api', '/nosql']
    paths = ["/register", "/update", "/read", "/delete"]

    sender.send_requests(routes, paths)
