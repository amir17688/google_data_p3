#!/usr/bin/env python

"""
Util script to handle instance creation over Nova using HTTP APIs for
Nova Agent CI tasks.
"""

__author__ = "Shivaling Sannalli, abhishekkr"

import urllib2
import json
import time
import ConfigParser
import logging
import os


def _http_requests_json(url, headers={}, body=None):
    """ General function for completing HTTP Requests over JSON. """
    print("HTTP Request: %s" % url)
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    request = urllib2.Request(url, body, headers)
    response_body = urllib2.urlopen(request)
    return json.load(response_body)


def get_auth_token(username, api_key, identity_url):
    """ Get HTTP AuthToken for RAX Actions. """
    body = """{
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                        "username": "%s", "apiKey": "%s"
                        }
                    }
            }""" % (username, api_key)

    data = _http_requests_json(identity_url, body=body)
    return data["access"]["token"]["id"]


def wait_server_to_active(url, auth_token, wait=20, timeout=600):
    """ Waits for the created server to activate for "wait_time". """
    time.sleep(wait)

    resp = _http_requests_json(url, {"X-Auth-Token": auth_token})
    status = resp["server"]["status"]
    print("Server status: %s" % status)

    if str(status) == "BUILD" and wait < timeout:
        wait += wait/2
        return wait_server_to_active(url, auth_token, wait, timeout)

    return resp


def create_configfile(IPv4, admin_pass):
    """ Dump information of created server to a file. """
    config = ConfigParser.RawConfigParser()
    config.add_section("credentials")
    config.set("credentials", "IPv4", "%s" % IPv4)
    config.set("credentials", "username", "root")
    config.set("credentials", "adminpass", "%s" % admin_pass)

    filename = "fabfile-%s.cfg" % os.getpid()
    with open(filename, "wb") as configfile:
        config.write(configfile)
    print("Configuration for %s have been dumped to file %s" % (IPv4, filename))
    return filename


def load_configurations():
    image_name = os.getenv("IMAGE_NAME")
    if not image_name:
        image_name = "CentOS60"
    print image_name
    config = ConfigParser.RawConfigParser()
    nova_agent_configuration = os.getenv("NOVA_AGENT_CONFIGURATION")
    if not nova_agent_configuration:
        nova_agent_configuration = os.path.join(os.getcwd(), "server_configurations.cfg")
    config.read(nova_agent_configuration)
    env = os.getenv("ENV_NAME")
    if not env:
        env = config.get("environment", "name")
    return {
        "tenant_id": config.get(env, "tenant_id"),
        "username": config.get(env, "username"),
        "api_key": config.get(env, "api_key"),
        "identity_url": config.get(env, "identity_url"),
        "cloud_url": config.get(env, "cloud_url"),
        "image_id": config.get(env, image_name),
        "flavor_id": config.get(env, "flavor_id"),
        "server_name": "testagent"+image_name
    }


def create_server(initial_wait=120):
    """ Create an instance over Nova using HTTP API. """
    rax_config = load_configurations()
    auth_token = get_auth_token(rax_config["username"], rax_config["api_key"], rax_config["identity_url"])
    print("Auth Token: %s" % auth_token)

    url = "%s" % rax_config["cloud_url"] + "%s/servers" % rax_config["tenant_id"]
    headers = {"X-Auth-Token": auth_token}
    body = """{
                "server": {
                    "imageRef": "%(image_id)s",
                    "flavorRef": "%(flavor_id)s",
                    "name": "%(server_name)s"
                    }
                }""" % rax_config
    resp = _http_requests_json(url, headers, body)

    admin_pass = resp["server"]["adminPass"]
    server_id = resp["server"]["id"]
    server_url = resp["server"]["links"][0]["href"]
    print("Server Details\nID:%s\nURL: %s" % (server_url, server_id))
    print("Initial wait time to get server status: %s sec" % initial_wait)

    time.sleep(initial_wait)
    resp = wait_server_to_active(server_url, auth_token)
    print(resp)
    ipv4 = resp["server"]["accessIPv4"]
    print("IPv4 : %s" % ipv4)
    return create_configfile(ipv4, admin_pass)

